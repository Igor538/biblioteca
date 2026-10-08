from flask import Blueprint, request, jsonify
from models import Auditoria
from auth import requer_perfil

auditoria_bp = Blueprint("auditoria", __name__)


@auditoria_bp.route("/auditoria", methods=["GET"])
@requer_perfil("Administrador")
def listar_auditoria():
    inicio = request.args.get("inicio")
    fim = request.args.get("fim")
    operacao = request.args.get("operacao")
    limite = request.args.get("limite", default=None, type=int)

    dados = Auditoria.buscar_por_periodo(inicio, fim, operacao)
    if limite:
        dados = dados[:limite]
    return jsonify(dados), 200
