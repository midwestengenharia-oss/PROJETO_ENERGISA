"""
Teste do Parser de IA para Faturas Energisa
"""

import os
import sys

# Adicionar backend ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Carregar .env
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), 'backend', '.env'))

import json
from faturas.ai_parser import FaturaAIParser

# Texto de exemplo de uma fatura Energisa MT (OCR)
TEXTO_FATURA_EXEMPLO = """
SEGUNDA VIA Nº DO DOCUMENTO 003.015.657 NOTA FISCAL DE ENERGIA ELÉTRICA ELETRÔNICA - SERIE 0
ENERGISA MATO GROSSO - DISTRIBUIDORA DE ENERGIA S.A.
CNPJ: 03.467.321/0001-99 I.E.: 13.179.429-1
Av. Rubens de Mendonça, 1.500, Sala 901-A - CPA, 78050-000, Cuiabá - MT

CLASSIFICAÇÃO: Comercial
SUBCLASSE: Comercial - Cooperativa
Dados da Instalação:
SUBGRUPO: B3 MODALIDADE: Convencional (B) TENSÃO NOMINAL: 220V
IDENTIFICAÇÃO DA CARGA INSTALADA: Bifásica (003)

MARÇO DE 2025

Dados de Medição
MEDIDOR 75058066 CONST. MULT.
ELEM. DATA LEITURA LEITURA MEDIDO FATUR.
ANT ATUAL kWh kWh
7585-AT 11.02 10.03 76567 76812 245 245
7585-INJ 11.02 10.03 174 363 189 189
7585-INJ-FP 11.02 10.03 0 0 0 0

Nº CLIENTE: 6/10002053-2
CLASSE: Comercial
Nº MEDIDOR: 75058066
GRUPO/SUBGRUPO: B/B3
Nº INSTALAÇÃO: 3016556299
LOTE: UC-2025-22100

Mês/Ano: MAR/2025
Vencimento: 25/03/2025
Total a Pagar: R$ 110,37

Data Apresentação: 12/03/2025
Período de Consumo: 11/02/2025 a 10/03/2025
DIAS: 27

RUA CEREJEIRA, 2260 - ELDORADO
SORRISO - MT - 78890000

COMPOSIÇÃO DO FORNECIMENTO Período de Consumo: 11/02/2025 a 10/03/2025
DESCRIÇÃO Un Qtde Preço un Preço c/ Valor
s/ Tribut Tributos
CONSUMO EM KWH KWH 245 0,33825 0,51036 125,04
ENERGIA INJETADA oUC GDII MAR/2025 KWH -189 0,33825 0,51036 -96,46
AJUSTE DE DISPONIBILIDADE LEI 14300 KWH 189 0,12168 0,18362 34,70
BANDEIRA TARIFÁRIA VERDE 0,00

Adicional de Bandeira Tarifária: 0,00
Total de Lançamentos e Serviços: 46,79

LANCAMENTOS E SERVIÇOS
CIP/COSIP-CONTRIB ILUM PUBLICA 46,79

Valor Total da Fatura: 110,07
Valor dos Tributos: 35,26

ATENÇÃO:
Saldo Acumulado: 391 A expirar no próximo ciclo: 0 Créditos Expirados: 0

LEITURA APROXIMADA - Impedimento de acesso

RESUMO
VALOR TOTAL: R$ 110,07

TOTAL A PAGAR R$ 110,37
"""

def test_openai_parser():
    """Testa o parser usando OpenAI GPT-4o"""
    print("=" * 60)
    print("TESTE DO PARSER DE IA (OpenAI GPT-4o)")
    print("=" * 60)

    # Verificar API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("\n[ERRO] OPENAI_API_KEY nao configurada!")
        print("Configure no arquivo backend/.env")
        return False

    print(f"\n[OK] API Key encontrada: {api_key[:20]}...")

    # Criar parser
    print("\n[INFO] Inicializando parser OpenAI...")
    parser = FaturaAIParser(provider="openai")

    # Parsear fatura
    print("[INFO] Enviando texto da fatura para GPT-4o...")
    print("-" * 60)

    try:
        resultado = parser.parse(TEXTO_FATURA_EXEMPLO)

        print("\n[SUCESSO] Dados extraidos pela IA:\n")
        print(json.dumps(resultado, indent=2, ensure_ascii=False, default=str))

        # Validar campos criticos
        print("\n" + "=" * 60)
        print("VALIDACAO DOS CAMPOS CRITICOS:")
        print("=" * 60)

        checks = [
            ("vencimento", resultado.get("vencimento"), "2025-03-25"),
            ("total_a_pagar", resultado.get("total_a_pagar"), 110.37),
            ("consumo_kwh", resultado.get("itens_fatura", {}).get("consumo_kwh", {}).get("quantidade"), 245),
            ("ligacao", resultado.get("ligacao"), "BIFASICO"),
            ("saldo_acumulado", resultado.get("quadro_atencao", {}).get("saldo_acumulado"), 391),
        ]

        all_ok = True
        for nome, valor, esperado in checks:
            status = "[OK]" if valor is not None else "[FALHA]"
            if valor is None:
                all_ok = False
            print(f"  {status} {nome}: {valor} (esperado: {esperado})")

        # Verificar energia injetada
        injetada = resultado.get("itens_fatura", {}).get("energia_injetada_ouc", [])
        if injetada:
            print(f"  [OK] energia_injetada_ouc: {len(injetada)} item(s)")
            for item in injetada:
                print(f"       - {item.get('descricao')}: {item.get('quantidade')} kWh")
        else:
            print("  [FALHA] energia_injetada_ouc: nenhum item")
            all_ok = False

        return all_ok

    except Exception as e:
        print(f"\n[ERRO] Falha ao parsear: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_anthropic_parser():
    """Testa o parser usando Anthropic Claude"""
    print("=" * 60)
    print("TESTE DO PARSER DE IA (Anthropic Claude)")
    print("=" * 60)

    # Verificar API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("\n[INFO] ANTHROPIC_API_KEY nao configurada - pulando teste")
        return None

    print(f"\n[OK] API Key encontrada: {api_key[:20]}...")

    parser = FaturaAIParser(provider="anthropic")

    try:
        resultado = parser.parse(TEXTO_FATURA_EXEMPLO)
        print("\n[SUCESSO] Dados extraidos pela IA (Claude):\n")
        print(json.dumps(resultado, indent=2, ensure_ascii=False, default=str))
        return True
    except Exception as e:
        print(f"\n[ERRO] Falha: {e}")
        return False


if __name__ == "__main__":
    print("\n")
    print("*" * 60)
    print("*  TESTE DO PARSER DE FATURAS COM IA                      *")
    print("*" * 60)
    print("\n")

    # Testar OpenAI
    openai_ok = test_openai_parser()

    print("\n")

    # Testar Anthropic (se configurado)
    # anthropic_ok = test_anthropic_parser()

    print("\n")
    print("=" * 60)
    print("RESULTADO FINAL:")
    print("=" * 60)

    if openai_ok:
        print("[SUCESSO] Parser de IA funcionando corretamente!")
    else:
        print("[FALHA] Parser de IA com problemas")

    print("\n")
