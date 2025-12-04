"""
Testes do módulo Beneficiários
"""

import pytest


class TestBeneficiariosListar:
    """Testes de listagem de beneficiários"""

    def test_listar_sem_token(self, client):
        """Acesso sem token deve retornar 401"""
        response = client.get("/api/beneficiarios")
        assert response.status_code == 401

    def test_listar_autenticado(self, client, auth_headers):
        """Deve retornar lista ou 403 se não tiver permissão"""
        if not auth_headers:
            pytest.skip("Sem autenticação")

        response = client.get("/api/beneficiarios", headers=auth_headers)
        assert response.status_code in [200, 403]


class TestBeneficiariosMeus:
    """Testes de meus benefícios"""

    def test_meus_sem_token(self, client):
        """Acesso sem token deve retornar 401"""
        response = client.get("/api/beneficiarios/meus")
        assert response.status_code == 401

    def test_meus_autenticado(self, client, auth_headers):
        """Deve retornar lista de benefícios do usuário"""
        if not auth_headers:
            pytest.skip("Sem autenticação")

        response = client.get("/api/beneficiarios/meus", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestBeneficiariosCriar:
    """Testes de criação de beneficiários"""

    def test_criar_sem_token(self, client, beneficiario_data):
        """Criar sem token deve retornar 401"""
        response = client.post("/api/beneficiarios", json=beneficiario_data)
        assert response.status_code == 401

    def test_criar_cpf_invalido(self, client, auth_headers):
        """CPF inválido deve retornar 422"""
        if not auth_headers:
            pytest.skip("Sem autenticação")

        response = client.post("/api/beneficiarios", headers=auth_headers, json={
            "usina_id": 1,
            "uc_id": 1,
            "cpf": "111.111.111-11",
            "percentual_rateio": 25.0,
            "desconto": 0.30
        })
        assert response.status_code == 422

    def test_criar_percentual_invalido(self, client, auth_headers):
        """Percentual > 100 deve retornar 422"""
        if not auth_headers:
            pytest.skip("Sem autenticação")

        response = client.post("/api/beneficiarios", headers=auth_headers, json={
            "usina_id": 1,
            "uc_id": 1,
            "cpf": "529.982.247-25",
            "percentual_rateio": 150.0,  # > 100
            "desconto": 0.30
        })
        assert response.status_code == 422


class TestBeneficiariosBuscar:
    """Testes de busca de beneficiário"""

    def test_buscar_sem_token(self, client):
        """Buscar sem token deve retornar 401"""
        response = client.get("/api/beneficiarios/1")
        assert response.status_code == 401

    def test_buscar_inexistente(self, client, auth_headers):
        """Beneficiário inexistente deve retornar 404"""
        if not auth_headers:
            pytest.skip("Sem autenticação")

        response = client.get("/api/beneficiarios/99999999", headers=auth_headers)
        assert response.status_code == 404


class TestBeneficiariosPorUsina:
    """Testes de beneficiários por usina"""

    def test_por_usina_sem_token(self, client):
        """Acesso sem token deve retornar 401"""
        response = client.get("/api/beneficiarios/usina/1")
        assert response.status_code == 401

    def test_por_usina_autenticado(self, client, auth_headers):
        """Deve retornar lista de beneficiários da usina"""
        if not auth_headers:
            pytest.skip("Sem autenticação")

        response = client.get("/api/beneficiarios/usina/1", headers=auth_headers)
        # Pode ser 200 ou 404 se usina não existir
        assert response.status_code in [200, 404]
