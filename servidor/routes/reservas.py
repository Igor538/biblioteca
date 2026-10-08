from flask import Blueprint, request, jsonify, g
from models import Reserva
from auth import requer_autenticacao, requer_perfil
from . import erro_interno

reservas_bp = Blueprint("reservas", __name__)


@reservas_bp.route("/reservas", methods=["GET"])
@requer_autenticacao
def listar_reservas():
    usuario = g.usuario
    if usuario["perfil"] == "Usuário":
        reservas = Reserva.listar_usuario(usuario["usuario_id"])
    else:
        reservas = Reserva.listar()
    return jsonify(reservas), 200


@reservas_bp.route("/reservas", methods=["POST"])
@requer_autenticacao
def criar_reserva():
    dados = request.get_json()
    if not dados:
        return jsonify({"erro": "Dados inválidos"}), 400

    usuario_id = g.usuario["usuario_id"]
    livro_id = dados.get("livro_id")

    if not livro_id:
        return jsonify({"erro": "Selecione um livro."}), 400

    try:
        nova_id = Reserva.criar(int(livro_id), usuario_id)
        return jsonify({"mensagem": "Reserva realizada com sucesso!", "id": nova_id}), 201
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
    except Exception as e:
        return jsonify(erro_interno(e)), 500


@reservas_bp.route("/reservas/<int:id>", methods=["DELETE"])
@requer_autenticacao
def cancelar_reserva(id):
    usuario = g.usuario
    usuario_id = usuario["usuario_id"] if usuario["perfil"] == "Usuário" else None
    try:
        Reserva.cancelar(id, usuario_id)
        return jsonify({"mensagem": "Reserva cancelada com sucesso!"}), 200
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
    except Exception as e:
        return jsonify(erro_interno(e)), 500
