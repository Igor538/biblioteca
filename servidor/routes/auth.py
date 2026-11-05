import os
from flask import Blueprint, request, jsonify, g, session
from datetime import datetime, timedelta
from werkzeug.security import check_password_hash
from models import Usuario, Sessao, Auditoria, Penalidade, TokenRecuperacao
from auth import validar_senha, criar_sessao, obter_usuario_autenticado, requer_autenticacao, gerar_token
import email_service
import validators as vd
from . import erro_interno
from seguranca import (
    HASH_FICTICIO,
    ip_cliente,
    limite_login as limite_login_compartilhado,
    limite_login_ip,
    limite_recuperacao,
    limite_recuperacao_email,
    validar_senha_forte,
)

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/api/login", methods=["POST"])
def login():
    dados = request.get_json(silent=True) or {}

    identificador = (dados.get("usuario") or "").strip().lower()
    senha = dados.get("senha") or ""

    if not identificador or not senha:
        return jsonify({"erro": "Informe usuário e senha."}), 400

    ip = ip_cliente()
    chave = f"api|{ip}|{identificador}"

    if not limite_login_ip.permitir(f"api-ip:{ip}"):
        return jsonify({
            "erro": "Muitas tentativas de login. Aguarde 15 minutos e tente novamente."
        }), 429

    if not limite_login_compartilhado.permitir(chave):
        return jsonify({
            "erro": "Muitas tentativas de login. Aguarde 15 minutos e tente novamente."
        }), 429

    usuario = Usuario.buscar_por_email(identificador) \
        or Usuario.buscar_por_prontuario(identificador)

    if not usuario:
        check_password_hash(HASH_FICTICIO, senha)
        return jsonify({"erro": "Usuário ou senha inválidos!"}), 401

    if not usuario.get("senha") or not validar_senha(senha, usuario.get("senha")):
        return jsonify({"erro": "Usuário ou senha inválidos!"}), 401

    if usuario["status"] == "Inativo":
        return jsonify({"erro": "Conta inativa. Procure a biblioteca."}), 403

    Penalidade.atualizar_status_usuario(usuario["id"])
    usuario = Usuario.buscar(usuario["id"])

    limite_login_compartilhado.liberar(chave)

    token = criar_sessao(usuario)
    Auditoria.registrar("Login no sistema", {"usuario": usuario["nome"]}, usuario["nome"])

    return jsonify({
        "token": token,
        "usuario": {
            "id": usuario["id"],
            "nome": usuario["nome"],
            "email": usuario["email"],
            "perfil": usuario["perfil"],
            "tipo_usuario": usuario["tipo_usuario"],
            "status": usuario["status"],
        }
    }), 200


@auth_bp.route("/api/logout", methods=["POST"])
@requer_autenticacao
def logout():
    token = (request.headers.get("Authorization") or "").replace("Bearer ", "")
    if token:
        Sessao.encerrar(token)
    session.clear()
    return jsonify({"mensagem": "Sessão encerrada."}), 200


@auth_bp.route("/api/sessao", methods=["GET"])
def sessao():
    usuario = obter_usuario_autenticado()
    if not usuario:
        return jsonify({"autenticado": False}), 200
    return jsonify({
        "autenticado": True,
        "usuario": {
            "id": usuario["usuario_id"],
            "nome": usuario["nome"],
            "email": usuario["email"],
            "perfil": usuario["perfil"],
            "tipo_usuario": usuario["tipo_usuario"],
            "status": usuario["status"],
        }
    }), 200


@auth_bp.route("/api/meus-dados", methods=["GET"])
@requer_autenticacao
def meus_dados():
    usuario = Usuario.buscar(g.usuario["usuario_id"])
    if not usuario:
        return jsonify({"erro": "Usuário não encontrado."}), 404
    usuario.pop("senha", None)
    usuario["limite_livros"] = Usuario.regras_categoria(usuario["tipo_usuario"])["limite"]
    usuario["prazo_dias"] = Usuario.regras_categoria(usuario["tipo_usuario"])["prazo"]
    usuario["penalidades"] = Penalidade.ativas_usuario(usuario["id"])
    return jsonify(usuario), 200


@auth_bp.route("/api/meus-dados", methods=["PUT"])
@requer_autenticacao
def atualizar_meus_dados():
    dados = request.get_json()
    if not dados:
        return jsonify({"erro": "Dados inválidos"}), 400

    permitidos = ["nome", "email", "telefone", "endereco", "curso"]
    filtrados = {k: v for k, v in dados.items() if k in permitidos}
    if not filtrados:
        return jsonify({"erro": "Nenhum dado permitido enviado."}), 400

    filtrados = vd.limpar_campos(filtrados, permitidos)

    if "nome" in filtrados and len(filtrados["nome"] or "") < 3:
        return jsonify({"erro": "Informe seu nome completo."}), 400

    if "email" in filtrados:
        filtrados["email"] = (filtrados["email"] or "").lower()
        if not vd.validar_email(filtrados["email"]):
            return jsonify({"erro": "E-mail inválido."}), 400

    if "telefone" in filtrados and not vd.validar_telefone(filtrados["telefone"]):
        return jsonify({"erro": "Telefone inválido."}), 400

    try:
        Usuario.atualizar(g.usuario["usuario_id"], filtrados)
        Auditoria.registrar(
            "Alteração de dados próprios",
            {"usuario_id": g.usuario["usuario_id"], "campos": list(filtrados.keys())},
            g.usuario["nome"]
        )
        return jsonify({"mensagem": "Dados atualizados com sucesso!"}), 200
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
    except Exception as e:
        return jsonify(erro_interno(e)), 500

@auth_bp.route('/api/esqueceu-senha', methods=['POST'])
@auth_bp.route('/api/recuperar-senha', methods=['POST'])
def esqueceu_senha():
    dados = request.get_json(silent=True) or {}
    email = (dados.get('email') or '').strip().lower()
    if not email:
        return jsonify({'erro': 'Informe o e-mail.'}), 400

    ip = ip_cliente()
    if not limite_recuperacao.permitir(f"recuperacao:{ip}"):
        return jsonify({
            'erro': 'Muitas solicitações. Aguarde alguns minutos e tente novamente.'
        }), 429

    if not limite_recuperacao_email.permitir(f"recuperacao-email:{email}"):
        return jsonify({
            'erro': 'Muitas solicitações para este e-mail. Aguarde alguns minutos.'
        }), 429

    usuario = Usuario.buscar_por_email(email)
    mensagem_padrao = 'Se o e-mail estiver cadastrado, enviaremos instrucoes para redefinir a senha.'
    if not usuario:
        return jsonify({'mensagem': mensagem_padrao}), 200

    try:
        token = TokenRecuperacao.criar(
            usuario['id'],
            gerar_token(),
            datetime.now() + timedelta(hours=TokenRecuperacao.EXPIRACAO_HORAS)
        )
        base_url = os.environ.get("APP_BASE_URL") or request.host_url
        link = f"{base_url.rstrip('/')}/recuperar-senha?token={token}"
        texto, html = email_service.montar_email_recuperacao(
            usuario.get('nome'), link, TokenRecuperacao.EXPIRACAO_HORAS
        )
        email_service.enviar_email(
            usuario['email'],
            "Redefinição de senha - Biblioteca Digital",
            texto,
            html
        )

        resposta = {'mensagem': mensagem_padrao}
        # O link so aparece na tela se a variavel MOSTRAR_LINK_RECUPERACAO
        # estiver ativa (uso apenas em desenvolvimento). Desligado por padrao:
        # o usuario deve receber a mensagem por e-mail.
        if os.environ.get('MOSTRAR_LINK_RECUPERACAO', '').lower() in ('1', 'true', 'sim'):
            resposta['link_redefinicao'] = link
        return jsonify(resposta), 200
    except Exception as e:
        return jsonify(erro_interno(e)), 500


@auth_bp.route('/api/redefinir-senha', methods=['POST'])
def redefinir_senha():
    dados = request.get_json(silent=True) or {}
    token = (dados.get('token') or '').strip()
    senha = dados.get('senha') or ""
    if not token:
        return jsonify({'erro': 'Token invalido ou expirado.'}), 400
    erro_senha = validar_senha_forte(senha)
    if erro_senha:
        return jsonify({'erro': erro_senha}), 400
    token_rec = TokenRecuperacao.buscar_valido(token)
    if not token_rec:
        return jsonify({'erro': 'Token invalido ou expirado.'}), 400
    try:
        Usuario.alterar_senha(token_rec['usuario_id'], senha)
        TokenRecuperacao.marcar_usado(token)
    except Exception as e:
        return jsonify(erro_interno(e)), 500
    return jsonify({'mensagem': 'Senha redefinida com sucesso! Faca login com a nova senha.'}), 200
