"""
Teste: Parser IA -> Calculo de Cobranca Automatica
Simula o fluxo completo como se fosse o botao "Gerar Cobranca Automatica"
"""

import os
import sys
import json
import asyncio
import base64
import io

# Adicionar backend ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Carregar .env
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), 'backend', '.env'))

from supabase import create_client
from faturas.ai_parser import FaturaAIParser
import pdfplumber

# Configurar Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")


def extrair_texto_pdf_base64(pdf_base64: str) -> str:
    """Extrai texto de um PDF em base64"""
    pdf_bytes = base64.b64decode(pdf_base64)
    texto = ""
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            texto += page.extract_text() or ""
    return texto


async def processar_fatura_com_ia(fatura_id: int) -> dict:
    """
    Processa uma fatura usando IA e retorna JSON estruturado
    para calculo de cobranca.
    """

    print(f"\n{'='*70}")
    print(f"PROCESSANDO FATURA #{fatura_id} COM IA")
    print(f"{'='*70}")

    # Conectar ao Supabase
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Buscar fatura
    result = supabase.table("faturas").select("*").eq("id", fatura_id).execute()

    if not result.data:
        return {"erro": f"Fatura {fatura_id} nao encontrada"}

    fatura = result.data[0]
    print(f"[OK] Fatura encontrada - UC: {fatura.get('uc_id')}, Ref: {fatura.get('mes_referencia')}/{fatura.get('ano_referencia')}")

    # Extrair texto do PDF
    texto_extraido = fatura.get("texto_extraido")

    if not texto_extraido:
        pdf_base64 = fatura.get("pdf_base64")
        if pdf_base64:
            print(f"[INFO] Extraindo texto do PDF...")
            texto_extraido = extrair_texto_pdf_base64(pdf_base64)
            print(f"[OK] Texto extraido: {len(texto_extraido)} chars")
        else:
            return {"erro": "Sem PDF disponivel"}

    # Parser IA
    print(f"[INFO] Enviando para GPT-4o...")
    parser = FaturaAIParser(provider="openai")
    dados_ia = parser.parse(texto_extraido)
    print(f"[OK] Dados extraidos pela IA")

    # Montar JSON estruturado para cobranca
    resultado = {
        "fatura_id": fatura_id,
        "uc_id": fatura.get("uc_id"),
        "fonte": "IA_GPT4o",

        # Identificacao
        "codigo_cliente": dados_ia.get("codigo_cliente"),
        "ligacao": dados_ia.get("ligacao"),
        "bandeira_tarifaria": dados_ia.get("bandeira_tarifaria"),

        # Datas
        "mes_ano_referencia": dados_ia.get("mes_ano_referencia"),
        "vencimento": dados_ia.get("vencimento"),
        "data_apresentacao": dados_ia.get("data_apresentacao"),
        "dias": dados_ia.get("dias"),

        # Leituras
        "leitura_anterior": dados_ia.get("leitura_anterior"),
        "leitura_anterior_data": dados_ia.get("leitura_anterior_data"),
        "leitura_atual": dados_ia.get("leitura_atual"),
        "leitura_atual_data": dados_ia.get("leitura_atual_data"),

        # Consumo e Energia
        "consumo_total_kwh": dados_ia.get("consumo_total_kwh"),
        "energia_injetada_total_kwh": dados_ia.get("energia_injetada_total_kwh"),

        # Itens da Fatura
        "itens_fatura": {
            "consumo_kwh": dados_ia.get("itens_fatura", {}).get("consumo_kwh"),
            "energia_injetada_ouc": dados_ia.get("itens_fatura", {}).get("energia_injetada_ouc", []),
            "energia_injetada_muc": dados_ia.get("itens_fatura", {}).get("energia_injetada_muc", []),
            "ajuste_lei_14300": dados_ia.get("itens_fatura", {}).get("ajuste_lei_14300"),
            "lancamentos_e_servicos": dados_ia.get("itens_fatura", {}).get("lancamentos_e_servicos", [])
        },

        # Totais
        "totais": {
            "adicionais_bandeira": dados_ia.get("totais", {}).get("adicionais_bandeira"),
            "lancamentos_e_servicos": dados_ia.get("totais", {}).get("lancamentos_e_servicos"),
            "total_geral_fatura": dados_ia.get("totais", {}).get("total_geral_fatura")
        },
        "total_a_pagar": dados_ia.get("total_a_pagar"),

        # Creditos GD
        "quadro_atencao": {
            "saldo_acumulado": dados_ia.get("quadro_atencao", {}).get("saldo_acumulado"),
            "a_expirar_proximo_ciclo": dados_ia.get("quadro_atencao", {}).get("a_expirar_proximo_ciclo"),
            "creditos_expirados": dados_ia.get("quadro_atencao", {}).get("creditos_expirados")
        },

        # Dados da Instalacao
        "dados_instalacao": {
            "numero_medidor": dados_ia.get("dados_instalacao", {}).get("numero_medidor"),
            "numero_instalacao": dados_ia.get("dados_instalacao", {}).get("numero_instalacao"),
            "classe_consumo": dados_ia.get("dados_instalacao", {}).get("classe_consumo"),
            "modalidade_tarifaria": dados_ia.get("dados_instalacao", {}).get("modalidade_tarifaria"),
            "tensao_nominal": dados_ia.get("dados_instalacao", {}).get("tensao_nominal"),
            "endereco": dados_ia.get("dados_instalacao", {}).get("endereco")
        },

        # Modelo GD detectado
        "modelo_gd": "GDII" if dados_ia.get("itens_fatura", {}).get("ajuste_lei_14300") else "GDI",

        # Dados para calculo de cobranca
        "calculo_cobranca": {
            "consumo_kwh": dados_ia.get("consumo_total_kwh"),
            "injetada_kwh": dados_ia.get("energia_injetada_total_kwh"),
            "compensado_kwh": abs(dados_ia.get("itens_fatura", {}).get("energia_injetada_ouc", [{}])[0].get("quantidade", 0)) if dados_ia.get("itens_fatura", {}).get("energia_injetada_ouc") else 0,
            "tarifa_energia": dados_ia.get("itens_fatura", {}).get("consumo_kwh", {}).get("preco_unit_com_tributos"),
            "valor_consumo": dados_ia.get("itens_fatura", {}).get("consumo_kwh", {}).get("valor"),
            "valor_injetada": abs(dados_ia.get("itens_fatura", {}).get("energia_injetada_ouc", [{}])[0].get("valor", 0)) if dados_ia.get("itens_fatura", {}).get("energia_injetada_ouc") else 0,
            "valor_ajuste_gdii": dados_ia.get("itens_fatura", {}).get("ajuste_lei_14300", {}).get("valor") if dados_ia.get("itens_fatura", {}).get("ajuste_lei_14300") else 0,
            "valor_bandeira": dados_ia.get("totais", {}).get("adicionais_bandeira"),
            "valor_iluminacao": next((l.get("valor") for l in dados_ia.get("itens_fatura", {}).get("lancamentos_e_servicos", []) if "ilum" in l.get("descricao", "").lower()), 0),
            "saldo_acumulado_kwh": dados_ia.get("quadro_atencao", {}).get("saldo_acumulado")
        }
    }

    return resultado


async def main():
    # ID da fatura
    FATURA_ID = 40577

    if len(sys.argv) > 1:
        FATURA_ID = int(sys.argv[1])

    # Processar
    resultado = await processar_fatura_com_ia(FATURA_ID)

    # Exibir JSON
    print(f"\n{'='*70}")
    print("JSON PARA CALCULO DE COBRANCA:")
    print(f"{'='*70}\n")

    print(json.dumps(resultado, indent=2, ensure_ascii=False, default=str))

    # Salvar em arquivo
    output_file = f"fatura_{FATURA_ID}_ia.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False, default=str)

    print(f"\n[OK] JSON salvo em: {output_file}")

    # Resumo para cobranca
    calc = resultado.get("calculo_cobranca", {})
    print(f"\n{'='*70}")
    print("RESUMO PARA COBRANCA:")
    print(f"{'='*70}")
    print(f"  Modelo GD: {resultado.get('modelo_gd')}")
    print(f"  Ligacao: {resultado.get('ligacao')}")
    print(f"  Vencimento: {resultado.get('vencimento')}")
    print(f"  ")
    print(f"  Consumo: {calc.get('consumo_kwh')} kWh = R$ {calc.get('valor_consumo')}")
    print(f"  Injetada: {calc.get('injetada_kwh')} kWh = -R$ {calc.get('valor_injetada')}")
    print(f"  Ajuste GDII: R$ {calc.get('valor_ajuste_gdii')}")
    print(f"  Bandeira: R$ {calc.get('valor_bandeira')}")
    print(f"  Iluminacao: R$ {calc.get('valor_iluminacao')}")
    print(f"  ")
    print(f"  Saldo Acumulado: {calc.get('saldo_acumulado_kwh')} kWh")
    print(f"  ")
    print(f"  TOTAL FATURA: R$ {resultado.get('total_a_pagar')}")
    print(f"{'='*70}")


if __name__ == "__main__":
    asyncio.run(main())
