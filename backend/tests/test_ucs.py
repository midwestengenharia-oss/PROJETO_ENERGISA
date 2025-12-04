"""
Testes do módulo UCs
"""

import pytest


class TestUCsListar:
    """Testes de listagem de UCs"""

    def test_listar_sem_token(self, client):
        """Acesso sem token deve retornar 401"""
        response = client.get("/api/ucs")
        assert response.status_code == 401

    def test_listar_autenticado(self, client, auth_headers):
        """Deve retornar lista de UCs"""
        if not auth_headers:
            pytest.skip("Sem autenticação")

        response = client.get("/api/ucs", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "ucs" in data
        assert "total" in data
        assert "page" in data

    def test_listar_com_paginacao(self, client, auth_headers):
        """Deve respeitar parâmetros de paginação"""
        if not auth_headers:
            pytest.skip("Sem autenticação")

        response = client.get("/api/ucs?page=1&per_page=5", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["per_page"] == 5


class TestUCsMinhas:
    """Testes de minhas UCs"""

    def test_minhas_sem_token(self, client):
        """Acesso sem token deve retornar 401"""
        response = client.get("/api/ucs/minhas")
        assert response.status_code == 401

    def test_minhas_autenticado(self, client, auth_headers):
        """Deve retornar UCs do usuário"""
        if not auth_headers:
            pytest.skip("Sem autenticação")

        response = client.get("/api/ucs/minhas", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "ucs" in data


class TestUCsGeradoras:
    """Testes de UCs geradoras"""

    def test_geradoras_autenticado(self, client, auth_headers):
        """Deve retornar lista de geradoras"""
        if not auth_headers:
            pytest.skip("Sem autenticação")

        response = client.get("/api/ucs/geradoras", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestUCsVincular:
    """Testes de vinculação de UCs"""

    def test_vincular_sem_token(self, client, uc_data):
        """Vincular sem token deve retornar 401"""
        response = client.post("/api/ucs/vincular", json=uc_data)
        assert response.status_code == 401

    def test_vincular_formato_invalido(self, client, auth_headers):
        """Formato inválido deve retornar 422"""
        if not auth_headers:
            pytest.skip("Sem autenticação")

        response = client.post("/api/ucs/vincular-formato", headers=auth_headers, json={
            "uc_formatada": "formato-invalido",
            "usuario_titular": True
        })
        assert response.status_code == 422


class TestUCsBuscar:
    """Testes de busca de UC"""

    def test_buscar_inexistente(self, client, auth_headers):
        """UC inexistente deve retornar 404"""
        if not auth_headers:
            pytest.skip("Sem autenticação")

        response = client.get("/api/ucs/99999999", headers=auth_headers)
        assert response.status_code == 404
