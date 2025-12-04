"""
Testes do módulo Usinas
"""

import pytest


class TestUsinasListar:
    """Testes de listagem de usinas"""

    def test_listar_sem_token(self, client):
        """Acesso sem token deve retornar 401"""
        response = client.get("/api/usinas")
        assert response.status_code == 401

    def test_listar_autenticado(self, client, auth_headers):
        """Deve retornar lista de usinas ou 403 se não tiver permissão"""
        if not auth_headers:
            pytest.skip("Sem autenticação")

        response = client.get("/api/usinas", headers=auth_headers)
        # Pode ser 200 (tem permissão) ou 403 (não tem)
        assert response.status_code in [200, 403]

        if response.status_code == 200:
            data = response.json()
            assert "usinas" in data
            assert "total" in data


class TestUsinasMinhas:
    """Testes de minhas usinas"""

    def test_minhas_sem_token(self, client):
        """Acesso sem token deve retornar 401"""
        response = client.get("/api/usinas/minhas")
        assert response.status_code == 401

    def test_minhas_autenticado(self, client, auth_headers):
        """Deve retornar lista de usinas do gestor"""
        if not auth_headers:
            pytest.skip("Sem autenticação")

        response = client.get("/api/usinas/minhas", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestUsinasCriar:
    """Testes de criação de usinas"""

    def test_criar_sem_token(self, client, usina_data):
        """Criar sem token deve retornar 401"""
        response = client.post("/api/usinas", json=usina_data)
        assert response.status_code == 401

    def test_criar_dados_invalidos(self, client, auth_headers):
        """Dados inválidos deve retornar 422"""
        if not auth_headers:
            pytest.skip("Sem autenticação")

        response = client.post("/api/usinas", headers=auth_headers, json={
            "nome": "A"  # Nome muito curto
        })
        assert response.status_code == 422


class TestUsinasBuscar:
    """Testes de busca de usina"""

    def test_buscar_sem_token(self, client):
        """Buscar sem token deve retornar 401"""
        response = client.get("/api/usinas/1")
        assert response.status_code == 401

    def test_buscar_inexistente(self, client, auth_headers):
        """Usina inexistente deve retornar 404"""
        if not auth_headers:
            pytest.skip("Sem autenticação")

        response = client.get("/api/usinas/99999999", headers=auth_headers)
        assert response.status_code == 404


class TestUsinasGestores:
    """Testes de gestores de usinas"""

    def test_listar_gestores_inexistente(self, client, auth_headers):
        """Gestores de usina inexistente deve retornar 404"""
        if not auth_headers:
            pytest.skip("Sem autenticação")

        response = client.get("/api/usinas/99999999/gestores", headers=auth_headers)
        assert response.status_code == 404
