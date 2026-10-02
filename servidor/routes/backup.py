from flask import Blueprint, jsonify
from database import query
from auth import requer_perfil
import json

backup_bp = Blueprint("backup", __name__)

TABELAS = [
    "usuarios", "livros", "emprestimos", "renovacoes", "reservas",
    "penalidades", "notificacoes", "auditoria_logs", "servicos_solicitacoes",
]


@backup_bp.route("/backup/exportar", methods=["GET"])
@requer_perfil("Administrador")
def exportar():
    """Backup lógico: exporta todas as tabelas em formato JSON."""
    backup = {}
    for tabela in TABELAS:
        backup[tabela] = query(f"SELECT * FROM {tabela}")
    return jsonify({
        "mensagem": "Backup gerado com sucesso.",
        "data": backup
    }), 200


@backup_bp.route("/backup/estatisticas", methods=["GET"])
@requer_perfil("Administrador")
def estatisticas():
    """Resumo das últimas operações para fins de auditoria de backup."""
    resumo = {}
    for tabela in TABELAS:
        from database import query_one
        contagem = query_one(f"SELECT COUNT(*) AS total FROM {tabela}")
        resumo[tabela] = contagem["total"] if contagem else 0
    return jsonify(resumo), 200
