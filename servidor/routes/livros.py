from flask import Blueprint, request, jsonify
from models import Livro
from auth import requer_autenticacao, requer_perfil
from . import erro_interno

livros_bp = Blueprint("livros", __name__)


@livros_bp.route("/livros", methods=["GET"])
@requer_autenticacao
def listar_livros():
    livros = Livro.listar()
    return jsonify(livros), 200


@livros_bp.route("/livros", methods=["POST"])
@requer_perfil("Administrador", "Bibliotecário")
def criar_livro():
    dados = request.get_json()
    if not dados:
        return jsonify({"erro": "Dados inválidos"}), 400
    try:
        novo_id = Livro.criar(dados)
        return jsonify({"mensagem": "Livro cadastrado com sucesso!", "id": novo_id}), 201
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
    except Exception as e:
        return jsonify(erro_interno(e)), 500


@livros_bp.route("/livros/<int:id>", methods=["PUT"])
@requer_perfil("Administrador", "Bibliotecário")
def atualizar_livro(id):
    dados = request.get_json()
    if not dados:
        return jsonify({"erro": "Dados inválidos"}), 400
    try:
        Livro.atualizar(id, dados)
        return jsonify({"mensagem": "Livro atualizado com sucesso!"}), 200
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
    except Exception as e:
        return jsonify(erro_interno(e)), 500


@livros_bp.route("/livros/<int:id>", methods=["DELETE"])
@requer_perfil("Administrador", "Bibliotecário")
def excluir_livro(id):
    try:
        Livro.excluir(id)
        return jsonify({"mensagem": "Livro excluído com sucesso!"}), 200
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
    except Exception as e:
        return jsonify(erro_interno(e)), 500
