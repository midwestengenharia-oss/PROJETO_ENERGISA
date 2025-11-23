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

# Configuração de CORS (Permitir acesso do Frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency Injection para Sessão do Banco
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==========================================
# 1. ROTAS DE LEITURA (FRONTEND OPTIMIZED)
# ==========================================

@app.get("/empresas")
def listar_empresas(db: Session = Depends(get_db)):
    """Lista todas as empresas cadastradas para o Dashboard Geral."""
    return db.query(Cliente).all()

@app.get("/empresas/{cliente_id}/ucs")
def listar_ucs_cliente(cliente_id: int, db: Session = Depends(get_db)):
    """
    Retorna a lista de UCs de um cliente. 
    Usado na tela de detalhes para mostrar os cards iniciais.
    """
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente: raise HTTPException(404, "Cliente não encontrado")
    return cliente.unidades

@app.get("/empresas/{cliente_id}/usinas")
def listar_usinas_arvore(cliente_id: int, db: Session = Depends(get_db)):
    """
    Endpoint Especial: Retorna apenas as UCs GERADORAS.
    Carrega junto as BENEFICIÁRIAS (filhas) para montar a árvore de rateio.
    """
    usinas = db.query(UnidadeConsumidora).filter(
        UnidadeConsumidora.cliente_id == cliente_id,
        UnidadeConsumidora.is_geradora == True
    ).options(joinedload(UnidadeConsumidora.beneficiarias)).all()
    return usinas

@app.get("/ucs/{uc_id}/faturas")
def listar_faturas_uc(uc_id: int, db: Session = Depends(get_db)):
    """
    Lazy Loading: Retorna as faturas de uma UC específica.
    Isso evita carregar milhares de registros de uma vez na tela inicial.
    """
    return db.query(Fatura).filter(Fatura.uc_id == uc_id).order_by(Fatura.ano.desc(), Fatura.mes.desc()).all()

@app.get("/faturas/{fatura_id}/detalhes")
def ver_detalhes_fatura(fatura_id: int, db: Session = Depends(get_db)):
    """Retorna os detalhes ricos (PIX, Barras, JSON) para o Modal."""
    fatura = db.query(Fatura).filter(Fatura.id == fatura_id).first()
    if not fatura: raise HTTPException(404, "Fatura não encontrada")
    return fatura

# ==========================================
# 2. ROTAS DE AÇÃO (LOGIN E DOWNLOAD)
# ==========================================

@app.post("/empresas/novo")
def registrar_empresa(nome: str, cpf: str, telefone_final: str, db: Session = Depends(get_db)):
    """Cadastra uma nova empresa/cliente no sistema."""
    # Remove pontuação do CPF para evitar duplicidade errada
    cpf_clean = cpf.replace(".", "").replace("-", "")
    
    cliente = Cliente(
        nome_empresa=nome, 
        responsavel_cpf=cpf_clean, 
        telefone_login=telefone_final, 
        ultimo_login=datetime.now()
    )
    db.add(cliente)
    db.commit()
    return {"msg": "Empresa cadastrada com sucesso", "id": cliente.id}

@app.post("/empresas/{id}/conectar")
def iniciar_conexao_energisa(id: int, db: Session = Depends(get_db)):
    """
    Inicia o fluxo de conexão.
    Se o Gateway disser que precisa de SMS, retorna status.
    Se já estiver logado (cookie válido), dispara sincronização direta.
    """
    cliente = db.query(Cliente).filter(Cliente.id == id).first()
    if not cliente: raise HTTPException(404, "Cliente não encontrado")
    
    try:
        # Chama o Gateway na porta 3000
        print(f"🔌 Iniciando conexão para {cliente.nome_empresa}...")
        resp = gateway.start_login(cliente.responsavel_cpf, cliente.telefone_login)
        
        # Se retornou transaction_id, é porque pediu SMS
        cliente.transaction_id = resp.get("transaction_id")
        cliente.status_conexao = "AGUARDANDO_SMS"
        db.commit()
        return {"msg": "SMS Enviado. Aguardando código.", "transaction_id": cliente.transaction_id}
        
    except Exception as e:
        # Erro comum: "Login falhou" ou timeout. 
        # Mas as vezes o erro é "Já logado" ou o Gateway recuperou a sessão.
        # Vamos tentar sincronizar de qualquer forma como fallback.
        print(f"⚠️ Aviso no login: {e}. Tentando sincronizar dados existentes...")
        
        # Dispara sync em background para não travar o request
        sincronizar_dados_cliente(cliente.id)
        
        return {"msg": "Processo de sincronização iniciado (Sessão recuperada ou erro tratado).", "details": str(e)}

@app.post("/empresas/{id}/validar-sms")
def validar_sms(id: int, codigo_sms: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Recebe o código SMS, envia para o Gateway e, se sucesso, dispara o robô de dados.
    """
    cliente = db.query(Cliente).filter(Cliente.id == id).first()
    
    try:
        gateway.finish_login(cliente.responsavel_cpf, cliente.transaction_id, codigo_sms)
        
        cliente.status_conexao = "CONECTADO"
        cliente.ultimo_login = datetime.now()
        db.commit()
        
        # Dispara o Robô em Background (Thread separada)
        background_tasks.add_task(sincronizar_dados_cliente, cliente.id)
        
        return {"msg": "Conectado com sucesso! O robô está baixando os dados."}
    except Exception as e:
        raise HTTPException(400, f"Falha ao validar SMS: {str(e)}")

@app.get("/faturas/{id}/download")
def baixar_pdf_fatura(id: int, db: Session = Depends(get_db)):
    """
    Gerencia o download do PDF:
    1. Verifica se já temos o arquivo em disco (Cache).
    2. Se não, pede para o Gateway baixar da Energisa.
    3. Salva em disco e retorna o Base64 para o navegador.
    """
    fatura = db.query(Fatura).filter(Fatura.id == id).first()
    if not fatura: raise HTTPException(404, "Fatura não encontrada")
    
    # Estratégia de Cache em Disco
    pasta_storage = "faturas_storage"
    os.makedirs(pasta_storage, exist_ok=True)
    filename_local = f"{pasta_storage}/fatura_{fatura.uc.cdc}_{fatura.mes}-{fatura.ano}.pdf"
    
    # Se não existe, vai buscar
    if not os.path.exists(filename_local):
        print(f"📥 PDF não encontrado em cache. Baixando do Gateway para Fatura {id}...")
        try:
            cliente = fatura.uc.cliente
            
            resultado = gateway.download_fatura(
                cliente.responsavel_cpf,
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
            
            if resultado and "file_base64" in resultado:
                with open(filename_local, "wb") as f:
                    f.write(base64.b64decode(resultado["file_base64"]))
                
                fatura.arquivo_pdf_path = filename_local
                db.commit()
                print(f"✅ PDF salvo com sucesso: {filename_local}")
            else:
                raise Exception("Gateway não retornou o arquivo (Base64 vazio).")
                
        except Exception as e:
            print(f"❌ Erro crítico no download: {e}")
            raise HTTPException(500, f"Erro ao baixar PDF: {str(e)}")

    # Retorna o arquivo
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
        raise HTTPException(500, f"Erro ao ler arquivo do disco: {e}")

# ==========================================
# 3. CORE: ROBÔ DE SINCRONIZAÇÃO (COMPLETO)
# ==========================================

def sincronizar_dados_cliente(cliente_id: int):
    """
    O Coração do Sistema.
    1. Lista UCs.
    2. Identifica Usinas Solares e busca detalhes (Rateio).
    3. Salva/Atualiza UCs e Beneficiárias.
    4. Baixa Faturas de todas as UCs principais.
    """
    db = SessionLocal()
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    
    if not cliente:
        print("❌ Erro Sync: Cliente não encontrado no banco.")
        return

    print(f"🔄 ROBÔ: Iniciando sincronização para {cliente.nome_empresa} (CPF {cliente.responsavel_cpf})...")
    
    try:
        # 1. Busca Lista de UCs no Gateway
        ucs_remotas = gateway.list_ucs(cliente.responsavel_cpf)
        
        # Validação de erro na resposta
        if isinstance(ucs_remotas, dict) and "detail" in ucs_remotas:
             print(f"❌ Erro ao buscar UCs no Gateway: {ucs_remotas['detail']}")
             return

        print(f"   📋 Encontradas {len(ucs_remotas)} UCs no portal.")
        
        for uc_data in ucs_remotas:
            # --- Tratamento de Endereço (Pode ser String ou Dict) ---
            raw_endereco = uc_data.get('endereco')
            endereco_final = "Endereço não informado"
            if isinstance(raw_endereco, dict):
                endereco_final = raw_endereco.get('descricao', endereco_final)
            elif isinstance(raw_endereco, str):
                endereco_final = raw_endereco
            
            # --- Tratamento de Identificadores (CDC vs NumeroUc) ---
            cdc_real = uc_data.get('cdc') or uc_data.get('numeroUc')
            
            # Tratamento de Dígito (Pode ser 0, que é False em Python)
            digito_real = uc_data.get('digitoVerificador')
            if digito_real is None: digito_real = uc_data.get('digitoVerificadorCdc')
            if digito_real is None: digito_real = 0 # Fallback seguro

            # --- LÓGICA SOLAR: É UMA USINA? ---
            gd_code = uc_data.get('geracaoDistribuida')
            eh_geradora = False
            saldo_kwh = 0.0
            tipo_geracao = None
            
            # Se o código GD for igual ao número da UC, ela é a geradora (Usina)
            if gd_code and str(gd_code) == str(uc_data.get('numeroUc')):
                eh_geradora = True
                print(f"   ☀️ UC {cdc_real} identificada como USINA! Buscando dados de geração...")
                
                try:
                    # Chama endpoint específico de GD
                    gd_info = gateway.get_gd_info(cliente.responsavel_cpf, {
                        "cdc": cdc_real,
                        "empresa_web": uc_data.get('codigoEmpresaWeb', 6),
                        "digitoVerificadorCdc": digito_real
                    })
                    
                    if gd_info and 'infos' in gd_info:
                        obj_gd = gd_info['infos'].get('objeto', {})
                        saldo_kwh = obj_gd.get('qtdKwhSaldo', 0)
                        tipo_geracao = obj_gd.get('tipoGeracao', 'Solar')
                        
                        # --- SUB-PROCESSO: SALVAR BENEFICIÁRIAS (FILHAS) ---
                        lista_beneficiarias = obj_gd.get('listaBeneficiarias', [])
                        print(f"      ↳ Encontradas {len(lista_beneficiarias)} beneficiárias para esta usina.")
                        
                        # Como vamos salvar as filhas, precisamos garantir que o Pai já tem ID.
                        # Isso é tratado no bloco abaixo (salvamento do Pai).
                        
                except Exception as e:
                    print(f"      ⚠️ Erro ao buscar dados GD: {e}")

            # --- SALVAR/ATUALIZAR UC PRINCIPAL NO BANCO ---
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
                    # Campos Solares
                    is_geradora=eh_geradora,
                    saldo_acumulado=saldo_kwh,
                    tipo_geracao=tipo_geracao
                )
                db.add(uc_local)
            else:
                # Atualiza dados existentes
                uc_local.is_geradora = eh_geradora
                uc_local.saldo_acumulado = saldo_kwh
                uc_local.tipo_geracao = tipo_geracao
            
            db.commit()
            db.refresh(uc_local) # Pega o ID gerado
            print(f"   ✅ UC {uc_local.codigo_uc} sincronizada no banco.")

            # --- AGORA SIM: PROCESSAR BENEFICIÁRIAS (SE FOR USINA) ---
            if eh_geradora and 'lista_beneficiarias' in locals():
                for ben in lista_beneficiarias:
                    ben_cdc = ben.get('cdc')
                    # Verifica se a beneficiária já existe (pode ter vindo na lista geral ou não)
                    uc_filha = db.query(UnidadeConsumidora).filter_by(cdc=ben_cdc).first()
                    
                    if not uc_filha:
                        # Cria a beneficiária se ela não existir
                        uc_filha = UnidadeConsumidora(
                            cliente_id=cliente.id,
                            codigo_uc=ben_cdc, # Usa CDC como código se não tiver outro
                            cdc=ben_cdc,
                            digito_verificador=ben.get('digitoVerificador', 0),
                            empresa_web=ben.get('codigoEmpresaWeb', 6),
                            endereco=ben.get('endereco', 'Endereço Beneficiária'),
                            nome_titular=ben.get('nome'),
                            is_geradora=False
                        )
                        db.add(uc_filha)
                    
                    # VINCULA AO PAI (Cria a relação de árvore)
                    uc_filha.geradora_id = uc_local.id
                    uc_filha.percentual_rateio = ben.get('percentualRecebido', 0)
                
                db.commit()

            # --- BUSCA DE FATURAS DA UC ---
            print(f"   🔎 Buscando faturas da UC {uc_local.cdc}...")
            
            try:
                faturas_remotas = gateway.list_faturas(cliente.responsavel_cpf, {
                    "cdc": uc_local.cdc,
                    "empresa_web": uc_local.empresa_web,
                    "digito_verificador": uc_local.digito_verificador
                })
                
                # Tratamento de erros da API de Faturas
                if isinstance(faturas_remotas, dict) and "detail" in faturas_remotas:
                    print(f"      ⚠️ Pular Faturas UC {uc_local.cdc}: {faturas_remotas['detail']}")
                    continue
                
                if not isinstance(faturas_remotas, list):
                    print(f"      ⚠️ Pular Faturas UC {uc_local.cdc}: Resposta inválida.")
                    continue
                
                count_novas = 0
                for fat in faturas_remotas:
                    # Verifica duplicidade
                    fat_existe = db.query(Fatura).filter_by(
                        uc_id=uc_local.id, 
                        numero_fatura=fat.get('numeroFatura')
                    ).first()
                    
                    if not fat_existe:
                        # Parse Seguro de Datas
                        data_venc = None
                        if fat.get('dataVencimentoISO'):
                            try: data_venc = datetime.fromisoformat(fat.get('dataVencimentoISO')).date()
                            except: pass
                        
                        data_leit = None
                        if fat.get('dataLeituraISO'):
                            try: data_leit = datetime.fromisoformat(fat.get('dataLeituraISO')).date()
                            except: pass

                        # Cria objeto Fatura com TODOS os dados ricos
                        nova_fatura = Fatura(
                            uc_id=uc_local.id,
                            mes=fat.get('mesReferencia'),
                            ano=fat.get('anoReferencia'),
                            valor=fat.get('valorFatura'),
                            status=fat.get('situacaoPagamento'),
                            numero_fatura=fat.get('numeroFatura'),
                            vencimento=data_venc,
                            
                            # Campos Extras
                            data_leitura=data_leit,
                            consumo_kwh=fat.get('consumo'),
                            # Prioriza LIS, depois normal
                            codigo_barras=fat.get('codigoBarraFaturaLis') or fat.get('codigoBarra'),
                            pix_copia_cola=fat.get('qrCodePix'),
                            # Salva o JSON completo para futuro
                            detalhes_json=json.dumps(fat.get('detalhamentoFatura', {}))
                        )
                        db.add(nova_fatura)
                        count_novas += 1
                        
                db.commit()
                print(f"      💰 {count_novas} novas faturas salvas.")
                
            except Exception as e:
                print(f"      ⚠️ Erro ao processar faturas desta UC: {e}")
            
    except Exception as e:
        print(f"❌ Erro Crítico no Robô: {e}")
        traceback.print_exc()
    finally:
        db.close()
        print("🏁 Sincronização finalizada.")