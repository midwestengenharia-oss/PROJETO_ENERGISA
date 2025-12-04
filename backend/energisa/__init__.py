"""
Energisa - Gateway de integração com portal da Energisa
Módulo preservado do gateway original (scraping + integração)
"""

from backend.energisa.service import EnergisaService
from backend.energisa.session_manager import SessionManager
from backend.energisa.calculadora import (
    calcular_economia_mensal,
    calcular_projecao_10_anos,
    processar_faturas
)
from backend.energisa.aneel_api import (
    buscar_tarifa_b1,
    buscar_fiob,
    get_tarifas_com_fallback
)
from backend.energisa.router import router

__all__ = [
    "EnergisaService",
    "SessionManager",
    "calcular_economia_mensal",
    "calcular_projecao_10_anos",
    "processar_faturas",
    "buscar_tarifa_b1",
    "buscar_fiob",
    "get_tarifas_com_fallback",
    "router"
]
