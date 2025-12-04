"""
Testes do módulo Auth
"""

import pytest
from datetime import datetime


class TestAuthSignup:
    """Testes de signup"""

    def test_signup_cpf_invalido(self, client):
        """CPF inválido deve retornar 422"""
        response = client.post("/api/auth/signup", json={
            "email": "cpfinvalido@teste.com",
            "password": "Senha123!",
            "nome_completo": "Teste",
            "cpf": "111.111.111-11"
        })
        assert response.status_code == 422

    def test_signup_senha_fraca(self, client):
        """Senha fraca deve retornar 422"""
        response = client.post("/api/auth/signup", json={
            "email": "senhafraca@teste.com",
            "password": "123",
            "nome_completo": "Teste",
            "cpf": "529.982.247-25"
        })
        assert response.status_code == 422

    def test_signup_email_invalido(self, client):
        """Email inválido deve retornar 422"""
        response = client.post("/api/auth/signup", json={
            "email": "email_invalido",
            "password": "Senha123!",
            "nome_completo": "Teste",
            "cpf": "529.982.247-25"
        })
        assert response.status_code == 422


class TestAuthSignin:
    """Testes de signin"""

    def test_signin_sem_credenciais(self, client):
        """Signin sem dados deve retornar 422"""
        response = client.post("/api/auth/signin", json={})
        assert response.status_code == 422

    def test_signin_credenciais_invalidas(self, client):
        """Credenciais inválidas deve retornar 401"""
        response = client.post("/api/auth/signin", json={
            "email": "naoexiste@teste.com",
            "password": "SenhaErrada123!"
        })
        # Pode ser 401 ou outro erro dependendo do Supabase
        assert response.status_code in [401, 400]


class TestAuthMe:
    """Testes do endpoint /me"""

    def test_me_sem_token(self, client):
        """Acesso sem token deve retornar 401"""
        response = client.get("/api/auth/me")
        assert response.status_code == 401

    def test_me_token_invalido(self, client):
        """Token inválido deve retornar 401"""
        response = client.get("/api/auth/me", headers={
            "Authorization": "Bearer token_invalido"
        })
        assert response.status_code == 401

    def test_me_autenticado(self, client, auth_headers):
        """Usuário autenticado deve receber seus dados"""
        if not auth_headers:
            pytest.skip("Sem autenticação")

        response = client.get("/api/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "user" in data
        assert "perfis" in data


class TestAuthPerfis:
    """Testes de perfis"""

    def test_perfis_sem_token(self, client):
        """Acesso sem token deve retornar 401"""
        response = client.get("/api/auth/perfis")
        assert response.status_code == 401

    def test_perfis_autenticado(self, client, auth_headers):
        """Deve retornar lista de perfis"""
        if not auth_headers:
            pytest.skip("Sem autenticação")

        response = client.get("/api/auth/perfis", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "perfis" in data


class TestAuthUpdateProfile:
    """Testes de atualização de perfil"""

    def test_update_nome(self, client, auth_headers):
        """Deve atualizar nome do usuário"""
        if not auth_headers:
            pytest.skip("Sem autenticação")

        novo_nome = f"Nome Pytest {datetime.now().strftime('%H%M%S')}"
        response = client.put("/api/auth/me", headers=auth_headers, json={
            "nome_completo": novo_nome
        })
        assert response.status_code == 200

    def test_update_telefone_invalido(self, client, auth_headers):
        """Telefone inválido deve retornar 422"""
        if not auth_headers:
            pytest.skip("Sem autenticação")

        response = client.put("/api/auth/me", headers=auth_headers, json={
            "telefone": "123"  # Muito curto
        })
        assert response.status_code == 422
