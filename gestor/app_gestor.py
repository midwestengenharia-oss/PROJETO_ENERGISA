from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session, joinedload
from database import SessionLocal, Cliente, UnidadeConsumidora, Fatura, engine
from energisa_client import EnergisaGatewayClient
import base64
import json
import os
import traceback
from datetime import datetime

app = FastAPI(title="Gestor de Faturas SaaS - Enterprise Edition")
gateway = EnergisaGatewayClient()

# Configuração de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

# ==========================================
# 1. ROTAS DE LEITURA
# ==========================================

@app.get("/empresas")
def listar_empresas(db: Session = Depends(get_db)):
    return db.query(Cliente).all()

@app.get("/empresas/{cliente_id}/ucs")
def listar_ucs_cliente(cliente_id: int, db: Session = Depends(get_db)):
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente: raise HTTPException(404, "Cliente não encontrado")
    return cliente.unidades

@app.get("/empresas/{cliente_id}/usinas")
def listar_usinas_arvore(cliente_id: int, db: Session = Depends(get_db)):
    usinas = db.query(UnidadeConsumidora).filter(
        UnidadeConsumidora.cliente_id == cliente_id,
        UnidadeConsumidora.is_geradora == True
    ).options(joinedload(UnidadeConsumidora.beneficiarias)).all()
    return usinas

@app.get("/ucs/{uc_id}/faturas")
def listar_faturas_uc(uc_id: int, db: Session = Depends(get_db)):
    return db.query(Fatura).filter(Fatura.uc_id == uc_id).order_by(Fatura.ano.desc(), Fatura.mes.desc()).all()

@app.get("/faturas/{fatura_id}/detalhes")
def ver_detalhes_fatura(fatura_id: int, db: Session = Depends(get_db)):
    fatura = db.query(Fatura).filter(Fatura.id == fatura_id).first()
    if not fatura: raise HTTPException(404, "Fatura não encontrada")
    return fatura

# ==========================================
# 2. ROTAS DE AÇÃO
# ==========================================

@app.post("/empresas/novo")
def registrar_empresa(nome: str, cpf: str, telefone_final: str, db: Session = Depends(get_db)):
    cpf_clean = cpf.replace(".", "").replace("-", "")
    cliente = Cliente(
        nome_empresa=nome, responsavel_cpf=cpf_clean, telefone_login=telefone_final, ultimo_login=datetime.now()
    )
    db.add(cliente)
    db.commit()
    return {"msg": "Empresa cadastrada com sucesso", "id": cliente.id}

@app.post("/empresas/{id}/conectar")
def iniciar_conexao_energisa(id: int, db: Session = Depends(get_db)):
    cliente = db.query(Cliente).filter(Cliente.id == id).first()
    if not cliente: raise HTTPException(404, "Cliente não encontrado")
    
    try:
        print(f"🔌 Iniciando conexão para {cliente.nome_empresa}...")
        resp = gateway.start_login(cliente.responsavel_cpf, cliente.telefone_login)
        
        cliente.transaction_id = resp.get("transaction_id")
        cliente.status_conexao = "AGUARDANDO_SMS"
        db.commit()
        return {"msg": "SMS Enviado", "transaction_id": cliente.transaction_id}
        
    except Exception as e:
        print(f"⚠️ Aviso no login: {e}. Tentando sincronizar dados existentes...")
        # Dispara sync em background para recuperar sessão se possível
        sincronizar_dados_cliente(cliente.id)
        return {"msg": "Processo de sincronização iniciado.", "details": str(e)}

@app.post("/empresas/{id}/validar-sms")
def validar_sms(id: int, codigo_sms: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    cliente = db.query(Cliente).filter(Cliente.id == id).first()
    try:
        gateway.finish_login(cliente.responsavel_cpf, cliente.transaction_id, codigo_sms)
        cliente.status_conexao = "CONECTADO"
        cliente.ultimo_login = datetime.now()
        db.commit()
        
        background_tasks.add_task(sincronizar_dados_cliente, cliente.id)
        return {"msg": "Conectado com sucesso!"}
    except Exception as e:
        raise HTTPException(400, f"Falha ao validar SMS: {str(e)}")

@app.get("/faturas/{id}/download")
def baixar_pdf_fatura(id: int, db: Session = Depends(get_db)):
    fatura = db.query(Fatura).filter(Fatura.id == id).first()
    if not fatura: raise HTTPException(404, "Fatura não encontrada")
    
    pasta_storage = "faturas_storage"
    os.makedirs(pasta_storage, exist_ok=True)
    filename_local = f"{pasta_storage}/fatura_{fatura.uc.cdc}_{fatura.mes}-{fatura.ano}.pdf"
    
    if not os.path.exists(filename_local):
        print(f"📥 Baixando PDF da Energisa para Fatura {id}...")
        try:
            cli = fatura.uc.cliente
            res = gateway.download_fatura(
                cli.responsavel_cpf,
                {
                    "cdc": fatura.uc.cdc, 
                    "empresa_web": fatura.uc.empresa_web, 
                    "digito_verificador": fatura.uc.digito_verificador
                },
                {
                    "mes": fatura.mes, 
                    "ano": fatura.ano, 
                    "numero_fatura": fatura.numero_fatura
                }
            )
            if res and "file_base64" in res:
                with open(filename_local, "wb") as f:
                    f.write(base64.b64decode(res["file_base64"]))
                fatura.arquivo_pdf_path = filename_local
                db.commit()
                print(f"✅ PDF salvo: {filename_local}")
            else:
                raise Exception("Gateway não retornou o arquivo.")
        except Exception as e:
            print(f"❌ Erro download: {e}")
            raise HTTPException(500, f"Erro ao baixar PDF: {str(e)}")

    try:
        with open(filename_local, "rb") as f:
            content = f.read()
            b64_string = base64.b64encode(content).decode('utf-8')
        return {
            "filename": f"Fatura_{fatura.uc.cdc}_{fatura.mes}-{fatura.ano}.pdf",
            "content_type": "application/pdf",
            "file_base64": b64_string
        }
    except Exception as e:
        raise HTTPException(500, f"Erro ao ler arquivo: {e}")

# ==========================================
# 3. CORE: ROBÔ DE SINCRONIZAÇÃO
# ==========================================

def sincronizar_dados_cliente(cliente_id: int):
    db = SessionLocal()
    try:
        cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
        if not cliente: return

        print(f"🔄 ROBÔ: Sincronizando {cliente.nome_empresa} (CPF {cliente.responsavel_cpf})...")
        
        ucs_remotas = gateway.list_ucs(cliente.responsavel_cpf)
        
        if isinstance(ucs_remotas, dict) and "detail" in ucs_remotas:
             print(f"❌ Erro ao buscar UCs: {ucs_remotas['detail']}")
             return

        print(f"   📋 Encontradas {len(ucs_remotas)} UCs.")
        
        for uc_data in ucs_remotas:
            # 1. TRATAMENTO DE DADOS BÁSICOS
            raw_end = uc_data.get('endereco')
            endereco_final = raw_end.get('descricao', "") if isinstance(raw_end, dict) else str(raw_end) if raw_end else "Endereço não informado"
            
            cdc_real = uc_data.get('cdc') or uc_data.get('numeroUc')
            digito_real = uc_data.get('digitoVerificador')
            if digito_real is None: digito_real = uc_data.get('digitoVerificadorCdc')
            if digito_real is None: digito_real = 0 

            # 2. Variáveis Solares (INICIALIZAÇÃO SEGURA)
            gd_code = uc_data.get('geracaoDistribuida')
            eh_geradora = False
            saldo_kwh = 0.0
            tipo_geracao = None
            lista_beneficiarias = [] # <--- ISSO AQUI GARANTE QUE A VARIÁVEL SEMPRE EXISTA

            # 3. Busca Dados Solares
            if gd_code and str(gd_code) == str(uc_data.get('numeroUc')):
                eh_geradora = True
                print(f"   ☀️ UC {cdc_real} é USINA! Buscando detalhes...")
                
                try:
                    gd_info = gateway.get_gd_info(cliente.responsavel_cpf, {
                        "cdc": cdc_real,
                        "empresa_web": uc_data.get('codigoEmpresaWeb', 6),
                        "digitoVerificadorCdc": digito_real
                    })
                    
                    if gd_info and 'infos' in gd_info:
                        obj_gd = gd_info['infos'].get('objeto', {}) or {} # Proteção contra None
                        saldo_kwh = obj_gd.get('qtdKwhSaldo', 0)
                        tipo_geracao = obj_gd.get('tipoGeracao', 'Solar')
                        
                        # PEGA A LISTA COM SEGURANÇA
                        lista_beneficiarias = obj_gd.get('listaBeneficiarias') or []
                        print(f"      ↳ {len(lista_beneficiarias)} beneficiárias encontradas.")
                        
                except Exception as e:
                    print(f"      ⚠️ Erro dados GD (mas vamos continuar): {e}")

            # 4. Salvar UC Principal (USINA ou NORMAL)
            uc_local = db.query(UnidadeConsumidora).filter_by(codigo_uc=uc_data['numeroUc']).first()
            
            if not uc_local:
                uc_local = UnidadeConsumidora(
                    cliente_id=cliente.id,
                    codigo_uc=uc_data.get('numeroUc'),
                    cdc=cdc_real,
                    digito_verificador=digito_real,
                    empresa_web=uc_data.get('codigoEmpresaWeb', 6),
                    endereco=endereco_final,
                    nome_titular=uc_data.get('nomeTitular'),
                    is_geradora=eh_geradora,
                    saldo_acumulado=saldo_kwh,
                    tipo_geracao=tipo_geracao
                )
                db.add(uc_local)
            else:
                uc_local.is_geradora = eh_geradora
                uc_local.saldo_acumulado = saldo_kwh
                uc_local.tipo_geracao = tipo_geracao
            
            db.commit()
            db.refresh(uc_local)
            print(f"   ✅ UC {uc_local.codigo_uc} salva.")

            # 5. Salvar Beneficiárias (AGORA VAI FUNCIONAR)
            if lista_beneficiarias: # Se a lista não estiver vazia
                for ben in lista_beneficiarias:
                    ben_cdc = ben.get('cdc')
                    uc_filha = db.query(UnidadeConsumidora).filter_by(cdc=ben_cdc).first()
                    
                    if not uc_filha:
                        uc_filha = UnidadeConsumidora(
                            cliente_id=cliente.id,
                            codigo_uc=ben_cdc,
                            cdc=ben_cdc,
                            digito_verificador=ben.get('digitoVerificador', 0),
                            empresa_web=ben.get('codigoEmpresaWeb', 6),
                            endereco=ben.get('endereco', 'Endereço Beneficiária'),
                            nome_titular=ben.get('nome'),
                            is_geradora=False
                        )
                        db.add(uc_filha)
                    
                    # VINCULA AO PAI
                    uc_filha.geradora_id = uc_local.id
                    uc_filha.percentual_rateio = ben.get('percentualRecebido', 0)
                
                db.commit()
                print(f"      👨‍👧 {len(lista_beneficiarias)} beneficiárias vinculadas à usina.")

            # --- 6. Baixar Faturas ---
            print(f"   🔎 Buscando faturas da UC {uc_local.cdc}...")
            try:
                faturas_remotas = gateway.list_faturas(cliente.responsavel_cpf, {
                    "cdc": uc_local.cdc,
                    "empresa_web": uc_local.empresa_web,
                    "digito_verificador": uc_local.digito_verificador
                })
                
                if isinstance(faturas_remotas, list):
                    count_novas = 0
                    for fat in faturas_remotas:
                        if not db.query(Fatura).filter_by(uc_id=uc_local.id, numero_fatura=fat.get('numeroFatura')).first():
                            
                            dt_venc = None
                            if fat.get('dataVencimentoISO'):
                                try: dt_venc = datetime.fromisoformat(fat.get('dataVencimentoISO')).date()
                                except: pass
                            
                            dt_leit = None
                            if fat.get('dataLeituraISO'):
                                try: dt_leit = datetime.fromisoformat(fat.get('dataLeituraISO')).date()
                                except: pass

                            nova_fatura = Fatura(
                                uc_id=uc_local.id,
                                mes=fat.get('mesReferencia'),
                                ano=fat.get('anoReferencia'),
                                valor=fat.get('valorFatura'),
                                status=fat.get('situacaoPagamento'),
                                numero_fatura=fat.get('numeroFatura'),
                                vencimento=dt_venc,
                                data_leitura=dt_leit,
                                consumo_kwh=fat.get('consumo'),
                                codigo_barras=fat.get('codigoBarraFaturaLis') or fat.get('codigoBarra'),
                                pix_copia_cola=fat.get('qrCodePix'),
                                detalhes_json=json.dumps(fat.get('detalhamentoFatura', {}))
                            )
                            db.add(nova_fatura)
                            count_novas += 1
                    db.commit()
                    print(f"      💰 {count_novas} novas faturas.")
                else:
                    print("      ⚠️ Resposta de faturas inválida (provável erro 500 no Gateway).")

            except Exception as e:
                print(f"      ⚠️ Erro faturas: {e}")
            
    except Exception as e:
        print(f"❌ Erro Crítico Sync: {e}")
        traceback.print_exc()
    finally:
        db.close()