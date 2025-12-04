"""
Testes do módulo Admin
"""

import pytest


class TestAdminDashboard:
    """Testes do dashboard administrativo"""

    def test_dashboard_stats_sem_token(self, client):
        """Acesso sem token deve retornar 401"""
        response = client.get("/api/admin/dashboard/stats")
        assert response.status_code == 401

    def test_dashboard_stats_autenticado(self, client, auth_headers):
        """Deve retornar estatísticas (se admin)"""
        if not auth_headers:
            pytest.skip("Sem autenticação")

        response = client.get("/api/admin/dashboard/stats", headers=auth_headers)
        # 403 se não for admin, 200 se for
        assert response.status_code in [200, 403]


class TestAdminGrafico:
    """Testes de gráficos do dashboard"""

    def test_grafico_sem_token(self, client):
        """Acesso sem token deve retornar 401"""
        response = client.post("/api/admin/dashboard/grafico", json={
            "tipo": "cobrancas",
            "periodo": "12m"
        })
        assert response.status_code == 401


class TestAdminConfiguracoes:
    """Testes de configurações do sistema"""

    def test_listar_configuracoes_sem_token(self, client):
        """Acesso sem token deve retornar 401"""
        response = client.get("/api/admin/configuracoes")
        assert response.status_code == 401

    def test_listar_configuracoes_autenticado(self, client, auth_headers):
        """Deve retornar lista de configurações (se superadmin)"""
        if not auth_headers:
            pytest.skip("Sem autenticação")

        response = client.get("/api/admin/configuracoes", headers=auth_headers)
        # 403 se não for superadmin
        assert response.status_code in [200, 403]


class TestAdminLogs:
    """Testes de logs de auditoria"""

    def test_logs_sem_token(self, client):
        """Acesso sem token deve retornar 401"""
        response = client.get("/api/admin/logs")
        assert response.status_code == 401

    def test_logs_autenticado(self, client, auth_headers):
        """Deve retornar logs (se superadmin)"""
        if not auth_headers:
            pytest.skip("Sem autenticação")

        response = client.get("/api/admin/logs", headers=auth_headers)
        assert response.status_code in [200, 403]


class TestAdminRelatorios:
    """Testes de relatórios"""

    def test_relatorio_sem_token(self, client):
        """Acesso sem token deve retornar 401"""
        response = client.post("/api/admin/relatorios", json={
            "tipo": "financeiro",
            "data_inicio": "2024-01-01",
            "data_fim": "2024-12-31"
        })
        assert response.status_code == 401


class TestAdminIntegracoes:
    """Testes de verificação de integrações"""

    def test_integracoes_sem_token(self, client):
        """Acesso sem token deve retornar 401"""
        response = client.get("/api/admin/integracoes")
        assert response.status_code == 401

    def test_integracoes_autenticado(self, client, auth_headers):
        """Deve retornar status das integrações (se superadmin)"""
        if not auth_headers:
            pytest.skip("Sem autenticação")

        response = client.get("/api/admin/integracoes", headers=auth_headers)
        assert response.status_code in [200, 403]


class TestAdminHealthDetailed:
    """Testes de health check detalhado"""

    def test_health_detailed_sem_token(self, client):
        """Acesso sem token deve retornar 401"""
        response = client.get("/api/admin/health-detailed")
        assert response.status_code == 401
