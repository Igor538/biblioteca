from flask import Blueprint, request, jsonify, g
from models import ServicoSolicitacao
from auth import requer_autenticacao, requer_perfil
from . import erro_interno

servicos_bp = Blueprint("servicos", __name__)


@servicos_bp.route("/servicos/tipos", methods=["GET"])
@requer_autenticacao
def tipos():
    return jsonify(ServicoSolicitacao.TIPOS), 200


@servicos_bp.route("/servicos", methods=["GET"])
@requer_autenticacao
def listar_servicos():
    usuario = g.usuario
    if usuario["perfil"] == "Usuário":
        solicitacoes = ServicoSolicitacao.listar_usuario(usuario["usuario_id"])
    else:
        solicitacoes = ServicoSolicitacao.listar()
    return jsonify(solicitacoes), 200


@servicos_bp.route("/servicos", methods=["POST"])
@requer_autenticacao
def criar_servico():
    dados = request.get_json()
    if not dados:
        return jsonify({"erro": "Dados inválidos"}), 400

    tipo = dados.get("tipo")
    descricao = dados.get("descricao")
    dados_json = dados.get("dados_json")

    try:
        novo_id = ServicoSolicitacao.criar(
            g.usuario["usuario_id"], tipo, descricao, dados_json
        )
        return jsonify({"mensagem": "Solicitação enviada com sucesso!", "id": novo_id}), 201
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
    except Exception as e:
        return jsonify(erro_interno(e)), 500


@servicos_bp.route("/servicos/<int:id>", methods=["PUT"])
@requer_perfil("Administrador", "Bibliotecário")
def atualizar_servico(id):
    dados = request.get_json()
    if not dados:
        return jsonify({"erro": "Dados inválidos"}), 400
    try:
        ServicoSolicitacao.atualizar_status(
            id, dados.get("status", "Pendente"), dados.get("resposta")
        )
        return jsonify({"mensagem": "Solicitação atualizada com sucesso!"}), 200
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
    except Exception as e:
        return jsonify(erro_interno(e)), 500
