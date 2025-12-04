"""
Script de Testes Automatizados - Backend Plataforma GD
Execute: python test_api.py
"""

import requests
import json
import sys
from datetime import date
from typing import Optional

# Configuração
BASE_URL = "http://localhost:8000"
VERBOSE = True

# Cores para output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def log(message: str, color: str = Colors.RESET):
    if VERBOSE:
        print(f"{color}{message}{Colors.RESET}")


def log_success(message: str):
    log(f"✅ {message}", Colors.GREEN)


def log_error(message: str):
    log(f"❌ {message}", Colors.RED)


def log_warning(message: str):
    log(f"⚠️  {message}", Colors.YELLOW)


def log_info(message: str):
    log(f"ℹ️  {message}", Colors.BLUE)


def log_header(message: str):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{message.center(60)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")


class APITester:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.user_id: Optional[str] = None
        self.results = {"passed": 0, "failed": 0, "skipped": 0}

        # Dados de teste
        self.test_email = f"teste_{date.today().strftime('%Y%m%d%H%M%S')}@exemplo.com"
        self.test_password = "Senha123!"
        self.test_cpf = "529.982.247-25"
        self.test_name = "Usuário de Teste"

    def _request(self, method: str, endpoint: str, data: dict = None,
                 auth: bool = True, expected_status: int = None) -> dict:
        """Faz requisição à API"""
        url = f"{self.base_url}{endpoint}"
        headers = {"Content-Type": "application/json"}

        if auth and self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        try:
            if method == "GET":
                response = requests.get(url, headers=headers, params=data)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=data)
            elif method == "PUT":
                response = requests.put(url, headers=headers, json=data)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers)
            else:
                raise ValueError(f"Método não suportado: {method}")

            result = {
                "status": response.status_code,
                "data": response.json() if response.text else {},
                "success": response.status_code < 400
            }

            if expected_status and response.status_code != expected_status:
                result["success"] = False

            return result

        except requests.exceptions.ConnectionError:
            return {"status": 0, "data": {}, "success": False, "error": "Conexão recusada"}
        except Exception as e:
            return {"status": 0, "data": {}, "success": False, "error": str(e)}

    def test(self, name: str, method: str, endpoint: str, data: dict = None,
             auth: bool = True, expected_status: int = 200,
             check_field: str = None) -> bool:
        """Executa um teste"""
        log_info(f"Testando: {name}")

        result = self._request(method, endpoint, data, auth, expected_status)

        if result.get("error"):
            log_error(f"{name}: {result['error']}")
            self.results["failed"] += 1
            return False

        if result["status"] == expected_status:
            if check_field and check_field not in result["data"]:
                log_error(f"{name}: Campo '{check_field}' não encontrado na resposta")
                self.results["failed"] += 1
                return False

            log_success(f"{name} (Status: {result['status']})")
            self.results["passed"] += 1
            return True
        else:
            log_error(f"{name}: Esperado {expected_status}, recebido {result['status']}")
            if VERBOSE and result["data"]:
                log_warning(f"Resposta: {json.dumps(result['data'], indent=2)[:200]}")
            self.results["failed"] += 1
            return False

    # ==================== TESTES ====================

    def test_health(self):
        """Testa health check"""
        log_header("HEALTH CHECK")

        result = self._request("GET", "/health", auth=False)

        if result["success"] and result["data"].get("status") == "healthy":
            log_success("Servidor está saudável")
            if result["data"].get("services", {}).get("supabase") == "connected":
                log_success("Supabase conectado")
            else:
                log_warning("Supabase não conectado")
            return True
        else:
            log_error("Servidor não está respondendo corretamente")
            return False

    def test_auth_module(self):
        """Testa módulo de autenticação"""
        log_header("MÓDULO AUTH")

        # Signup
        signup_result = self._request("POST", "/api/auth/signup", {
            "email": self.test_email,
            "password": self.test_password,
            "nome_completo": self.test_name,
            "cpf": self.test_cpf,
            "telefone": "(65) 99999-9999"
        }, auth=False)

        if signup_result["success"]:
            log_success(f"Signup: Usuário criado ({self.test_email})")
            self.token = signup_result["data"].get("tokens", {}).get("access_token")
            self.refresh_token = signup_result["data"].get("tokens", {}).get("refresh_token")
            self.user_id = signup_result["data"].get("user", {}).get("id")
            self.results["passed"] += 1
        else:
            # Tenta login se usuário já existe
            log_warning("Signup falhou, tentando login...")
            signin_result = self._request("POST", "/api/auth/signin", {
                "email": self.test_email,
                "password": self.test_password
            }, auth=False)

            if signin_result["success"]:
                log_success("Signin: Login realizado")
                self.token = signin_result["data"].get("tokens", {}).get("access_token")
                self.refresh_token = signin_result["data"].get("tokens", {}).get("refresh_token")
                self.user_id = signin_result["data"].get("user", {}).get("id")
                self.results["passed"] += 1
            else:
                log_error("Não foi possível autenticar")
                self.results["failed"] += 1
                return False

        if not self.token:
            log_error("Token não obtido")
            return False

        # Me
        self.test("GET /me", "GET", "/api/auth/me", expected_status=200, check_field="user")

        # Update profile
        self.test("PUT /me", "PUT", "/api/auth/me",
                  data={"nome_completo": "Nome Atualizado"}, expected_status=200)

        # Perfis
        self.test("GET /perfis", "GET", "/api/auth/perfis", expected_status=200)

        # Refresh token
        if self.refresh_token:
            refresh_result = self._request("POST", "/api/auth/refresh",
                                           {"refresh_token": self.refresh_token}, auth=False)
            if refresh_result["success"]:
                log_success("Refresh token: Tokens renovados")
                self.token = refresh_result["data"].get("tokens", {}).get("access_token")
                self.results["passed"] += 1
            else:
                log_warning("Refresh token falhou")
                self.results["skipped"] += 1

        return True

    def test_usuarios_module(self):
        """Testa módulo de usuários"""
        log_header("MÓDULO USUARIOS")

        if not self.token:
            log_warning("Sem token, pulando testes de usuários")
            self.results["skipped"] += 5
            return False

        # Listar (pode falhar se não for admin)
        result = self._request("GET", "/api/usuarios", {"page": 1, "per_page": 10})
        if result["status"] == 200:
            log_success("GET /usuarios: Listagem OK")
            self.results["passed"] += 1
        elif result["status"] == 403:
            log_warning("GET /usuarios: Sem permissão (esperado para usuário comum)")
            self.results["skipped"] += 1
        else:
            log_error(f"GET /usuarios: Status {result['status']}")
            self.results["failed"] += 1

        return True

    def test_ucs_module(self):
        """Testa módulo de UCs"""
        log_header("MÓDULO UCS")

        if not self.token:
            log_warning("Sem token, pulando testes de UCs")
            self.results["skipped"] += 5
            return False

        # Minhas UCs
        self.test("GET /ucs/minhas", "GET", "/api/ucs/minhas", expected_status=200)

        # Listar UCs
        self.test("GET /ucs", "GET", "/api/ucs", data={"page": 1, "per_page": 10}, expected_status=200)

        # Geradoras
        self.test("GET /ucs/geradoras", "GET", "/api/ucs/geradoras", expected_status=200)

        return True

    def test_usinas_module(self):
        """Testa módulo de usinas"""
        log_header("MÓDULO USINAS")

        if not self.token:
            log_warning("Sem token, pulando testes de usinas")
            self.results["skipped"] += 3
            return False

        # Listar
        result = self._request("GET", "/api/usinas", {"page": 1, "per_page": 10})
        if result["status"] == 200:
            log_success("GET /usinas: Listagem OK")
            self.results["passed"] += 1
        elif result["status"] == 403:
            log_warning("GET /usinas: Sem permissão")
            self.results["skipped"] += 1
        else:
            log_error(f"GET /usinas: Status {result['status']}")
            self.results["failed"] += 1

        # Minhas usinas
        self.test("GET /usinas/minhas", "GET", "/api/usinas/minhas", expected_status=200)

        return True

    def test_beneficiarios_module(self):
        """Testa módulo de beneficiários"""
        log_header("MÓDULO BENEFICIÁRIOS")

        if not self.token:
            log_warning("Sem token, pulando testes de beneficiários")
            self.results["skipped"] += 3
            return False

        # Listar (pode precisar de permissão)
        result = self._request("GET", "/api/beneficiarios", {"page": 1, "per_page": 10})
        if result["status"] == 200:
            log_success("GET /beneficiarios: Listagem OK")
            self.results["passed"] += 1
        elif result["status"] == 403:
            log_warning("GET /beneficiarios: Sem permissão")
            self.results["skipped"] += 1
        else:
            log_error(f"GET /beneficiarios: Status {result['status']}")
            self.results["failed"] += 1

        # Meus benefícios
        self.test("GET /beneficiarios/meus", "GET", "/api/beneficiarios/meus", expected_status=200)

        return True

    def test_faturas_module(self):
        """Testa módulo de faturas"""
        log_header("MÓDULO FATURAS")

        if not self.token:
            log_warning("Sem token, pulando testes de faturas")
            self.results["skipped"] += 3
            return False

        # Listar
        self.test("GET /faturas", "GET", "/api/faturas",
                  data={"page": 1, "per_page": 10}, expected_status=200)

        return True

    def test_validation_errors(self):
        """Testa erros de validação"""
        log_header("VALIDAÇÃO DE ERROS")

        # CPF inválido
        result = self._request("POST", "/api/auth/signup", {
            "email": "cpfinvalido@teste.com",
            "password": "Senha123!",
            "nome_completo": "Teste CPF",
            "cpf": "111.111.111-11"
        }, auth=False)

        if result["status"] == 422:
            log_success("CPF inválido: Rejeitado corretamente (422)")
            self.results["passed"] += 1
        else:
            log_error(f"CPF inválido: Esperado 422, recebido {result['status']}")
            self.results["failed"] += 1

        # Token inválido
        old_token = self.token
        self.token = "token_invalido"
        result = self._request("GET", "/api/auth/me")
        self.token = old_token

        if result["status"] == 401:
            log_success("Token inválido: Rejeitado corretamente (401)")
            self.results["passed"] += 1
        else:
            log_error(f"Token inválido: Esperado 401, recebido {result['status']}")
            self.results["failed"] += 1

        # Sem token
        result = self._request("GET", "/api/auth/me", auth=False)
        if result["status"] == 401:
            log_success("Sem token: Rejeitado corretamente (401)")
            self.results["passed"] += 1
        else:
            log_error(f"Sem token: Esperado 401, recebido {result['status']}")
            self.results["failed"] += 1

        return True

    def run_all(self):
        """Executa todos os testes"""
        log_header("INICIANDO TESTES DA API")
        log_info(f"URL Base: {self.base_url}")
        log_info(f"Email de teste: {self.test_email}")

        # Health check primeiro
        if not self.test_health():
            log_error("Servidor não está respondendo. Abortando testes.")
            return False

        # Módulos
        self.test_auth_module()
        self.test_usuarios_module()
        self.test_ucs_module()
        self.test_usinas_module()
        self.test_beneficiarios_module()
        self.test_faturas_module()
        self.test_validation_errors()

        # Resumo
        self.print_summary()

        return self.results["failed"] == 0

    def print_summary(self):
        """Imprime resumo dos testes"""
        log_header("RESUMO DOS TESTES")

        total = self.results["passed"] + self.results["failed"] + self.results["skipped"]

        log_success(f"Passaram:  {self.results['passed']}")
        log_error(f"Falharam:  {self.results['failed']}")
        log_warning(f"Pulados:   {self.results['skipped']}")
        print(f"\n{Colors.BOLD}Total: {total}{Colors.RESET}")

        if self.results["failed"] == 0:
            print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 TODOS OS TESTES PASSARAM!{Colors.RESET}")
        else:
            print(f"\n{Colors.RED}{Colors.BOLD}⚠️  ALGUNS TESTES FALHARAM{Colors.RESET}")


def main():
    """Função principal"""
    import argparse

    parser = argparse.ArgumentParser(description="Testes da API Plataforma GD")
    parser.add_argument("--url", default=BASE_URL, help="URL base da API")
    parser.add_argument("--quiet", action="store_true", help="Modo silencioso")

    args = parser.parse_args()

    global VERBOSE
    VERBOSE = not args.quiet

    tester = APITester(args.url)
    success = tester.run_all()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
