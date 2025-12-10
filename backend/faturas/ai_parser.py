"""
Parser de Faturas usando IA (Claude/OpenAI)

Extrai dados estruturados do texto de faturas usando LLMs.
Muito mais robusto que regex para textos OCR mal formatados.
"""

import os
import json
import logging
from typing import Optional
from decimal import Decimal
from datetime import date

logger = logging.getLogger(__name__)


# Schema JSON que o LLM deve retornar
EXTRACTION_SCHEMA = """
{
    "codigo_cliente": "string (formato 6/XXXXXXXX-X)",
    "ligacao": "MONOFASICO | BIFASICO | TRIFASICO",
    "data_apresentacao": "YYYY-MM-DD",
    "mes_ano_referencia": "YYYY-MM",
    "vencimento": "YYYY-MM-DD",
    "total_a_pagar": number,

    "leitura_anterior_data": "YYYY-MM-DD",
    "leitura_atual_data": "YYYY-MM-DD",
    "dias": number (1-45),
    "leitura_anterior": number (valor do medidor),
    "leitura_atual": number (valor do medidor),

    "itens_fatura": {
        "consumo_kwh": {
            "quantidade": number,
            "preco_unit_com_tributos": number,
            "valor": number
        },
        "energia_injetada_ouc": [
            {
                "descricao": "string",
                "tipo_gd": "GDI | GDII",
                "quantidade": number,
                "preco_unit_com_tributos": number,
                "valor": number,
                "mes_ano_referencia_item": "YYYY-MM"
            }
        ],
        "energia_injetada_muc": [],
        "ajuste_lei_14300": {
            "quantidade": number,
            "preco_unit_com_tributos": number,
            "valor": number
        },
        "lancamentos_e_servicos": [
            {"descricao": "string", "valor": number}
        ]
    },

    "totais": {
        "adicionais_bandeira": number,
        "lancamentos_e_servicos": number,
        "total_geral_fatura": number
    },

    "quadro_atencao": {
        "saldo_acumulado": number,
        "a_expirar_proximo_ciclo": number,
        "creditos_expirados": number
    },

    "dados_instalacao": {
        "numero_medidor": "string",
        "numero_instalacao": "string",
        "classe_consumo": "RESIDENCIAL | COMERCIAL | INDUSTRIAL | RURAL",
        "modalidade_tarifaria": "CONVENCIONAL | BRANCA | AZUL | VERDE",
        "tensao_nominal": "string (ex: 127V, 220V)",
        "endereco": "string"
    },

    "bandeira_tarifaria": "VERDE | AMARELA | VERMELHA I | VERMELHA II",
    "consumo_total_kwh": number,
    "energia_injetada_total_kwh": number
}
"""

SYSTEM_PROMPT = """Você é um especialista em extrair dados estruturados de faturas de energia elétrica brasileiras (Energisa).

Extraia os dados do texto da fatura e retorne APENAS um JSON válido, sem markdown ou explicações.

Regras importantes:
1. Use null para campos não encontrados
2. Datas no formato YYYY-MM-DD
3. Valores monetários como números decimais (ex: 127.50, não "R$ 127,50")
4. kWh como números inteiros
5. GDII = Geração Distribuída II (Lei 14.300/22), GDI = modelo anterior
6. Energia injetada oUC = própria UC, mUC = múltiplas UCs
7. O ajuste Lei 14.300 indica modelo GDII

Schema esperado:
""" + EXTRACTION_SCHEMA


class FaturaAIParser:
    """Parser de faturas usando IA"""

    def __init__(self, provider: str = "anthropic"):
        """
        Inicializa o parser.

        Args:
            provider: "anthropic" (Claude) ou "openai" (GPT)
        """
        self.provider = provider
        self._client = None

    def _get_anthropic_client(self):
        """Retorna cliente Anthropic (lazy loading)"""
        if self._client is None:
            try:
                import anthropic
                api_key = os.getenv("ANTHROPIC_API_KEY")
                if not api_key:
                    raise ValueError("ANTHROPIC_API_KEY não configurada")
                self._client = anthropic.Anthropic(api_key=api_key)
            except ImportError:
                raise ImportError("Instale anthropic: pip install anthropic")
        return self._client

    def _get_openai_client(self):
        """Retorna cliente OpenAI (lazy loading)"""
        if self._client is None:
            try:
                import openai
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    raise ValueError("OPENAI_API_KEY não configurada")
                self._client = openai.OpenAI(api_key=api_key)
            except ImportError:
                raise ImportError("Instale openai: pip install openai")
        return self._client

    def parse(self, texto: str) -> dict:
        """
        Extrai dados estruturados do texto da fatura usando IA.

        Args:
            texto: Texto extraído do PDF da fatura

        Returns:
            Dados estruturados como dicionário
        """
        if self.provider == "anthropic":
            return self._parse_with_anthropic(texto)
        elif self.provider == "openai":
            return self._parse_with_openai(texto)
        else:
            raise ValueError(f"Provider não suportado: {self.provider}")

    def _parse_with_anthropic(self, texto: str) -> dict:
        """Parse usando Claude (Anthropic)"""
        client = self._get_anthropic_client()

        logger.info("Enviando texto para Claude extrair dados da fatura")

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": f"Extraia os dados desta fatura de energia:\n\n{texto}"
                }
            ]
        )

        # Extrair texto da resposta
        response_text = response.content[0].text

        # Limpar e parsear JSON
        return self._parse_json_response(response_text)

    def _parse_with_openai(self, texto: str) -> dict:
        """Parse usando GPT (OpenAI)"""
        client = self._get_openai_client()

        logger.info("Enviando texto para GPT extrair dados da fatura")

        response = client.chat.completions.create(
            model="gpt-4o",
            max_tokens=4096,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Extraia os dados desta fatura de energia:\n\n{texto}"}
            ],
            response_format={"type": "json_object"}
        )

        response_text = response.choices[0].message.content
        return self._parse_json_response(response_text)

    def _parse_json_response(self, response_text: str) -> dict:
        """Limpa e parseia resposta JSON do LLM"""
        # Remover markdown se presente
        text = response_text.strip()
        if text.startswith("```"):
            # Remover ```json e ```
            lines = text.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines)

        try:
            data = json.loads(text)
            logger.info("Dados extraídos com sucesso via IA")
            return self._normalize_data(data)
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao parsear JSON da IA: {e}")
            logger.debug(f"Resposta: {text[:500]}")
            raise ValueError(f"IA retornou JSON inválido: {e}")

    def _normalize_data(self, data: dict) -> dict:
        """Normaliza dados para o formato esperado pelo schema"""
        # Garantir estrutura mínima
        if "itens_fatura" not in data:
            data["itens_fatura"] = {}

        itens = data["itens_fatura"]
        if "energia_injetada_ouc" not in itens:
            itens["energia_injetada_ouc"] = []
        if "energia_injetada_muc" not in itens:
            itens["energia_injetada_muc"] = []
        if "lancamentos_e_servicos" not in itens:
            itens["lancamentos_e_servicos"] = []

        if "totais" not in data:
            data["totais"] = {}

        return data


def parse_fatura_com_ia(texto: str, provider: str = "anthropic") -> dict:
    """
    Função utilitária para parsear fatura com IA.

    Args:
        texto: Texto do PDF da fatura
        provider: "anthropic" ou "openai"

    Returns:
        Dados estruturados
    """
    parser = FaturaAIParser(provider=provider)
    return parser.parse(texto)
