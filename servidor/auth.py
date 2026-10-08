"""Autenticação, sessões e controle de permissões por perfil."""

import secrets
import functools
from flask import request, jsonify, g
from werkzeug.security import check_password_hash, generate_password_hash

from models import Sessao, Auditoria


def gerar_token():
    return secrets.token_hex(32)


def validar_senha(senha, hash_senha):
    if not hash_senha:
        return False
    return check_password_hash(hash_senha, senha)


def criar_sessao(usuario):
    token = gerar_token()
    Sessao.criar(usuario["id"], token)
    return token


def obter_usuario_autenticado():
    """Extrai o usuário da requisição.

    Aceita tanto o token Bearer (sessão da tabela `sessoes`)
    quanto a sessão Flask (login tradicional via formulário).
    """
    token = request.headers.get("Authorization", "")
    if token.startswith("Bearer "):
        token = token[7:]
    if token:
        sessao = Sessao.buscar_por_token(token)
        if sessao:
            return sessao

    from flask import session as flask_session
    usuario_id = flask_session.get("usuario_id")
    if usuario_id:
        from models import Usuario
        usuario = Usuario.buscar(usuario_id)
        if usuario and usuario.get("status") != "Inativo":
            return {
                "usuario_id": usuario["id"],
                "nome": usuario["nome"],
                "email": usuario["email"],
                "perfil": usuario["perfil"],
                "tipo_usuario": usuario["tipo_usuario"],
                "status": usuario["status"],
            }

    return None


def requer_autenticacao(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        usuario = obter_usuario_autenticado()
        if not usuario:
            return jsonify({"erro": "Não autenticado. Faça login para continuar."}), 401
        g.usuario = usuario
        return f(*args, **kwargs)
    return wrapper


def requer_perfil(*perfis):
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            usuario = obter_usuario_autenticado()
            if not usuario:
                return jsonify({"erro": "Não autenticado. Faça login para continuar."}), 401
            if usuario["perfil"] not in perfis:
                return jsonify({"erro": "Acesso negado. Seu perfil não possui permissão para esta operação."}), 403
            g.usuario = usuario
            return f(*args, **kwargs)
        return wrapper
    return decorator


def responsavel_atual():
    usuario = getattr(g, "usuario", None)
    return usuario["nome"] if usuario else "Sistema"


def registrar_auditoria(operacao, dados=None):
    Auditoria.registrar(operacao, dados, responsavel=responsavel_atual())


def inicializar_administradores():
    """Garante contas padrão de acesso (idempotente)."""
    from models import Usuario, Auditoria

    contas = [
        {
            "nome": "Administrador do Sistema",
            "email": "admin@biblioteca.local",
            "senha": "admin",
            "perfil": "Administrador",
            "tipo_usuario": "Servidor",
            "telefone": "(19) 0000-0000",
            "status": "Ativo",
        },
        {
            "nome": "Bibliotecária",
            "email": "bibliotecaria@biblioteca.local",
            "senha": "biblioteca",
            "perfil": "Bibliotecário",
            "tipo_usuario": "Servidor",
            "telefone": "(19) 0000-0001",
            "status": "Ativo",
        },
    ]

    for conta in contas:
        existente = Usuario.buscar_por_email(conta["email"])
        if not existente:
            conta["senha"] = generate_password_hash(conta["senha"])
            Usuario.criar(conta)
            Auditoria.registrar("Cadastro de Usuário", {"nome": conta["nome"], "perfil": conta["perfil"]}, "Sistema")
