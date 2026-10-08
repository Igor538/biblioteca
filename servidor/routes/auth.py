from flask import Blueprint, request, jsonify, g
from models import Usuario, Sessao, Auditoria, Penalidade
from auth import validar_senha, criar_sessao, obter_usuario_autenticado, requer_autenticacao
from . import erro_interno
import time
from collections import defaultdict

auth_bp = Blueprint("auth", __name__)

# -------------------------------------------------------------
# RATE LIMIT DE LOGIN (proteção contra força bruta)
# -------------------------------------------------------------
# Armazena tentativas falhas por chave (IP + identificador).
# Regras:
#   - máx 5 falhas por chave a cada 15 minutos
#   - bloqueio temporário por 15 minutos após o limite
_TENTATIVAS = defaultdict(list)
_MAX_TENTATIVAS = 5
_JANELA_SEGUNDOS = 15 * 60


def _chave_login(identificador):
    return f"{request.remote_addr}|{identificador}"


def _limpar_falhas(chave):
    _TENTATIVAS.pop(chave, None)


def _registrar_falha(chave):
    agora = time.time()
    lista = _TENTATIVAS[chave]
    lista.append(agora)
    _TENTATIVAS[chave] = [t for t in lista if agora - t <= _JANELA_SEGUNDOS]


def _limpar_tentativas_antigas():
    """Remove chaves sem tentativas recentes para não acumular memória."""
    agora = time.time()
    for chave in list(_TENTATIVAS.keys()):
        lista = [t for t in _TENTATIVAS[chave] if agora - t <= _JANELA_SEGUNDOS]
        if not lista:
            del _TENTATIVAS[chave]
        else:
            _TENTATIVAS[chave] = lista


def _esta_bloqueado(chave):
    _limpar_tentativas_antigas()
    agora = time.time()
    lista = [t for t in _TENTATIVAS.get(chave, []) if agora - t <= _JANELA_SEGUNDOS]
    _TENTATIVAS[chave] = lista
    if len(lista) < _MAX_TENTATIVAS:
        return False
    return True


@auth_bp.route("/api/login", methods=["POST"])
def login():
    dados = request.get_json()
    if not dados:
        return jsonify({"erro": "Dados inválidos"}), 400

    identificador = (dados.get("usuario") or "").strip()
    senha = dados.get("senha") or ""

    if not identificador or not senha:
        return jsonify({"erro": "Informe usuário e senha."}), 400

    chave = _chave_login(identificador)
    if _esta_bloqueado(chave):
        return jsonify({
            "erro": "Muitas tentativas de login. Aguarde 15 minutos e tente novamente."
        }), 429

    usuario = Usuario.buscar_por_email(identificador) \
        or Usuario.buscar_por_prontuario(identificador)

    if not usuario or not validar_senha(senha, usuario.get("senha")):
        _registrar_falha(chave)
        return jsonify({"erro": "Usuário ou senha inválidos!"}), 401

    if usuario["status"] == "Inativo":
        return jsonify({"erro": "Conta inativa. Procure a biblioteca."}), 403

    Penalidade.atualizar_status_usuario(usuario["id"])
    usuario = Usuario.buscar(usuario["id"])

    _limpar_falhas(chave)

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
    Sessao.encerrar(token)
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
