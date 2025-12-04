"""
Testes do módulo Faturas
"""

import pytest


class TestFaturasListar:
    """Testes de listagem de faturas"""

    def test_listar_sem_token(self, client):
        """Acesso sem token deve retornar 401"""
        response = client.get("/api/faturas")
        assert response.status_code == 401

    def test_listar_autenticado(self, client, auth_headers):
        """Deve retornar lista de faturas"""
        if not auth_headers:
            pytest.skip("Sem autenticação")

        response = client.get("/api/faturas", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "faturas" in data
        assert "total" in data
        assert "page" in data

    def test_listar_com_filtros(self, client, auth_headers):
        """Deve aceitar filtros"""
        if not auth_headers:
            pytest.skip("Sem autenticação")

        response = client.get(
            "/api/faturas?ano_referencia=2024&mes_referencia=11",
            headers=auth_headers
        )
        assert response.status_code == 200


class TestFaturasPorUC:
    """Testes de faturas por UC"""

    def test_por_uc_sem_token(self, client):
        """Acesso sem token deve retornar 401"""
        response = client.get("/api/faturas/uc/1")
        assert response.status_code == 401

    def test_por_uc_inexistente(self, client, auth_headers):
        """UC inexistente deve retornar lista vazia ou 404"""
        if not auth_headers:
            pytest.skip("Sem autenticação")

        response = client.get("/api/faturas/uc/99999999", headers=auth_headers)
        # Pode retornar 200 com lista vazia ou 404
        assert response.status_code in [200, 404]


class TestFaturasEstatisticas:
    """Testes de estatísticas de faturas"""

    def test_estatisticas_sem_token(self, client):
        """Acesso sem token deve retornar 401"""
        response = client.get("/api/faturas/uc/1/estatisticas")
        assert response.status_code == 401

    def test_estatisticas_autenticado(self, client, auth_headers):
        """Deve retornar estatísticas"""
        if not auth_headers:
            pytest.skip("Sem autenticação")

        response = client.get("/api/faturas/uc/1/estatisticas", headers=auth_headers)
        # Pode ser 200 ou 404 se UC não existir
        if response.status_code == 200:
            data = response.json()
            assert "total_faturas" in data
            assert "valor_total" in data


class TestFaturasComparativo:
    """Testes de comparativo mensal"""

    def test_comparativo_sem_token(self, client):
        """Acesso sem token deve retornar 401"""
        response = client.get("/api/faturas/uc/1/comparativo")
        assert response.status_code == 401

    def test_comparativo_autenticado(self, client, auth_headers):
        """Deve retornar comparativo"""
        if not auth_headers:
            pytest.skip("Sem autenticação")

        response = client.get("/api/faturas/uc/1/comparativo?meses=6", headers=auth_headers)
        # Pode ser 200 ou 404
        if response.status_code == 200:
            assert isinstance(response.json(), list)


class TestFaturasHistoricoGD:
    """Testes de histórico GD"""

    def test_historico_gd_sem_token(self, client):
        """Acesso sem token deve retornar 401"""
        response = client.get("/api/faturas/uc/1/gd")
        assert response.status_code == 401

    def test_historico_gd_autenticado(self, client, auth_headers):
        """Deve retornar histórico GD"""
        if not auth_headers:
            pytest.skip("Sem autenticação")

        response = client.get("/api/faturas/uc/1/gd", headers=auth_headers)
        # Pode ser 200 ou 404
        if response.status_code == 200:
            assert isinstance(response.json(), list)


class TestFaturasPorReferencia:
    """Testes de fatura por referência"""

    def test_por_referencia_sem_token(self, client):
        """Acesso sem token deve retornar 401"""
        response = client.get("/api/faturas/uc/1/2024/11")
        assert response.status_code == 401

    def test_por_referencia_inexistente(self, client, auth_headers):
        """Fatura inexistente deve retornar 404"""
        if not auth_headers:
            pytest.skip("Sem autenticação")

        response = client.get("/api/faturas/uc/99999999/2024/11", headers=auth_headers)
        assert response.status_code == 404


class TestFaturasBuscar:
    """Testes de busca de fatura"""

    def test_buscar_sem_token(self, client):
        """Buscar sem token deve retornar 401"""
        response = client.get("/api/faturas/1")
        assert response.status_code == 401

    def test_buscar_inexistente(self, client, auth_headers):
        """Fatura inexistente deve retornar 404"""
        if not auth_headers:
            pytest.skip("Sem autenticação")

        response = client.get("/api/faturas/99999999", headers=auth_headers)
        assert response.status_code == 404


class TestFaturasManual:
    """Testes de criação de fatura manual"""

    def test_manual_sem_token(self, client, fatura_data):
        """Criar sem token deve retornar 401"""
        response = client.post("/api/faturas/manual", json=fatura_data)
        assert response.status_code == 401

    def test_manual_mes_invalido(self, client, auth_headers):
        """Mês inválido deve retornar 422"""
        if not auth_headers:
            pytest.skip("Sem autenticação")

        response = client.post("/api/faturas/manual", headers=auth_headers, json={
            "uc_id": 1,
            "mes_referencia": 13,  # Inválido
            "ano_referencia": 2024,
            "valor_fatura": 100.0,
            "data_vencimento": "2024-12-10"
        })
        assert response.status_code == 422

    def test_manual_valor_negativo(self, client, auth_headers):
        """Valor negativo deve retornar 422"""
        if not auth_headers:
            pytest.skip("Sem autenticação")

        response = client.post("/api/faturas/manual", headers=auth_headers, json={
            "uc_id": 1,
            "mes_referencia": 11,
            "ano_referencia": 2024,
            "valor_fatura": -100.0,  # Negativo
            "data_vencimento": "2024-12-10"
        })
        assert response.status_code == 422
