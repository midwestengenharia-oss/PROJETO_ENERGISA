"""
Testes do módulo Contratos
"""

import pytest


class TestContratosListar:
    """Testes de listagem de contratos"""

    def test_listar_sem_token(self, client):
        """Acesso sem token deve retornar 401"""
        response = client.get("/api/contratos")
        assert response.status_code == 401

    def test_listar_autenticado(self, client, auth_headers):
        """Deve retornar lista de contratos"""
        if not auth_headers:
            pytest.skip("Sem autenticação")

        response = client.get("/api/contratos", headers=auth_headers)
        assert response.status_code in [200, 403]

        if response.status_code == 200:
            data = response.json()
            assert "contratos" in data
            assert "total" in data


class TestContratosMeus:
    """Testes de meus contratos"""

    def test_meus_sem_token(self, client):
        """Acesso sem token deve retornar 401"""
        response = client.get("/api/contratos/meus")
        assert response.status_code == 401

    def test_meus_autenticado(self, client, auth_headers):
        """Deve retornar lista de contratos do usuário"""
        if not auth_headers:
            pytest.skip("Sem autenticação")

        response = client.get("/api/contratos/meus", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestContratosEstatisticas:
    """Testes de estatísticas de contratos"""

    def test_estatisticas_sem_token(self, client):
        """Acesso sem token deve retornar 401"""
        response = client.get("/api/contratos/estatisticas")
        assert response.status_code == 401


class TestContratosBuscar:
    """Testes de busca de contrato"""

    def test_buscar_sem_token(self, client):
        """Buscar sem token deve retornar 401"""
        response = client.get("/api/contratos/1")
        assert response.status_code == 401

    def test_buscar_inexistente(self, client, auth_headers):
        """Contrato inexistente deve retornar 404"""
        if not auth_headers:
            pytest.skip("Sem autenticação")

        response = client.get("/api/contratos/99999999", headers=auth_headers)
        assert response.status_code in [404, 403]


class TestContratosCriar:
    """Testes de criação de contratos"""

    def test_criar_sem_token(self, client):
        """Criar sem token deve retornar 401"""
        response = client.post("/api/contratos", json={
            "beneficiario_id": 1,
            "desconto_percentual": 0.30,
            "data_inicio": "2024-12-01"
        })
        assert response.status_code == 401


class TestContratosAssinar:
    """Testes de assinatura de contrato"""

    def test_assinar_sem_token(self, client):
        """Assinar sem token deve retornar 401"""
        response = client.post("/api/contratos/1/assinar", json={
            "aceite_termos": True
        })
        assert response.status_code == 401
