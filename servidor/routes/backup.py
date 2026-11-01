from flask import Blueprint, jsonify
from database import query
from auth import requer_perfil

backup_bp = Blueprint("backup", __name__)

TABELAS = [
    "usuarios", "livros", "emprestimos", "renovacoes", "reservas",
    "penalidades", "notificacoes", "auditoria_logs", "servicos_solicitacoes",
]

# Nunca exporta hash de senha, tokens de sessão ou tokens de recuperação.
COLUNAS_USUARIOS_BACKUP = """
    id, nome, email, telefone, endereco, prontuario, curso, ano_ingresso,
    tipo_usuario, perfil, status, data_cadastro, cpf, data_nascimento, matricula
"""


@backup_bp.route("/backup/exportar", methods=["GET"])
@requer_perfil("Administrador")
def exportar():
    """Backup lógico: exporta as tabelas em formato JSON, sem credenciais."""
    backup = {}
    for tabela in TABELAS:
        if tabela == "usuarios":
            backup[tabela] = query(
                f"SELECT {COLUNAS_USUARIOS_BACKUP} FROM usuarios"
            )
        else:
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
