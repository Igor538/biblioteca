from flask import Blueprint, g, request, jsonify
from database import query_one
from models import Usuario
from auth import requer_perfil
from validators import CATEGORIAS
from . import erro_interno

usuarios_bp = Blueprint("usuarios", __name__)


def _alvo(usuario_id):
    usuario = Usuario.buscar(usuario_id)
    if not usuario:
        raise LookupError("Usuário não encontrado.")
    return usuario


def _outros_admins_ativos(usuario_id):
    linha = query_one(
        """SELECT COUNT(*) AS total FROM usuarios
           WHERE perfil = 'Administrador' AND status = 'Ativo' AND id <> ?""",
        [usuario_id],
    )
    return linha["total"] if linha else 0


def _autor_atual():
    return g.usuario


@usuarios_bp.route("/usuarios", methods=["GET"])
@requer_perfil("Administrador", "Bibliotecário")
def listar_usuarios():
    usuarios = Usuario.listar()
    return jsonify(usuarios), 200


@usuarios_bp.route("/usuarios/categorias", methods=["GET"])
@requer_perfil("Administrador", "Bibliotecário")
def categorias():
    return jsonify(CATEGORIAS), 200


@usuarios_bp.route("/usuarios", methods=["POST"])
@requer_perfil("Administrador", "Bibliotecário")
def criar_usuario():
    dados = request.get_json()
    if not dados:
        return jsonify({"erro": "Dados inválidos"}), 400

    autor = _autor_atual()

    # Bibliotecário só pode criar leitores ativos.
    if autor["perfil"] != "Administrador":
        if dados.get("perfil") not in (None, "", "Usuário"):
            return jsonify({
                "erro": "Somente administradores podem criar perfis de gestão."
            }), 403
        if dados.get("status") not in (None, "", "Ativo"):
            return jsonify({
                "erro": "Somente administradores podem definir o status inicial da conta."
            }), 403
        dados["perfil"] = "Usuário"
        dados["status"] = "Ativo"

    try:
        novo_id = Usuario.criar(dados)
        return jsonify({"mensagem": "Usuário cadastrado com sucesso!", "id": novo_id}), 201
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
    except Exception as e:
        return jsonify(erro_interno(e)), 500


@usuarios_bp.route("/usuarios/<int:id>", methods=["PUT"])
@requer_perfil("Administrador", "Bibliotecário")
def atualizar_usuario(id):
    dados = request.get_json()
    if not dados:
        return jsonify({"erro": "Dados inválidos"}), 400

    try:
        alvo = _alvo(id)
    except LookupError as e:
        return jsonify({"erro": str(e)}), 404

    autor = _autor_atual()

    if autor["perfil"] != "Administrador":
        if alvo["perfil"] == "Administrador":
            return jsonify({
                "erro": "Somente administradores podem alterar outro administrador."
            }), 403
        if "perfil" in dados and dados["perfil"] != alvo["perfil"]:
            return jsonify({
                "erro": "Somente administradores podem alterar perfis de acesso."
            }), 403
        dados.pop("perfil", None)

    if alvo["perfil"] == "Administrador":
        remove_admin = (
            dados.get("perfil") not in (None, "Administrador")
            or dados.get("status") not in (None, "Ativo")
        )
        if remove_admin and _outros_admins_ativos(id) == 0:
            return jsonify({
                "erro": "O sistema precisa de pelo menos um administrador ativo."
            }), 400

    try:
        Usuario.atualizar(id, dados)
        return jsonify({"mensagem": "Usuário atualizado com sucesso!"}), 200
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
    except Exception as e:
        return jsonify(erro_interno(e)), 500


@usuarios_bp.route("/usuarios/<int:id>", methods=["DELETE"])
@requer_perfil("Administrador")
def excluir_usuario(id):
    autor = _autor_atual()

    if autor["usuario_id"] == id:
        return jsonify({"erro": "Você não pode excluir a própria conta."}), 400

    try:
        alvo = _alvo(id)
    except LookupError as e:
        return jsonify({"erro": str(e)}), 404

    if alvo["perfil"] == "Administrador" and _outros_admins_ativos(id) == 0:
        return jsonify({
            "erro": "O sistema precisa de pelo menos um administrador ativo."
        }), 400

    try:
        Usuario.excluir(id)
        return jsonify({"mensagem": "Usuário excluído com sucesso!"}), 200
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
    except Exception as e:
        return jsonify(erro_interno(e)), 500
