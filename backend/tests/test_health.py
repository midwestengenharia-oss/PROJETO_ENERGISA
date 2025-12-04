"""
Testes de Health Check
"""

import pytest


class TestHealthCheck:
    """Testes do health check"""

    def test_root(self, client):
        """Testa rota raiz"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "online"
        assert "version" in data

    def test_health(self, client):
        """Testa health check"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "services" in data
