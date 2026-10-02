from flask import Blueprint, request, jsonify
from models import Livro
from auth import requer_autenticacao

busca_bp = Blueprint("busca", __name__)


@busca_bp.route("/busca", methods=["GET"])
@requer_autenticacao
def buscar():
    termo = request.args.get("q", "").strip()
    campo = request.args.get("campo", "").strip() or None

    if not termo:
        return jsonify({"resultados": [], "total": 0}), 200

    resultados = Livro.buscar_avancada(termo, campo)
    return jsonify({"resultados": resultados, "total": len(resultados)}), 200
