from flask import Blueprint, request, jsonify
from models import Livro
from seguranca import ip_cliente, limite_busca

busca_bp = Blueprint("busca", __name__)

MAX_TERMO = 100
MAX_RESULTADOS = 200


@busca_bp.route("/busca", methods=["GET"])
def buscar():
    if not limite_busca.permitir(f"busca:{ip_cliente()}"):
        return jsonify({"erro": "Muitas consultas. Aguarde um instante."}), 429

    termo = (request.args.get("q") or "").strip()[:MAX_TERMO]
    campo = (request.args.get("campo") or "").strip() or None

    if not termo:
        return jsonify({"resultados": [], "total": 0}), 200

    resultados = Livro.buscar_avancada(termo, campo, limite=MAX_RESULTADOS)
    return jsonify({"resultados": resultados, "total": len(resultados)}), 200
