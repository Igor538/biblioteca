from flask import Blueprint, request, jsonify
from models import Usuario
from auth import requer_perfil
from validators import CATEGORIAS
from . import erro_interno

usuarios_bp = Blueprint("usuarios", __name__)


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
        Usuario.atualizar(id, dados)
        return jsonify({"mensagem": "Usuário atualizado com sucesso!"}), 200
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
    except Exception as e:
        return jsonify(erro_interno(e)), 500


@usuarios_bp.route("/usuarios/<int:id>", methods=["DELETE"])
@requer_perfil("Administrador")
def excluir_usuario(id):
    try:
        Usuario.excluir(id)
        return jsonify({"mensagem": "Usuário excluído com sucesso!"}), 200
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
    except Exception as e:
        return jsonify(erro_interno(e)), 500
