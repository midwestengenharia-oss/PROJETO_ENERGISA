"""
Testes do módulo Saques
"""

import pytest


class TestSaquesListar:
    """Testes de listagem de saques"""

    def test_listar_sem_token(self, client):
        """Acesso sem token deve retornar 401"""
        response = client.get("/api/saques")
        assert response.status_code == 401

    def test_listar_autenticado(self, client, auth_headers):
        """Deve retornar lista de saques"""
        if not auth_headers:
            pytest.skip("Sem autenticação")

        response = client.get("/api/saques", headers=auth_headers)
        assert response.status_code in [200, 403]


class TestSaquesMeus:
    """Testes de meus saques"""

    def test_meus_sem_token(self, client):
        """Acesso sem token deve retornar 401"""
        response = client.get("/api/saques/meus")
        assert response.status_code == 401

    def test_meus_autenticado(self, client, auth_headers):
        """Deve retornar lista de saques do usuário"""
        if not auth_headers:
            pytest.skip("Sem autenticação")

        response = client.get("/api/saques/meus", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestSaquesSaldo:
    """Testes de saldo de comissões"""

    def test_saldo_sem_token(self, client):
        """Acesso sem token deve retornar 401"""
        response = client.get("/api/saques/saldo")
        assert response.status_code == 401

    def test_saldo_autenticado(self, client, auth_headers):
        """Deve retornar saldo do usuário"""
        if not auth_headers:
            pytest.skip("Sem autenticação")

        response = client.get("/api/saques/saldo", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "saldo_disponivel" in data


class TestSaquesComissoes:
    """Testes de listagem de comissões"""

    def test_comissoes_sem_token(self, client):
        """Acesso sem token deve retornar 401"""
        response = client.get("/api/saques/comissoes")
        assert response.status_code == 401

    def test_comissoes_autenticado(self, client, auth_headers):
        """Deve retornar comissões do usuário"""
        if not auth_headers:
            pytest.skip("Sem autenticação")

        response = client.get("/api/saques/comissoes", headers=auth_headers)
        assert response.status_code == 200


class TestSaquesSolicitar:
    """Testes de solicitação de saque"""

    def test_solicitar_sem_token(self, client):
        """Solicitar sem token deve retornar 401"""
        response = client.post("/api/saques", json={
            "valor": 100.0,
            "dados_bancarios": {
                "tipo_conta": "PIX",
                "banco": "Banco do Brasil",
                "agencia": "1234",
                "conta": "12345",
                "pix_chave": "email@teste.com",
                "pix_tipo": "email",
                "titular_nome": "Teste",
                "titular_cpf_cnpj": "529.982.247-25"
            }
        })
        assert response.status_code == 401
