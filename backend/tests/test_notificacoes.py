"""
Testes do módulo Notificações
"""

import pytest


class TestNotificacoesListar:
    """Testes de listagem de notificações"""

    def test_listar_sem_token(self, client):
        """Acesso sem token deve retornar 401"""
        response = client.get("/api/notificacoes")
        assert response.status_code == 401

    def test_listar_autenticado(self, client, auth_headers):
        """Deve retornar lista de notificações"""
        if not auth_headers:
            pytest.skip("Sem autenticação")

        response = client.get("/api/notificacoes", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "notificacoes" in data
        assert "nao_lidas" in data


class TestNotificacoesContador:
    """Testes de contador de notificações"""

    def test_contador_sem_token(self, client):
        """Acesso sem token deve retornar 401"""
        response = client.get("/api/notificacoes/contador")
        assert response.status_code == 401

    def test_contador_autenticado(self, client, auth_headers):
        """Deve retornar contador de não lidas"""
        if not auth_headers:
            pytest.skip("Sem autenticação")

        response = client.get("/api/notificacoes/contador", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "nao_lidas" in data


class TestNotificacoesPreferencias:
    """Testes de preferências de notificação"""

    def test_preferencias_sem_token(self, client):
        """Acesso sem token deve retornar 401"""
        response = client.get("/api/notificacoes/preferencias")
        assert response.status_code == 401

    def test_preferencias_autenticado(self, client, auth_headers):
        """Deve retornar preferências do usuário"""
        if not auth_headers:
            pytest.skip("Sem autenticação")

        response = client.get("/api/notificacoes/preferencias", headers=auth_headers)
        assert response.status_code == 200

    def test_atualizar_preferencias(self, client, auth_headers):
        """Deve atualizar preferências"""
        if not auth_headers:
            pytest.skip("Sem autenticação")

        response = client.put("/api/notificacoes/preferencias", headers=auth_headers, json={
            "email_marketing": False,
            "push_habilitado": True
        })
        assert response.status_code == 200


class TestNotificacoesMarcarLida:
    """Testes de marcar notificação como lida"""

    def test_marcar_todas_lidas_sem_token(self, client):
        """Acesso sem token deve retornar 401"""
        response = client.post("/api/notificacoes/marcar-todas-lidas")
        assert response.status_code == 401

    def test_marcar_todas_lidas_autenticado(self, client, auth_headers):
        """Deve marcar todas como lidas"""
        if not auth_headers:
            pytest.skip("Sem autenticação")

        response = client.post("/api/notificacoes/marcar-todas-lidas", headers=auth_headers)
        assert response.status_code == 200


class TestNotificacoesCriar:
    """Testes de criação de notificação (admin)"""

    def test_criar_sem_token(self, client):
        """Criar sem token deve retornar 401"""
        response = client.post("/api/notificacoes", json={
            "usuario_id": "uuid-teste",
            "titulo": "Teste",
            "mensagem": "Mensagem de teste"
        })
        assert response.status_code == 401
