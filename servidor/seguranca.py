"""Controles de segurança: rate limiting, cabeçalhos e validação de origem."""

import os
import re
import secrets
import threading
import time
from collections import deque
from urllib.parse import urlsplit

from flask import request
from werkzeug.security import generate_password_hash

# Hash descartável para igualar o tempo de resposta quando o e-mail não existe.
HASH_FICTICIO = generate_password_hash(secrets.token_hex(16))


def bool_env(nome, padrao=False):
    valor = os.environ.get(nome)
    if valor is None:
        return padrao
    return valor.strip().lower() in ("1", "true", "sim", "yes", "on")


def ip_cliente():
    """IP do cliente.

    Só confia em X-Forwarded-For quando TRUST_PROXY estiver ativo, pois esse
    cabeçalho pode ser forjado pelo próprio cliente.
    """
    if bool_env("TRUST_PROXY"):
        encaminhado = request.headers.get("X-Forwarded-For", "")
        if encaminhado:
            return encaminhado.split(",")[0].strip()
    return request.remote_addr or "desconhecido"


class RateLimiter:
    """Limitador em memória com janela deslizante e bloqueio explícito."""

    def __init__(self, maximo, janela_segundos, nome="limite"):
        self.maximo = int(maximo)
        self.janela = int(janela_segundos)
        self.nome = nome
        self._eventos = {}
        self._bloqueios = {}
        self._lock = threading.Lock()
        self._ultima_limpeza = time.monotonic()

    def _purgar(self, agora):
        if agora - self._ultima_limpeza < min(self.janela, 60):
            return
        self._ultima_limpeza = agora
        for chave in list(self._eventos):
            eventos = self._eventos[chave]
            while eventos and agora - eventos[0] > self.janela:
                eventos.popleft()
            if not eventos:
                del self._eventos[chave]
        for chave, expira in list(self._bloqueios.items()):
            if agora >= expira:
                del self._bloqueios[chave]

    def permitir(self, chave):
        agora = time.monotonic()
        with self._lock:
            self._purgar(agora)

            expira = self._bloqueios.get(chave)
            if expira is not None:
                if agora < expira:
                    return False
                del self._bloqueios[chave]

            eventos = self._eventos.setdefault(chave, deque())
            while eventos and agora - eventos[0] > self.janela:
                eventos.popleft()
            if len(eventos) >= self.maximo:
                return False
            eventos.append(agora)
            return True

    def bloquear(self, chave, segundos=None):
        with self._lock:
            self._bloqueios[chave] = time.monotonic() + (segundos or self.janela)

    def liberar(self, chave):
        with self._lock:
            self._eventos.pop(chave, None)
            self._bloqueios.pop(chave, None)


limite_login = RateLimiter(5, 15 * 60, "login")
limite_login_ip = RateLimiter(60, 15 * 60, "login_ip")
limite_cadastro = RateLimiter(5, 60 * 60, "cadastro")
limite_recuperacao = RateLimiter(5, 60 * 60, "recuperacao")
limite_recuperacao_email = RateLimiter(3, 60 * 60, "recuperacao_email")
limite_busca = RateLimiter(120, 60, "busca")


CSP = (
    "default-src 'self'; "
    "base-uri 'self'; "
    "object-src 'none'; "
    "frame-ancestors 'none'; "
    "form-action 'self'; "
    "img-src 'self' data:; "
    "font-src 'self' data:; "
    "style-src 'self' 'unsafe-inline'; "
    "script-src 'self'; "
    "connect-src 'self'"
)


def requisicao_https():
    if request.is_secure:
        return True
    encaminhado = request.headers.get("X-Forwarded-Proto", "")
    return encaminhado.split(",")[0].strip().lower() == "https"


def aplicar_cabecalhos_seguranca(resposta):
    resposta.headers.setdefault("Content-Security-Policy", CSP)
    resposta.headers.setdefault("X-Content-Type-Options", "nosniff")
    resposta.headers.setdefault("X-Frame-Options", "DENY")
    resposta.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    resposta.headers.setdefault(
        "Permissions-Policy",
        "camera=(), microphone=(), geolocation=(), payment=(), usb=()",
    )
    resposta.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
    resposta.headers.setdefault("Cross-Origin-Resource-Policy", "same-origin")
    resposta.headers.setdefault("X-Permitted-Cross-Domain-Policies", "none")

    if request.path.startswith("/api/"):
        resposta.headers.setdefault("Cache-Control", "no-store")

    if requisicao_https():
        resposta.headers.setdefault(
            "Strict-Transport-Security",
            "max-age=31536000; includeSubDomains",
        )

    return resposta


def validar_origem_requisicao():
    """Bloqueia requisições de escrita vindas de outra origem.

    Requisições sem Origin/Referer (curl, testes, apps nativos) continuam
    permitidas; navegadores enviam Origin em POST/PUT/DELETE.
    """
    if request.method in ("GET", "HEAD", "OPTIONS"):
        return True

    if request.headers.get("Sec-Fetch-Site") == "cross-site":
        return False

    origem = request.headers.get("Origin") or request.headers.get("Referer")
    if not origem:
        return True

    partes = urlsplit(origem)
    if partes.scheme not in ("http", "https"):
        return False
    if partes.netloc == request.host:
        return True

    base = (os.environ.get("APP_BASE_URL") or "").strip()
    if base:
        base_partes = urlsplit(base)
        if base_partes.netloc and partes.netloc == base_partes.netloc:
            return True

    return False


def validar_senha_forte(senha):
    """Retorna None quando a senha é aceitável, ou a mensagem de erro."""
    if not isinstance(senha, str) or not senha:
        return "Informe uma senha."
    if len(senha) < 8:
        return "A senha deve ter pelo menos 8 caracteres."
    if len(senha) > 128:
        return "A senha deve ter no máximo 128 caracteres."
    if not re.search(r"[A-Za-zÀ-ÿ]", senha):
        return "A senha deve conter pelo menos uma letra."
    if not re.search(r"\d", senha):
        return "A senha deve conter pelo menos um número."
    return None
