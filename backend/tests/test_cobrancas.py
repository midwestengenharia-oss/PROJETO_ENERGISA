"""
Testes do módulo Cobranças
"""

import pytest


class TestCobrancasListar:
    """Testes de listagem de cobranças"""

    def test_listar_sem_token(self, client):
        """Acesso sem token deve retornar 401"""
        response = client.get("/api/cobrancas")
        assert response.status_code == 401

    def test_listar_autenticado(self, client, auth_headers):
        """Deve retornar lista de cobranças"""
        if not auth_headers:
            pytest.skip("Sem autenticação")

        response = client.get("/api/cobrancas", headers=auth_headers)
        assert response.status_code in [200, 403]

        if response.status_code == 200:
            data = response.json()
            assert "cobrancas" in data
            assert "total" in data


class TestCobrancasMinhas:
    """Testes de minhas cobranças"""

    def test_minhas_sem_token(self, client):
        """Acesso sem token deve retornar 401"""
        response = client.get("/api/cobrancas/minhas")
        assert response.status_code == 401

    def test_minhas_autenticado(self, client, auth_headers):
        """Deve retornar lista de cobranças do usuário"""
        if not auth_headers:
            pytest.skip("Sem autenticação")

        response = client.get("/api/cobrancas/minhas", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestCobrancasEstatisticas:
    """Testes de estatísticas de cobranças"""

    def test_estatisticas_sem_token(self, client):
        """Acesso sem token deve retornar 401"""
        response = client.get("/api/cobrancas/estatisticas")
        assert response.status_code == 401


class TestCobrancasBuscar:
    """Testes de busca de cobrança"""

    def test_buscar_sem_token(self, client):
        """Buscar sem token deve retornar 401"""
        response = client.get("/api/cobrancas/1")
        assert response.status_code == 401

    def test_buscar_inexistente(self, client, auth_headers):
        """Cobrança inexistente deve retornar 404"""
        if not auth_headers:
            pytest.skip("Sem autenticação")

        response = client.get("/api/cobrancas/99999999", headers=auth_headers)
        assert response.status_code in [404, 403]


class TestCobrancasCriar:
    """Testes de criação de cobranças"""

    def test_criar_sem_token(self, client):
        """Criar sem token deve retornar 401"""
        response = client.post("/api/cobrancas", json={
            "beneficiario_id": 1,
            "valor_energia_injetada": 100.0,
            "desconto_percentual": 0.30,
            "mes_referencia": 11,
            "ano_referencia": 2024,
            "data_vencimento": "2024-12-10"
        })
        assert response.status_code == 401

    def test_criar_dados_invalidos(self, client, auth_headers):
        """Dados inválidos deve retornar 422"""
        if not auth_headers:
            pytest.skip("Sem autenticação")

        response = client.post("/api/cobrancas", headers=auth_headers, json={
            "beneficiario_id": 1
            # Faltam campos obrigatórios
        })
        assert response.status_code in [422, 403]
