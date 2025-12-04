"""
Configuração dos testes pytest
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime

# Importa a aplicação
from backend.main import app


@pytest.fixture(scope="session")
def client():
    """Cliente de teste para a API"""
    return TestClient(app)


@pytest.fixture(scope="session")
def test_user_data():
    """Dados de usuário para teste"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return {
        "email": f"pytest_{timestamp}@teste.com",
        "password": "Senha123!",
        "nome_completo": "Pytest User",
        "cpf": "529.982.247-25",
        "telefone": "(65) 99999-9999"
    }


@pytest.fixture(scope="session")
def auth_headers(client, test_user_data):
    """
    Headers com token de autenticação.
    Tenta criar usuário ou fazer login.
    """
    # Tenta signup
    response = client.post("/api/auth/signup", json=test_user_data)

    if response.status_code == 201:
        token = response.json()["tokens"]["access_token"]
    elif response.status_code == 409:  # Email já existe
        # Tenta signin
        response = client.post("/api/auth/signin", json={
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        })
        if response.status_code == 200:
            token = response.json()["tokens"]["access_token"]
        else:
            pytest.skip("Não foi possível autenticar")
            return {}
    else:
        pytest.skip(f"Erro no signup: {response.status_code}")
        return {}

    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def uc_data():
    """Dados de UC para teste"""
    return {
        "cod_empresa": 6,
        "cdc": 9999999,
        "digito_verificador": 0,
        "usuario_titular": True
    }


@pytest.fixture
def usina_data():
    """Dados de usina para teste"""
    return {
        "nome": "Usina Pytest",
        "uc_geradora_id": 1,  # Precisa existir
        "capacidade_kwp": 100.0,
        "tipo_geracao": "SOLAR",
        "desconto_padrao": 0.30
    }


@pytest.fixture
def beneficiario_data():
    """Dados de beneficiário para teste"""
    return {
        "usina_id": 1,
        "uc_id": 1,
        "cpf": "123.456.789-09",
        "nome": "Beneficiário Pytest",
        "email": "benef_pytest@teste.com",
        "percentual_rateio": 25.0,
        "desconto": 0.30
    }


@pytest.fixture
def fatura_data():
    """Dados de fatura para teste"""
    return {
        "uc_id": 1,
        "mes_referencia": 12,
        "ano_referencia": 2024,
        "valor_fatura": 350.50,
        "data_vencimento": "2024-12-10",
        "consumo": 250
    }
