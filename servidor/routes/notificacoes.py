from flask import Blueprint, request, jsonify, g
from models import Notificacao
from auth import requer_autenticacao

notificacoes_bp = Blueprint("notificacoes", __name__)


@notificacoes_bp.route("/notificacoes", methods=["GET"])
@requer_autenticacao
def listar_notificacoes():
    notificacoes = Notificacao.listar_usuario(g.usuario["usuario_id"])
    nao_lidas = Notificacao.nao_lidas(g.usuario["usuario_id"])
    return jsonify({"notificacoes": notificacoes, "nao_lidas": nao_lidas}), 200


@notificacoes_bp.route("/notificacoes/nao-lidas", methods=["GET"])
@requer_autenticacao
def contagem_nao_lidas():
    return jsonify({"nao_lidas": Notificacao.nao_lidas(g.usuario["usuario_id"])}), 200


@notificacoes_bp.route("/notificacoes/<int:id>/lida", methods=["PUT"])
@requer_autenticacao
def marcar_lida(id):
    Notificacao.marcar_lida(id, g.usuario["usuario_id"])
    return jsonify({"mensagem": "Notificação marcada como lida."}), 200


@notificacoes_bp.route("/notificacoes/ler-todas", methods=["PUT"])
@requer_autenticacao
def marcar_todas_lidas():
    Notificacao.marcar_todas_lidas(g.usuario["usuario_id"])
    return jsonify({"mensagem": "Todas as notificações foram marcadas como lidas."}), 200
