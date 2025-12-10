"""
Teste Completo: Fatura -> IA Parser -> Calculo Cobranca -> Resultado
Simula o fluxo de "Gerar Cobranca Automatica"
"""

import os
import sys
import json
import asyncio
import base64
import io
from decimal import Decimal
from datetime import datetime, date, timedelta

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

# Constantes de calculo
DESCONTO_ASSINATURA = Decimal("0.30")  # 30%
TAXA_MINIMA = {
    "MONOFASICO": 30,
    "BIFASICO": 50,
    "TRIFASICO": 100
}


def extrair_texto_pdf_base64(pdf_base64: str) -> str:
    """Extrai texto de um PDF em base64"""
    pdf_bytes = base64.b64decode(pdf_base64)
    texto = ""
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            texto += page.extract_text() or ""
    return texto


def calcular_cobranca(dados_ia: dict) -> dict:
    """
    Calcula a cobranca baseada nos dados extraidos pela IA.

    Regras:
    - GD II: Cobra ajuste Lei 14.300 + iluminacao + bandeira
    - GD I: Cobra taxa minima ou excedente + iluminacao + bandeira
    - Assinatura: 30% de desconto na tarifa de energia
    """

    calc = dados_ia.get("calculo_cobranca", {})
    modelo_gd = dados_ia.get("modelo_gd", "GDII")
    ligacao = dados_ia.get("ligacao", "BIFASICO")

    # Tarifas
    tarifa_base = Decimal(str(calc.get("tarifa_energia", 0) or 0))
    tarifa_assinatura = tarifa_base * (Decimal("1") - DESCONTO_ASSINATURA)

    # Valores de energia
    consumo_kwh = Decimal(str(calc.get("consumo_kwh", 0) or 0))
    injetada_kwh = Decimal(str(calc.get("injetada_kwh", 0) or 0))
    compensado_kwh = Decimal(str(calc.get("compensado_kwh", 0) or 0))

    # Gap = consumo - compensado
    gap_kwh = max(Decimal("0"), consumo_kwh - compensado_kwh)

    # Valores base
    valor_energia_base = injetada_kwh * tarifa_base
    valor_energia_assinatura = injetada_kwh * tarifa_assinatura

    # Encargos
    taxa_minima_kwh = TAXA_MINIMA.get(ligacao, 50)
    taxa_minima_valor = Decimal("0")
    energia_excedente_kwh = 0
    energia_excedente_valor = Decimal("0")
    disponibilidade_valor = Decimal("0")

    if modelo_gd == "GDI":
        # GD I: Taxa minima ou excedente
        if gap_kwh > taxa_minima_kwh:
            energia_excedente_kwh = int(gap_kwh)
            energia_excedente_valor = gap_kwh * tarifa_base
        else:
            taxa_minima_valor = Decimal(str(taxa_minima_kwh)) * tarifa_base
    else:
        # GD II: Ajuste Lei 14.300
        disponibilidade_valor = Decimal(str(calc.get("valor_ajuste_gdii", 0) or 0))

    # Extras
    bandeiras_valor = Decimal(str(calc.get("valor_bandeira", 0) or 0))
    iluminacao_valor = Decimal(str(calc.get("valor_iluminacao", 0) or 0))

    # Encargos fixos
    encargos_fixos = (
        taxa_minima_valor +
        energia_excedente_valor +
        disponibilidade_valor +
        bandeiras_valor +
        iluminacao_valor
    )

    # Totais
    valor_sem_assinatura = valor_energia_base + encargos_fixos
    valor_com_assinatura = valor_energia_assinatura + encargos_fixos
    economia_mes = valor_sem_assinatura - valor_com_assinatura

    # Vencimento (1 dia antes da fatura)
    vencimento_fatura = dados_ia.get("vencimento")
    if vencimento_fatura:
        if isinstance(vencimento_fatura, str):
            vencimento_fatura = datetime.strptime(vencimento_fatura, "%Y-%m-%d").date()
        vencimento_cobranca = vencimento_fatura - timedelta(days=1)
    else:
        vencimento_cobranca = None

    return {
        "modelo_gd": modelo_gd,
        "tipo_ligacao": ligacao,

        # Metricas
        "consumo_kwh": float(consumo_kwh),
        "injetada_kwh": float(injetada_kwh),
        "compensado_kwh": float(compensado_kwh),
        "gap_kwh": float(gap_kwh),

        # Tarifas
        "tarifa_base": float(tarifa_base),
        "tarifa_assinatura": float(tarifa_assinatura),
        "desconto_percentual": float(DESCONTO_ASSINATURA * 100),

        # Valores de energia
        "valor_energia_base": float(valor_energia_base),
        "valor_energia_assinatura": float(valor_energia_assinatura),

        # Encargos GD I
        "taxa_minima_kwh": taxa_minima_kwh,
        "taxa_minima_valor": float(taxa_minima_valor),
        "energia_excedente_kwh": energia_excedente_kwh,
        "energia_excedente_valor": float(energia_excedente_valor),

        # Encargos GD II
        "disponibilidade_valor": float(disponibilidade_valor),

        # Extras
        "bandeiras_valor": float(bandeiras_valor),
        "iluminacao_valor": float(iluminacao_valor),

        # Totais
        "valor_sem_assinatura": float(valor_sem_assinatura),
        "valor_com_assinatura": float(valor_com_assinatura),
        "economia_mes": float(economia_mes),
        "valor_total_cobranca": float(valor_com_assinatura),

        # Vencimentos
        "vencimento_fatura": str(vencimento_fatura) if vencimento_fatura else None,
        "vencimento_cobranca": str(vencimento_cobranca) if vencimento_cobranca else None,

        # Creditos
        "saldo_acumulado_kwh": calc.get("saldo_acumulado_kwh", 0)
    }


async def gerar_cobranca_completa(fatura_id: int):
    """Fluxo completo de geracao de cobranca"""

    print(f"\n{'#'*70}")
    print(f"#  GERACAO DE COBRANCA AUTOMATICA - FATURA #{fatura_id}")
    print(f"{'#'*70}")

    # 1. Buscar fatura
    print(f"\n[ETAPA 1] Buscando fatura no banco...")
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    result = supabase.table("faturas").select("*").eq("id", fatura_id).execute()

    if not result.data:
        print(f"[ERRO] Fatura {fatura_id} nao encontrada!")
        return

    fatura = result.data[0]
    print(f"  -> UC: {fatura.get('uc_id')}")
    print(f"  -> Ref: {fatura.get('mes_referencia')}/{fatura.get('ano_referencia')}")
    print(f"  -> Valor Fatura: R$ {fatura.get('valor_fatura')}")

    # 2. Extrair texto do PDF
    print(f"\n[ETAPA 2] Extraindo texto do PDF...")
    texto = fatura.get("texto_extraido")
    if not texto:
        pdf_base64 = fatura.get("pdf_base64")
        if pdf_base64:
            texto = extrair_texto_pdf_base64(pdf_base64)
            print(f"  -> Texto extraido: {len(texto)} caracteres")
        else:
            print(f"  [ERRO] Sem PDF disponivel!")
            return
    else:
        print(f"  -> Texto ja disponivel: {len(texto)} caracteres")

    # 3. Parser IA
    print(f"\n[ETAPA 3] Processando com IA (GPT-4o)...")
    parser = FaturaAIParser(provider="openai")
    dados_ia_raw = parser.parse(texto)

    # Montar estrutura
    dados_ia = {
        "fatura_id": fatura_id,
        "uc_id": fatura.get("uc_id"),
        "codigo_cliente": dados_ia_raw.get("codigo_cliente"),
        "ligacao": dados_ia_raw.get("ligacao"),
        "vencimento": dados_ia_raw.get("vencimento"),
        "modelo_gd": "GDII" if dados_ia_raw.get("itens_fatura", {}).get("ajuste_lei_14300") else "GDI",
        "calculo_cobranca": {
            "consumo_kwh": dados_ia_raw.get("consumo_total_kwh"),
            "injetada_kwh": dados_ia_raw.get("energia_injetada_total_kwh"),
            "compensado_kwh": abs(dados_ia_raw.get("itens_fatura", {}).get("energia_injetada_ouc", [{}])[0].get("quantidade", 0)) if dados_ia_raw.get("itens_fatura", {}).get("energia_injetada_ouc") else 0,
            "tarifa_energia": dados_ia_raw.get("itens_fatura", {}).get("consumo_kwh", {}).get("preco_unit_com_tributos"),
            "valor_consumo": dados_ia_raw.get("itens_fatura", {}).get("consumo_kwh", {}).get("valor"),
            "valor_injetada": abs(dados_ia_raw.get("itens_fatura", {}).get("energia_injetada_ouc", [{}])[0].get("valor", 0)) if dados_ia_raw.get("itens_fatura", {}).get("energia_injetada_ouc") else 0,
            "valor_ajuste_gdii": dados_ia_raw.get("itens_fatura", {}).get("ajuste_lei_14300", {}).get("valor") if dados_ia_raw.get("itens_fatura", {}).get("ajuste_lei_14300") else 0,
            "valor_bandeira": dados_ia_raw.get("totais", {}).get("adicionais_bandeira", 0),
            "valor_iluminacao": next((l.get("valor") for l in dados_ia_raw.get("itens_fatura", {}).get("lancamentos_e_servicos", []) if "ilum" in l.get("descricao", "").lower()), 0),
            "saldo_acumulado_kwh": dados_ia_raw.get("quadro_atencao", {}).get("saldo_acumulado", 0)
        }
    }

    print(f"  -> Modelo GD: {dados_ia['modelo_gd']}")
    print(f"  -> Ligacao: {dados_ia['ligacao']}")
    print(f"  -> Consumo: {dados_ia['calculo_cobranca']['consumo_kwh']} kWh")
    print(f"  -> Injetada: {dados_ia['calculo_cobranca']['injetada_kwh']} kWh")

    # 4. Calcular cobranca
    print(f"\n[ETAPA 4] Calculando cobranca...")
    cobranca = calcular_cobranca(dados_ia)

    # 5. Resultado
    print(f"\n{'='*70}")
    print(f"  RESULTADO DA COBRANCA")
    print(f"{'='*70}")

    print(f"\n  DADOS DA FATURA:")
    print(f"  {'-'*50}")
    print(f"  Fatura ID:        {fatura_id}")
    print(f"  UC ID:            {dados_ia['uc_id']}")
    print(f"  Codigo Cliente:   {dados_ia['codigo_cliente']}")
    print(f"  Modelo GD:        {cobranca['modelo_gd']}")
    print(f"  Tipo Ligacao:     {cobranca['tipo_ligacao']}")

    print(f"\n  ENERGIA:")
    print(f"  {'-'*50}")
    print(f"  Consumo:          {cobranca['consumo_kwh']:,.0f} kWh")
    print(f"  Injetada:         {cobranca['injetada_kwh']:,.0f} kWh")
    print(f"  Compensado:       {cobranca['compensado_kwh']:,.0f} kWh")
    print(f"  Gap:              {cobranca['gap_kwh']:,.0f} kWh")
    print(f"  Saldo Acumulado:  {cobranca['saldo_acumulado_kwh']:,} kWh")

    print(f"\n  TARIFAS:")
    print(f"  {'-'*50}")
    print(f"  Tarifa Base:      R$ {cobranca['tarifa_base']:.6f}/kWh")
    print(f"  Desconto:         {cobranca['desconto_percentual']:.0f}%")
    print(f"  Tarifa Assinat:   R$ {cobranca['tarifa_assinatura']:.6f}/kWh")

    print(f"\n  VALORES DE ENERGIA:")
    print(f"  {'-'*50}")
    print(f"  Sem Assinatura:   R$ {cobranca['valor_energia_base']:,.2f}")
    print(f"  Com Assinatura:   R$ {cobranca['valor_energia_assinatura']:,.2f}")

    print(f"\n  ENCARGOS:")
    print(f"  {'-'*50}")
    if cobranca['modelo_gd'] == "GDI":
        print(f"  Taxa Minima:      {cobranca['taxa_minima_kwh']} kWh = R$ {cobranca['taxa_minima_valor']:,.2f}")
        print(f"  Excedente:        {cobranca['energia_excedente_kwh']} kWh = R$ {cobranca['energia_excedente_valor']:,.2f}")
    else:
        print(f"  Ajuste GDII:      R$ {cobranca['disponibilidade_valor']:,.2f}")
    print(f"  Bandeira:         R$ {cobranca['bandeiras_valor']:,.2f}")
    print(f"  Iluminacao:       R$ {cobranca['iluminacao_valor']:,.2f}")

    print(f"\n  TOTAIS:")
    print(f"  {'-'*50}")
    print(f"  Sem Assinatura:   R$ {cobranca['valor_sem_assinatura']:,.2f}")
    print(f"  Com Assinatura:   R$ {cobranca['valor_com_assinatura']:,.2f}")
    print(f"  ECONOMIA:         R$ {cobranca['economia_mes']:,.2f}")

    print(f"\n  {'='*50}")
    print(f"  VALOR DA COBRANCA:  R$ {cobranca['valor_total_cobranca']:,.2f}")
    print(f"  {'='*50}")

    print(f"\n  VENCIMENTOS:")
    print(f"  {'-'*50}")
    print(f"  Venc. Fatura:     {cobranca['vencimento_fatura']}")
    print(f"  Venc. Cobranca:   {cobranca['vencimento_cobranca']}")

    # 6. JSON completo
    resultado_completo = {
        "fatura": {
            "id": fatura_id,
            "uc_id": dados_ia['uc_id'],
            "codigo_cliente": dados_ia['codigo_cliente'],
            "mes_referencia": fatura.get('mes_referencia'),
            "ano_referencia": fatura.get('ano_referencia'),
            "valor_fatura": fatura.get('valor_fatura')
        },
        "dados_extraidos_ia": dados_ia,
        "cobranca_calculada": cobranca
    }

    print(f"\n{'='*70}")
    print(f"  JSON COMPLETO:")
    print(f"{'='*70}")
    print(json.dumps(resultado_completo, indent=2, ensure_ascii=False, default=str))

    # Salvar
    output_file = f"cobranca_fatura_{fatura_id}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(resultado_completo, f, indent=2, ensure_ascii=False, default=str)

    print(f"\n[OK] Salvo em: {output_file}")

    return resultado_completo


if __name__ == "__main__":
    FATURA_ID = 40616

    if len(sys.argv) > 1:
        FATURA_ID = int(sys.argv[1])

    asyncio.run(gerar_cobranca_completa(FATURA_ID))
