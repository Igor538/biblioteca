from flask import Blueprint, request, jsonify
from database import query, query_one
from auth import requer_perfil, requer_autenticacao

relatorios_bp = Blueprint("relatorios", __name__)


@relatorios_bp.route("/relatorios/livros-mais-emprestados", methods=["GET"])
@requer_perfil("Administrador", "Bibliotecário")
def livros_mais_emprestados():
    limite = request.args.get("limite", default=10, type=int)
    dados = query(
        f"""SELECT l.id, l.titulo, l.autor,
                   COUNT(e.id) AS total_emprestimos
            FROM livros l
            JOIN emprestimos e ON e.livro_id = l.id
            GROUP BY l.id, l.titulo, l.autor
            ORDER BY total_emprestimos DESC
            LIMIT ?""",
        [limite]
    )
    return jsonify(dados), 200


@relatorios_bp.route("/relatorios/livros-atrasados", methods=["GET"])
@requer_perfil("Administrador", "Bibliotecário")
def livros_atrasados():
    dados = query(
        """SELECT e.id, u.nome AS usuario_nome, u.email AS usuario_email, u.telefone,
                  l.titulo AS livro_titulo, e.data_emprestimo, e.data_prevista_devolucao,
                  (CAST(julianday(CURRENT_DATE) - julianday(e.data_prevista_devolucao) AS INTEGER)) AS dias_atraso
           FROM emprestimos e
           JOIN usuarios u ON e.usuario_id = u.id
           JOIN livros l ON e.livro_id = l.id
           WHERE e.status = 'Emprestado' AND e.data_prevista_devolucao < CURRENT_DATE
           ORDER BY dias_atraso DESC"""
    )
    return jsonify(dados), 200


@relatorios_bp.route("/relatorios/usuarios-pendencias", methods=["GET"])
@requer_perfil("Administrador", "Bibliotecário")
def usuarios_pendencias():
    dados = query(
        """SELECT u.id, u.nome, u.email, u.telefone, u.tipo_usuario,
                  (SELECT COUNT(*) FROM emprestimos e
                   WHERE e.usuario_id = u.id AND e.status = 'Emprestado') AS emprestimos_ativos,
                  (SELECT COUNT(*) FROM emprestimos e
                   WHERE e.usuario_id = u.id AND e.status = 'Emprestado'
                     AND e.data_prevista_devolucao < CURRENT_DATE) AS atrasos,
                  (SELECT COUNT(*) FROM penalidades p
                   WHERE p.usuario_id = u.id AND p.status = 'Ativa') AS penalidades_ativas
           FROM usuarios u
           WHERE (SELECT COUNT(*) FROM emprestimos e
                  WHERE e.usuario_id = u.id AND e.status = 'Emprestado') > 0
              OR (SELECT COUNT(*) FROM penalidades p
                  WHERE p.usuario_id = u.id AND p.status = 'Ativa') > 0
           ORDER BY atrasos DESC"""
    )
    return jsonify(dados), 200


@relatorios_bp.route("/relatorios/emprestimos-periodo", methods=["GET"])
@requer_perfil("Administrador", "Bibliotecário")
def emprestimos_periodo():
    inicio = request.args.get("inicio")
    fim = request.args.get("fim")
    where = []
    params = []
    if inicio:
        where.append("e.data_emprestimo >= ?")
        params.append(inicio)
    if fim:
        where.append("e.data_emprestimo <= ?")
        params.append(fim)
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""
    dados = query(
        f"""SELECT e.id, u.nome AS usuario_nome, l.titulo AS livro_titulo,
                   e.data_emprestimo, e.data_prevista_devolucao, e.data_devolucao, e.status
            FROM emprestimos e
            JOIN usuarios u ON e.usuario_id = u.id
            JOIN livros l ON e.livro_id = l.id
            {where_sql}
            ORDER BY e.data_emprestimo DESC""",
        params
    )
    return jsonify(dados), 200


@relatorios_bp.route("/relatorios/devolucoes-periodo", methods=["GET"])
@requer_perfil("Administrador", "Bibliotecário")
def devolucoes_periodo():
    inicio = request.args.get("inicio")
    fim = request.args.get("fim")
    where = ["e.data_devolucao IS NOT NULL"]
    params = []
    if inicio:
        where.append("e.data_devolucao >= ?")
        params.append(inicio)
    if fim:
        where.append("e.data_devolucao <= ?")
        params.append(fim)
    dados = query(
        f"""SELECT e.id, u.nome AS usuario_nome, l.titulo AS livro_titulo,
                   e.data_emprestimo, e.data_prevista_devolucao, e.data_devolucao,
                   max(CAST(julianday(e.data_devolucao) - julianday(e.data_prevista_devolucao) AS INTEGER), 0) AS dias_atraso
            FROM emprestimos e
            JOIN usuarios u ON e.usuario_id = u.id
            JOIN livros l ON e.livro_id = l.id
            WHERE {' AND '.join(where)}
            ORDER BY e.data_devolucao DESC""",
        params
    )
    return jsonify(dados), 200


@relatorios_bp.route("/relatorios/reservas-ativas", methods=["GET"])
@requer_perfil("Administrador", "Bibliotecário")
def reservas_ativas():
    dados = query(
        """SELECT r.id, l.titulo AS livro_titulo, u.nome AS usuario_nome, u.email AS usuario_email,
                  r.data_reserva, r.status
           FROM reservas r
           JOIN livros l ON r.livro_id = l.id
           JOIN usuarios u ON r.usuario_id = u.id
           WHERE r.status = 'Ativa'
           ORDER BY r.data_reserva ASC"""
    )
    return jsonify(dados), 200


@relatorios_bp.route("/relatorios/estatisticas-acervo", methods=["GET"])
@requer_perfil("Administrador", "Bibliotecário")
def estatisticas_acervo():
    dados = query(
        """SELECT l.categoria,
                  COUNT(*) AS total_titulos,
                  COALESCE(SUM(l.quantidade), 0) AS total_exemplares,
                  COALESCE(SUM(l.disponivel), 0) AS disponiveis,
                  COALESCE(SUM(l.quantidade - l.disponivel), 0) AS emprestados
           FROM livros l
           GROUP BY l.categoria
           ORDER BY total_titulos DESC"""
    )
    return jsonify(dados), 200


@relatorios_bp.route("/relatorios/circulacao", methods=["GET"])
@requer_perfil("Administrador", "Bibliotecário")
def circulacao():
    meses = query(
        """SELECT strftime('%Y-%m', data_emprestimo) AS mes,
                  COUNT(*) AS emprestimos,
                  COUNT(data_devolucao) AS devolucoes
           FROM emprestimos
           WHERE data_emprestimo >= date('now','-6 months')
           GROUP BY strftime('%Y-%m', data_emprestimo)
           ORDER BY mes ASC"""
    )
    por_usuario = query(
        """SELECT u.tipo_usuario AS categoria, COUNT(*) AS total
           FROM emprestimos e
           JOIN usuarios u ON e.usuario_id = u.id
           GROUP BY u.tipo_usuario
           ORDER BY total DESC"""
    )
    return jsonify({"por_mes": meses, "por_categoria_usuario": por_usuario}), 200


@relatorios_bp.route("/relatorios/regras-emprestimo", methods=["GET"])
@requer_autenticacao
def regras_emprestimo():
    from models import CATEGORIA_REGRAS, MAX_RENOVACOES
    return jsonify({
        "categorias": [
            {"categoria": nome, "limite_livros": regras["limite"], "prazo_dias": regras["prazo"]}
            for nome, regras in CATEGORIA_REGRAS.items()
        ],
        "max_renovacoes": MAX_RENOVACOES
    }), 200
