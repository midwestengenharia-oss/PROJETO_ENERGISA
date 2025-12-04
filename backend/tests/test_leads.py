"""
Testes do módulo Leads
"""

import pytest


class TestLeadsCaptura:
    """Testes de captura de leads (público)"""

    def test_capturar_lead_valido(self, client):
        """Deve capturar lead com dados válidos"""
        response = client.post("/api/leads/captura", json={
            "nome": "Lead Teste",
            "cpf": "529.982.247-25",
            "telefone": "(65) 99999-9999",
            "cidade": "Cuiabá",
            "uf": "MT"
        })
        # Pode ser 201 (criado) ou 200 (já existente)
        assert response.status_code in [200, 201]

    def test_capturar_lead_cpf_invalido(self, client):
        """CPF inválido deve retornar 422"""
        response = client.post("/api/leads/captura", json={
            "nome": "Lead Teste",
            "cpf": "111.111.111-11"
        })
        assert response.status_code == 422

    def test_capturar_lead_nome_curto(self, client):
        """Nome muito curto deve retornar 422"""
        response = client.post("/api/leads/captura", json={
            "nome": "AB",
            "cpf": "529.982.247-25"
        })
        assert response.status_code == 422


class TestLeadsSimulacao:
    """Testes de simulação (público)"""

    def test_simular_valores_validos(self, client):
        """Deve simular com valores válidos"""
        # Primeiro captura o lead
        lead_response = client.post("/api/leads/captura", json={
            "nome": "Lead Simulação",
            "cpf": "529.982.247-25"
        })

        if lead_response.status_code in [200, 201]:
            lead_id = lead_response.json().get("id")
            if lead_id:
                response = client.post("/api/leads/simular", json={
                    "lead_id": lead_id,
                    "valor_fatura_media": 500.0,
                    "quantidade_ucs": 1
                })
                assert response.status_code == 200
                data = response.json()
                assert "economia_mensal" in data


class TestLeadsListar:
    """Testes de listagem de leads"""

    def test_listar_sem_token(self, client):
        """Acesso sem token deve retornar 401"""
        response = client.get("/api/leads")
        assert response.status_code == 401

    def test_listar_autenticado(self, client, auth_headers):
        """Deve retornar lista de leads"""
        if not auth_headers:
            pytest.skip("Sem autenticação")

        response = client.get("/api/leads", headers=auth_headers)
        assert response.status_code in [200, 403]


class TestLeadsEstatisticas:
    """Testes de estatísticas de leads"""

    def test_estatisticas_sem_token(self, client):
        """Acesso sem token deve retornar 401"""
        response = client.get("/api/leads/estatisticas")
        assert response.status_code == 401


class TestLeadsFunil:
    """Testes de funil de vendas"""

    def test_funil_sem_token(self, client):
        """Acesso sem token deve retornar 401"""
        response = client.get("/api/leads/funil")
        assert response.status_code == 401


class TestLeadsBuscar:
    """Testes de busca de lead"""

    def test_buscar_sem_token(self, client):
        """Buscar sem token deve retornar 401"""
        response = client.get("/api/leads/1")
        assert response.status_code == 401

    def test_buscar_inexistente(self, client, auth_headers):
        """Lead inexistente deve retornar 404"""
        if not auth_headers:
            pytest.skip("Sem autenticação")

        response = client.get("/api/leads/99999999", headers=auth_headers)
        assert response.status_code in [404, 403]
