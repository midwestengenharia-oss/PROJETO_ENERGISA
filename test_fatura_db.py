"""
Teste do Parser de IA com Fatura do Banco de Dados
"""

import os
import sys
import json
import asyncio

# Adicionar backend ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Carregar .env
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), 'backend', '.env'))

from supabase import create_client
from faturas.ai_parser import FaturaAIParser

# Configurar Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")


async def test_fatura_from_db(fatura_id: int):
    """Testa parser de IA com uma fatura especifica do banco"""

    print("=" * 70)
    print(f"TESTE: Parser de IA com Fatura #{fatura_id}")
    print("=" * 70)

    # Conectar ao Supabase
    print("\n[INFO] Conectando ao Supabase...")
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Buscar fatura
    print(f"[INFO] Buscando fatura {fatura_id}...")
    result = supabase.table("faturas").select("*").eq("id", fatura_id).execute()

    if not result.data:
        print(f"[ERRO] Fatura {fatura_id} nao encontrada!")
        return

    fatura = result.data[0]
    print(f"\n[OK] Fatura encontrada. Campos disponiveis:")
    for key, value in fatura.items():
        if value is not None:
            val_str = str(value)[:100] + "..." if len(str(value)) > 100 else str(value)
            print(f"     - {key}: {val_str}")

    # Verificar se tem texto extraido
    texto_extraido = fatura.get("texto_extraido")

    if not texto_extraido:
        print("\n[AVISO] Fatura sem texto_extraido no banco.")

        # Verificar arquivo
        arquivo_path = fatura.get("arquivo_path") or fatura.get("arquivo_url")
        if arquivo_path:
            print(f"[INFO] Arquivo encontrado: {arquivo_path}")

            # Tentar baixar
            try:
                print(f"[INFO] Baixando arquivo do storage...")
                file_data = supabase.storage.from_("faturas").download(arquivo_path)

                temp_path = f"temp_fatura_{fatura_id}.pdf"
                with open(temp_path, "wb") as f:
                    f.write(file_data)

                print(f"[OK] PDF baixado: {temp_path}")

                # Extrair texto
                import pdfplumber
                texto_extraido = ""
                with pdfplumber.open(temp_path) as pdf:
                    for page in pdf.pages:
                        texto_extraido += page.extract_text() or ""

                os.remove(temp_path)
                print(f"[OK] Texto extraido: {len(texto_extraido)} caracteres")

            except Exception as e:
                print(f"[ERRO] Falha ao baixar/extrair PDF: {e}")

        # Tentar PDF em base64
        if not texto_extraido:
            pdf_base64 = fatura.get("pdf_base64")
            if pdf_base64:
                print(f"[INFO] PDF em base64 encontrado ({len(pdf_base64)} chars)")
                try:
                    import base64
                    import pdfplumber
                    import io

                    # Decodificar base64
                    pdf_bytes = base64.b64decode(pdf_base64)
                    print(f"[OK] PDF decodificado: {len(pdf_bytes)} bytes")

                    # Extrair texto
                    texto_extraido = ""
                    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                        for page in pdf.pages:
                            texto_extraido += page.extract_text() or ""

                    print(f"[OK] Texto extraido do PDF: {len(texto_extraido)} caracteres")

                except Exception as e:
                    print(f"[ERRO] Falha ao decodificar/extrair PDF base64: {e}")

        if not texto_extraido:
            # Verificar dados_extraidos existentes
            dados = fatura.get("dados_extraidos")
            if dados:
                print("\n[INFO] Fatura ja tem dados_extraidos. Exibindo:")
                if isinstance(dados, str):
                    dados = json.loads(dados)
                print(json.dumps(dados, indent=2, ensure_ascii=False, default=str))
            else:
                print("\n[ERRO] Sem texto e sem dados extraidos!")
            return
    else:
        print(f"\n[OK] Texto extraido encontrado: {len(texto_extraido)} caracteres")

    # Mostrar preview do texto
    print("\n" + "-" * 70)
    print("PREVIEW DO TEXTO (primeiros 2000 chars):")
    print("-" * 70)
    print(texto_extraido[:2000])
    print("..." if len(texto_extraido) > 2000 else "")
    print("-" * 70)

    # Testar parser de IA
    print("\n[INFO] Iniciando parser de IA (OpenAI GPT-4o)...")
    parser = FaturaAIParser(provider="openai")

    try:
        resultado = parser.parse(texto_extraido)

        print("\n" + "=" * 70)
        print("RESULTADO DO PARSER DE IA:")
        print("=" * 70)
        print(json.dumps(resultado, indent=2, ensure_ascii=False, default=str))

        # Exibir TODOS os dados extraidos
        print("\n" + "=" * 70)
        print("TODOS OS DADOS EXTRAIDOS PELA IA:")
        print("=" * 70)

        def print_section(title, data, indent=0):
            prefix = "  " * indent
            print(f"\n{prefix}{'='*40}")
            print(f"{prefix}{title}")
            print(f"{prefix}{'='*40}")
            if isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, dict):
                        print(f"{prefix}{key}:")
                        for k, v in value.items():
                            print(f"{prefix}  {k}: {v}")
                    elif isinstance(value, list):
                        print(f"{prefix}{key}: [{len(value)} itens]")
                        for i, item in enumerate(value):
                            if isinstance(item, dict):
                                print(f"{prefix}  [{i+1}]")
                                for k, v in item.items():
                                    print(f"{prefix}    {k}: {v}")
                            else:
                                print(f"{prefix}  - {item}")
                    else:
                        print(f"{prefix}{key}: {value}")

        # 1. Identificacao
        print("\n" + "=" * 70)
        print("1. IDENTIFICACAO DO CLIENTE/UC")
        print("=" * 70)
        print(f"  Codigo Cliente: {resultado.get('codigo_cliente')}")
        print(f"  Ligacao: {resultado.get('ligacao')}")
        print(f"  Bandeira Tarifaria: {resultado.get('bandeira_tarifaria')}")

        # 2. Datas
        print("\n" + "=" * 70)
        print("2. DATAS")
        print("=" * 70)
        print(f"  Data Apresentacao: {resultado.get('data_apresentacao')}")
        print(f"  Mes/Ano Referencia: {resultado.get('mes_ano_referencia')}")
        print(f"  Vencimento: {resultado.get('vencimento')}")
        print(f"  Leitura Anterior Data: {resultado.get('leitura_anterior_data')}")
        print(f"  Leitura Atual Data: {resultado.get('leitura_atual_data')}")
        print(f"  Dias: {resultado.get('dias')}")

        # 3. Leituras
        print("\n" + "=" * 70)
        print("3. LEITURAS DO MEDIDOR")
        print("=" * 70)
        print(f"  Leitura Anterior: {resultado.get('leitura_anterior')}")
        print(f"  Leitura Atual: {resultado.get('leitura_atual')}")
        print(f"  Consumo Total kWh: {resultado.get('consumo_total_kwh')}")
        print(f"  Energia Injetada Total kWh: {resultado.get('energia_injetada_total_kwh')}")

        # 4. Valores
        print("\n" + "=" * 70)
        print("4. VALORES")
        print("=" * 70)
        print(f"  Total a Pagar: R$ {resultado.get('total_a_pagar')}")

        # 5. Itens da Fatura
        print("\n" + "=" * 70)
        print("5. ITENS DA FATURA")
        print("=" * 70)

        itens = resultado.get("itens_fatura", {})

        # Consumo
        consumo = itens.get("consumo_kwh", {})
        if consumo:
            print("\n  [CONSUMO EM KWH]")
            print(f"    Quantidade: {consumo.get('quantidade')} kWh")
            print(f"    Preco Unit c/ Tributos: R$ {consumo.get('preco_unit_com_tributos')}")
            print(f"    Valor: R$ {consumo.get('valor')}")

        # Energia Injetada oUC
        injetada_ouc = itens.get("energia_injetada_ouc", [])
        if injetada_ouc:
            print(f"\n  [ENERGIA INJETADA oUC] ({len(injetada_ouc)} itens)")
            for i, item in enumerate(injetada_ouc):
                print(f"    [{i+1}] {item.get('descricao')}")
                print(f"        Tipo GD: {item.get('tipo_gd')}")
                print(f"        Quantidade: {item.get('quantidade')} kWh")
                print(f"        Preco Unit: R$ {item.get('preco_unit_com_tributos')}")
                print(f"        Valor: R$ {item.get('valor')}")
                print(f"        Mes/Ano Ref: {item.get('mes_ano_referencia_item')}")

        # Energia Injetada mUC
        injetada_muc = itens.get("energia_injetada_muc", [])
        if injetada_muc:
            print(f"\n  [ENERGIA INJETADA mUC] ({len(injetada_muc)} itens)")
            for i, item in enumerate(injetada_muc):
                print(f"    [{i+1}] {item.get('descricao')}")
                print(f"        Tipo GD: {item.get('tipo_gd')}")
                print(f"        Quantidade: {item.get('quantidade')} kWh")
                print(f"        Valor: R$ {item.get('valor')}")

        # Ajuste Lei 14.300
        ajuste = itens.get("ajuste_lei_14300", {})
        if ajuste and any(ajuste.values()):
            print("\n  [AJUSTE LEI 14.300 (GDII)]")
            print(f"    Quantidade: {ajuste.get('quantidade')} kWh")
            print(f"    Preco Unit: R$ {ajuste.get('preco_unit_com_tributos')}")
            print(f"    Valor: R$ {ajuste.get('valor')}")

        # Lancamentos e Servicos
        lancamentos = itens.get("lancamentos_e_servicos", [])
        if lancamentos:
            print(f"\n  [LANCAMENTOS E SERVICOS] ({len(lancamentos)} itens)")
            for i, item in enumerate(lancamentos):
                print(f"    [{i+1}] {item.get('descricao')}: R$ {item.get('valor')}")

        # 6. Totais
        print("\n" + "=" * 70)
        print("6. TOTAIS")
        print("=" * 70)
        totais = resultado.get("totais", {})
        print(f"  Adicionais Bandeira: R$ {totais.get('adicionais_bandeira')}")
        print(f"  Lancamentos/Servicos: R$ {totais.get('lancamentos_e_servicos')}")
        print(f"  Total Geral Fatura: R$ {totais.get('total_geral_fatura')}")

        # 7. Quadro Atencao (GD)
        print("\n" + "=" * 70)
        print("7. QUADRO ATENCAO (CREDITOS GD)")
        print("=" * 70)
        quadro = resultado.get("quadro_atencao", {})
        print(f"  Saldo Acumulado: {quadro.get('saldo_acumulado')} kWh")
        print(f"  A Expirar Proximo Ciclo: {quadro.get('a_expirar_proximo_ciclo')} kWh")
        print(f"  Creditos Expirados: {quadro.get('creditos_expirados')} kWh")

        # 8. Dados da Instalacao
        print("\n" + "=" * 70)
        print("8. DADOS DA INSTALACAO")
        print("=" * 70)
        instalacao = resultado.get("dados_instalacao", {})
        print(f"  Numero Medidor: {instalacao.get('numero_medidor')}")
        print(f"  Numero Instalacao: {instalacao.get('numero_instalacao')}")
        print(f"  Classe Consumo: {instalacao.get('classe_consumo')}")
        print(f"  Modalidade Tarifaria: {instalacao.get('modalidade_tarifaria')}")
        print(f"  Tensao Nominal: {instalacao.get('tensao_nominal')}")
        print(f"  Endereco: {instalacao.get('endereco')}")

        # 9. Comparacao com banco
        print("\n" + "=" * 70)
        print("9. COMPARACAO COM DADOS DO BANCO (API ENERGISA)")
        print("=" * 70)
        print(f"  {'Campo':<25} {'IA (PDF)':<20} {'API':<20} {'Status'}")
        print("  " + "-" * 70)

        comparacoes = [
            ("vencimento", resultado.get("vencimento"), fatura.get("data_vencimento")),
            ("total_a_pagar", resultado.get("total_a_pagar"), fatura.get("valor_fatura")),
            ("consumo_kwh", resultado.get("consumo_total_kwh"), fatura.get("consumo")),
            ("leitura_anterior", resultado.get("leitura_anterior"), fatura.get("leitura_anterior")),
            ("leitura_atual", resultado.get("leitura_atual"), fatura.get("leitura_atual")),
            ("dias", resultado.get("dias"), fatura.get("quantidade_dias")),
            ("iluminacao_publica", totais.get("lancamentos_e_servicos"), fatura.get("valor_iluminacao_publica")),
            ("icms", None, fatura.get("valor_icms")),
            ("bandeira", resultado.get("bandeira_tarifaria"), fatura.get("bandeira_tarifaria")),
        ]

        for campo, valor_ia, valor_api in comparacoes:
            ia_str = str(valor_ia) if valor_ia is not None else "-"
            api_str = str(valor_api) if valor_api is not None else "-"
            if valor_ia is not None and valor_api is not None:
                status = "✓" if str(valor_ia) == str(valor_api) else "≠"
            elif valor_ia is not None:
                status = "NEW"
            else:
                status = "API"
            print(f"  {campo:<25} {ia_str:<20} {api_str:<20} {status}")

        print("\n" + "=" * 70)
        print("[SUCESSO] Extracao completa!")
        print("=" * 70)

    except Exception as e:
        print(f"\n[ERRO] Falha no parser de IA: {e}")
        import traceback
        traceback.print_exc()


async def listar_faturas_recentes():
    """Lista as faturas mais recentes com texto extraido"""
    print("=" * 70)
    print("FATURAS RECENTES COM TEXTO EXTRAIDO")
    print("=" * 70)

    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    result = supabase.table("faturas").select("id, uc_id, mes_referencia, ano_referencia, texto_extraido, arquivo_path").not_.is_("texto_extraido", "null").order("id", desc=True).limit(20).execute()

    if result.data:
        print(f"\nEncontradas {len(result.data)} faturas com texto:\n")
        for f in result.data:
            texto_len = len(f.get("texto_extraido", "") or "")
            print(f"  ID: {f['id']:<8} UC: {f['uc_id']:<6} Ref: {f['mes_referencia']}/{f['ano_referencia']}  Texto: {texto_len} chars")
    else:
        print("Nenhuma fatura com texto extraido encontrada.")


if __name__ == "__main__":
    # ID da fatura a testar
    FATURA_ID = 40434

    # Verificar se foi passado como argumento
    if len(sys.argv) > 1:
        if sys.argv[1] == "--list":
            asyncio.run(listar_faturas_recentes())
            sys.exit(0)
        FATURA_ID = int(sys.argv[1])

    asyncio.run(test_fatura_from_db(FATURA_ID))
