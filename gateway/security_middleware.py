"""
Middleware de Segurança para Energisa Gateway
Implementa múltiplas camadas de proteção contra ataques
"""
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime, timedelta
from typing import Dict, List, Set
import hashlib
import secrets
import logging
from collections import defaultdict
import time

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("security")


class SecurityManager:
    """Gerenciador centralizado de segurança"""

    def __init__(self):
        # Rate limiting por IP
        self.ip_requests: Dict[str, List[float]] = defaultdict(list)

        # IPs bloqueados (manual ou automático)
        self.blocked_ips: Set[str] = set()

        # Tentativas de autenticação por IP
        self.auth_attempts: Dict[str, List[float]] = defaultdict(list)

        # Session IDs válidos (com expiração)
        self.valid_sessions: Dict[str, dict] = {}

        # CSRF Tokens (para rotas públicas)
        self.csrf_tokens: Dict[str, dict] = {}

        # Fingerprints de dispositivos suspeitos
        self.suspicious_fingerprints: Set[str] = set()

    def check_rate_limit(self, ip: str, endpoint: str, max_requests: int = 10, window_seconds: int = 60) -> bool:
        """
        Verifica se o IP excedeu o rate limit

        Args:
            ip: Endereço IP
            endpoint: Nome do endpoint
            max_requests: Máximo de requisições permitidas
            window_seconds: Janela de tempo em segundos

        Returns:
            True se permitido, False se bloqueado
        """
        now = time.time()
        key = f"{ip}:{endpoint}"

        # Remove requisições antigas
        self.ip_requests[key] = [
            req_time for req_time in self.ip_requests[key]
            if now - req_time < window_seconds
        ]

        # Verifica se excedeu o limite
        if len(self.ip_requests[key]) >= max_requests:
            logger.warning(f"Rate limit exceeded for IP {ip} on endpoint {endpoint}")
            return False

        # Adiciona requisição atual
        self.ip_requests[key].append(now)
        return True

    def is_ip_blocked(self, ip: str) -> bool:
        """Verifica se IP está bloqueado"""
        return ip in self.blocked_ips

    def block_ip(self, ip: str, reason: str = "Manual"):
        """Bloqueia um IP"""
        self.blocked_ips.add(ip)
        logger.warning(f"IP {ip} bloqueado. Razão: {reason}")

    def unblock_ip(self, ip: str):
        """Desbloqueia um IP"""
        self.blocked_ips.discard(ip)
        logger.info(f"IP {ip} desbloqueado")

    def check_auth_attempts(self, ip: str, max_attempts: int = 5, window_minutes: int = 15) -> bool:
        """
        Verifica tentativas de autenticação falhadas
        Bloqueia IP após muitas tentativas
        """
        now = time.time()
        window_seconds = window_minutes * 60

        # Limpa tentativas antigas
        self.auth_attempts[ip] = [
            attempt_time for attempt_time in self.auth_attempts[ip]
            if now - attempt_time < window_seconds
        ]

        # Verifica se excedeu tentativas
        if len(self.auth_attempts[ip]) >= max_attempts:
            self.block_ip(ip, f"Excesso de tentativas de autenticação ({max_attempts} em {window_minutes} min)")
            return False

        return True

    def register_auth_failure(self, ip: str):
        """Registra falha de autenticação"""
        self.auth_attempts[ip].append(time.time())
        logger.warning(f"Falha de autenticação do IP {ip}")

    def create_session(self, ip: str, cpf: str, expires_minutes: int = 30) -> str:
        """
        Cria session ID seguro vinculado ao IP

        Returns:
            Session ID criptograficamente seguro
        """
        # Gera ID aleatório + vincula ao IP + CPF
        random_part = secrets.token_urlsafe(32)
        session_data = f"{random_part}:{ip}:{cpf}:{time.time()}"
        session_id = hashlib.sha256(session_data.encode()).hexdigest()

        expires_at = datetime.utcnow() + timedelta(minutes=expires_minutes)

        self.valid_sessions[session_id] = {
            "ip": ip,
            "cpf": cpf,
            "created_at": datetime.utcnow(),
            "expires_at": expires_at,
            "requests_count": 0
        }

        logger.info(f"Session criada: {session_id[:16]}... para IP {ip}")
        return session_id

    def validate_session(self, session_id: str, ip: str) -> bool:
        """
        Valida se session é válida e pertence ao IP correto
        """
        # Limpa sessões expiradas periodicamente
        self._cleanup_expired_sessions()

        if session_id not in self.valid_sessions:
            logger.warning(f"Tentativa de uso de session inválida: {session_id[:16]}... do IP {ip}")
            return False

        session = self.valid_sessions[session_id]

        # Verifica expiração
        if datetime.utcnow() > session["expires_at"]:
            logger.warning(f"Session expirada: {session_id[:16]}...")
            del self.valid_sessions[session_id]
            return False

        # Verifica se o IP bate (proteção contra session hijacking)
        if session["ip"] != ip:
            logger.error(f"⚠️ ALERTA DE SEGURANÇA: Tentativa de session hijacking! Session do IP {session['ip']} usada por {ip}")
            # Invalida a sessão imediatamente
            del self.valid_sessions[session_id]
            self.block_ip(ip, "Tentativa de session hijacking")
            return False

        # Incrementa contador de requisições
        session["requests_count"] += 1

        # Se muitas requisições, pode ser abuso
        if session["requests_count"] > 100:
            logger.warning(f"Session {session_id[:16]}... com {session['requests_count']} requisições")

        return True

    def invalidate_session(self, session_id: str):
        """Invalida uma sessão"""
        if session_id in self.valid_sessions:
            del self.valid_sessions[session_id]
            logger.info(f"Session invalidada: {session_id[:16]}...")

    def _cleanup_expired_sessions(self):
        """Remove sessões expiradas (executa periodicamente)"""
        now = datetime.utcnow()
        expired = [
            sid for sid, session in self.valid_sessions.items()
            if now > session["expires_at"]
        ]

        for sid in expired:
            del self.valid_sessions[sid]

        if expired:
            logger.info(f"Limpeza: {len(expired)} sessões expiradas removidas")

    def create_csrf_token(self, ip: str, expires_minutes: int = 10) -> str:
        """
        Cria token CSRF para validação de formulários
        Token vinculado ao IP do cliente
        """
        random_part = secrets.token_urlsafe(24)
        token_data = f"{random_part}:{ip}:{time.time()}"
        csrf_token = hashlib.sha256(token_data.encode()).hexdigest()

        expires_at = datetime.utcnow() + timedelta(minutes=expires_minutes)

        self.csrf_tokens[csrf_token] = {
            "ip": ip,
            "created_at": datetime.utcnow(),
            "expires_at": expires_at,
            "used": False
        }

        return csrf_token

    def validate_csrf_token(self, token: str, ip: str, consume: bool = True) -> bool:
        """
        Valida token CSRF

        Args:
            token: Token CSRF
            ip: IP do cliente
            consume: Se True, marca token como usado (one-time use)
        """
        if token not in self.csrf_tokens:
            logger.warning(f"Token CSRF inválido do IP {ip}")
            return False

        csrf = self.csrf_tokens[token]

        # Verifica expiração
        if datetime.utcnow() > csrf["expires_at"]:
            logger.warning(f"Token CSRF expirado do IP {ip}")
            del self.csrf_tokens[token]
            return False

        # Verifica se já foi usado (proteção contra replay)
        if csrf["used"]:
            logger.warning(f"Tentativa de reusar token CSRF do IP {ip}")
            return False

        # Verifica se IP bate
        if csrf["ip"] != ip:
            logger.error(f"⚠️ Token CSRF do IP {csrf['ip']} usado por {ip}")
            return False

        # Marca como usado se necessário
        if consume:
            csrf["used"] = True

        return True

    def get_client_fingerprint(self, request: Request) -> str:
        """
        Cria fingerprint do cliente baseado em headers
        Usado para detectar comportamento suspeito
        """
        user_agent = request.headers.get("user-agent", "")
        accept_language = request.headers.get("accept-language", "")
        accept_encoding = request.headers.get("accept-encoding", "")

        fingerprint_data = f"{user_agent}:{accept_language}:{accept_encoding}"
        return hashlib.md5(fingerprint_data.encode()).hexdigest()

    def is_suspicious_request(self, request: Request) -> bool:
        """
        Detecta requisições suspeitas baseado em heurísticas
        """
        user_agent = request.headers.get("user-agent", "").lower()

        # Lista de bots/scanners conhecidos
        suspicious_agents = [
            "bot", "crawler", "spider", "scraper", "curl", "wget",
            "python-requests", "postman", "insomnia", "burp", "sqlmap",
            "nikto", "nmap", "masscan", "zap"
        ]

        for agent in suspicious_agents:
            if agent in user_agent:
                logger.warning(f"User-Agent suspeito detectado: {user_agent}")
                return True

        # Requisições sem User-Agent
        if not user_agent:
            logger.warning("Requisição sem User-Agent")
            return True

        # Verifica fingerprint
        fingerprint = self.get_client_fingerprint(request)
        if fingerprint in self.suspicious_fingerprints:
            logger.warning(f"Fingerprint suspeito: {fingerprint}")
            return True

        return False

    def log_request(self, request: Request, ip: str, status_code: int = 200):
        """Registra requisição para auditoria"""
        logger.info(
            f"[AUDIT] {request.method} {request.url.path} | "
            f"IP: {ip} | Status: {status_code} | "
            f"UA: {request.headers.get('user-agent', 'N/A')[:50]}"
        )


# Instância global do gerenciador de segurança
security_manager = SecurityManager()


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Middleware que aplica verificações de segurança em todas as requisições
    """

    async def dispatch(self, request: Request, call_next):
        # Pega IP real (considerando proxies como Coolify/Nginx)
        ip = self._get_real_ip(request)

        # 1. Verifica se IP está bloqueado
        if security_manager.is_ip_blocked(ip):
            logger.error(f"Requisição bloqueada de IP banido: {ip}")
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "Acesso bloqueado"}
            )

        # 2. Detecta requisições suspeitas
        if security_manager.is_suspicious_request(request):
            # Não bloqueia imediatamente, mas registra
            logger.warning(f"Requisição suspeita de {ip} para {request.url.path}")

        # 3. Rate limiting para rotas públicas
        if request.url.path.startswith("/public/"):
            if not security_manager.check_rate_limit(ip, request.url.path, max_requests=20, window_seconds=60):
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={"detail": "Muitas requisições. Tente novamente em alguns segundos."}
                )

        # Executa a requisição
        response = await call_next(request)

        # Log de auditoria
        security_manager.log_request(request, ip, response.status_code)

        # Adiciona headers de segurança
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        return response

    def _get_real_ip(self, request: Request) -> str:
        """
        Obtém IP real do cliente, considerando proxies reversos
        """
        # Coolify/Nginx geralmente usa X-Forwarded-For ou X-Real-IP
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Pega o primeiro IP da lista (cliente original)
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fallback para IP direto
        if request.client:
            return request.client.host

        return "unknown"
