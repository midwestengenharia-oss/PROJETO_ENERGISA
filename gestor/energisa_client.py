import requests
import os

class EnergisaGatewayClient:
    def __init__(self, base_url=os.getenv("GATEWAY_URL", "http://localhost:3000")):
        self.base_url = base_url
        self.token = None
        # Credenciais fixas para comunicação interna
        self.client_id = "7966649d-d20a-4129-afbd-341f51aa74d6" 
        self.client_secret = os.getenv("CRM_SECRET", "cnOOJJCg8VK3W11xOo6vhaHd4RNTP-ALT06#cs#I")

    def authenticate(self):
        try:
            resp = requests.post(f"{self.base_url}/api/token", json={
                "client_id": self.client_id,
                "client_secret": self.client_secret
            })
            if resp.status_code == 200:
                self.token = resp.json()["access_token"]
                return True
            print(f"Falha autenticação Gateway: {resp.text}")
            return False
        except Exception as e:
            print(f"Erro conexão Gateway: {e}")
            return False

    def _get_headers(self):
        if not self.token:
            self.authenticate()
        return {"Authorization": f"Bearer {self.token}"}

    def start_login(self, cpf, final_tel):
        """Inicia o login pedindo SMS"""
        resp = requests.post(
            f"{self.base_url}/auth/login/start",
            json={"cpf": cpf, "final_telefone": final_tel},
            headers=self._get_headers()
        )
        return resp.json()

    def finish_login(self, cpf, transaction_id, sms_code):
        """Finaliza o login com o código SMS"""
        resp = requests.post(
            f"{self.base_url}/auth/login/finish",
            json={"cpf": cpf, "transaction_id": transaction_id, "sms_code": sms_code},
            headers=self._get_headers()
        )
        return resp.json()

    def list_ucs(self, cpf):
        """Lista todas as UCs vinculadas ao CPF"""
        resp = requests.post(
            f"{self.base_url}/ucs",
            json={"cpf": cpf},
            headers=self._get_headers()
        )
        return resp.json()

    def list_faturas(self, cpf, uc_data):
        """Lista as faturas de uma UC específica"""
        # uc_data deve ter: cdc, codigoEmpresaWeb, digitoVerificadorCdc (ou digitoVerificador)
        payload = {
            "cpf": cpf,
            "cdc": uc_data['cdc'],
            "codigoEmpresaWeb": uc_data['empresa_web'],
            # O Gateway espera digitoVerificadorCdc
            "digitoVerificadorCdc": uc_data.get('digitoVerificadorCdc') or uc_data.get('digitoVerificador')
        }
        resp = requests.post(
            f"{self.base_url}/faturas/listar",
            json=payload,
            headers=self._get_headers()
        )
        if resp.status_code == 200:
            return resp.json()
        return [] # Retorna lista vazia em caso de erro para não quebrar o loop

    def download_fatura(self, cpf, uc_data, fatura_data):
        """Baixa o PDF da fatura"""
        payload = {
            "cpf": cpf,
            "cdc": uc_data['cdc'],
            "codigoEmpresaWeb": uc_data['empresa_web'],
            "digitoVerificadorCdc": uc_data.get('digitoVerificadorCdc') or uc_data.get('digitoVerificador'),
            "ano": fatura_data['ano'],
            "mes": fatura_data['mes'],
            "numeroFatura": fatura_data['numeroFatura']
        }
        resp = requests.post(
            f"{self.base_url}/faturas/pdf",
            json=payload,
            headers=self._get_headers()
        )
        if resp.status_code == 200:
            return resp.json()
        return None

    def get_gd_info(self, cpf, uc_data):
        """Busca detalhes da Usina (Saldo, Beneficiárias)"""
        payload = {
            "cpf": cpf,
            "cdc": uc_data['cdc'],
            "codigoEmpresaWeb": uc_data['empresa_web'],
            # Importante: O Gateway espera 'digitoVerificadorCdc' no objeto UcRequest
            "digitoVerificadorCdc": uc_data.get('digitoVerificadorCdc') or uc_data.get('digitoVerificador')
        }
        resp = requests.post(
            f"{self.base_url}/gd/info",
            json=payload,
            headers=self._get_headers()
        )
        if resp.status_code == 200:
            return resp.json()
        return None