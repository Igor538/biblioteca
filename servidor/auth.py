"""Autenticação, sessões e controle de permissões por perfil."""

import os
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


def _senha_inicial(variavel, rotulo, padrao_dev):
    """Senha inicial da conta de gestão.

    Ordem de precedência:
      1. ADMIN_SENHA/BIB_SENHA, quando definidas;
      2. a senha padrão de desenvolvimento (contas de teste do projeto);
      3. em produção, exige a variável de ambiente.
    """
    senha = os.environ.get(variavel, "").strip()
    if senha:
        return senha, False

    ambiente = (
        os.environ.get("APP_ENV") or os.environ.get("FLASK_ENV") or ""
    ).strip().lower()

    if ambiente in {"producao", "production"}:
        raise RuntimeError(
            f"Defina {variavel} no ambiente antes de criar a conta {rotulo}."
        )

    return padrao_dev, True


def inicializar_administradores():
    """Garante as contas de gestão (idempotente).

    Em desenvolvimento usa as senhas de teste do projeto; em produção exige
    ADMIN_SENHA/BIB_SENHA no ambiente.
    """
    from models import Usuario, Auditoria

    contas = [
        {
            "nome": "Administrador do Sistema",
            "email": os.environ.get("ADMIN_EMAIL", "admin@biblioteca.local"),
            "variavel_senha": "ADMIN_SENHA",
            "senha_padrao": "admin",
            "rotulo": "Administrador",
            "perfil": "Administrador",
            "tipo_usuario": "Servidor",
            "telefone": "(19) 0000-0000",
            "status": "Ativo",
        },
        {
            "nome": "Bibliotecária",
            "email": os.environ.get("BIB_EMAIL", "bibliotecaria@biblioteca.local"),
            "variavel_senha": "BIB_SENHA",
            "senha_padrao": "biblioteca",
            "rotulo": "Bibliotecário",
            "perfil": "Bibliotecário",
            "tipo_usuario": "Servidor",
            "telefone": "(19) 0000-0001",
            "status": "Ativo",
        },
    ]

    for conta in contas:
        existente = Usuario.buscar_por_email(conta["email"])
        if existente:
            continue

        senha, _ = _senha_inicial(
            conta.pop("variavel_senha"),
            conta.pop("rotulo"),
            conta.pop("senha_padrao"),
        )
        conta["senha"] = generate_password_hash(senha, method="scrypt")
        Usuario.criar(conta)
        Auditoria.registrar(
            "Cadastro de Usuário",
            {"nome": conta["nome"], "perfil": conta["perfil"]},
            "Sistema",
        )
