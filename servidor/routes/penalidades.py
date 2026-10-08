from flask import Blueprint, request, jsonify, g
from models import Penalidade
from auth import requer_autenticacao, requer_perfil
from . import erro_interno

penalidades_bp = Blueprint("penalidades", __name__)


@penalidades_bp.route("/penalidades", methods=["GET"])
@requer_autenticacao
def listar_penalidades():
    usuario = g.usuario
    if usuario["perfil"] == "Usuário":
        penalidades = Penalidade.ativas_usuario(usuario["usuario_id"])
        return jsonify(penalidades), 200
    return jsonify(Penalidade.listar()), 200


@penalidades_bp.route("/penalidades/<int:id>/cumprir", methods=["PUT"])
@requer_perfil("Administrador", "Bibliotecário")
def cumprir_penalidade(id):
    try:
        from database import execute
        execute("UPDATE penalidades SET status = 'Cumprida' WHERE id = ?", [id])
        penalidade = Penalidade.listar()
        penalidade = next((p for p in penalidade if p["id"] == id), None)
        if penalidade:
            Penalidade.atualizar_status_usuario(penalidade["usuario_id"])
        return jsonify({"mensagem": "Penalidade marcada como cumprida."}), 200
    except Exception as e:
        return jsonify(erro_interno(e)), 500
