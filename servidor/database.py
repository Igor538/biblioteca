import sqlite3
from contextlib import contextmanager
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
BANCO_DIR = BASE_DIR / "banco"
BANCO_DIR.mkdir(exist_ok=True)

DATABASE = BANCO_DIR / "biblioteca.db"


def conectar():
    conexao = sqlite3.connect(DATABASE)
    conexao.row_factory = sqlite3.Row
    return conexao


# ------------------------------------------------------------
# HELPERS GENÉRICOS (usados por models.py e routes/*)
# ------------------------------------------------------------

def _linha(linha):
    return dict(linha) if linha is not None else None


def query(sql, params=None):
    conexao = conectar()
    try:
        linhas = conexao.execute(sql, params or []).fetchall()
        return [dict(l) for l in linhas]
    finally:
        conexao.close()


def query_one(sql, params=None):
    conexao = conectar()
    try:
        linha = conexao.execute(sql, params or []).fetchone()
        return _linha(linha)
    finally:
        conexao.close()


def execute(sql, params=None):
    conexao = conectar()
    try:
        conexao.execute(sql, params or [])
        conexao.commit()
    finally:
        conexao.close()


def execute_insert(sql, params=None):
    conexao = conectar()
    try:
        cursor = conexao.execute(sql, params or [])
        conexao.commit()
        if "RETURNING" in sql.upper():
            linha = cursor.fetchone()
            return linha[0] if linha else None
        return cursor.lastrowid
    finally:
        conexao.close()


def _executar(conexao, sql, params=None):
    return conexao.execute(sql, params or [])


@contextmanager
def transacao():
    conexao = conectar()
    try:
        yield conexao
        conexao.commit()
    except Exception:
        conexao.rollback()
        raise
    finally:
        conexao.close()


def criar_tabela_usuarios():
    conexao = conectar()

    conexao.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            cpf TEXT NOT NULL UNIQUE,
            data_nascimento TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            telefone TEXT NOT NULL,
            matricula TEXT NOT NULL UNIQUE,
            curso TEXT NOT NULL,
            tipo_usuario TEXT NOT NULL,
            senha TEXT NOT NULL
        )
    """)

    conexao.commit()
    conexao.close()


def buscar_usuario_por_id(usuario_id):
    conexao = conectar()

    usuario = conexao.execute(
        """
        SELECT *
        FROM usuarios
        WHERE id = ?
        """,
        (usuario_id,)
    ).fetchone()

    conexao.close()

    return usuario


def dados_dashboard():
    conexao = conectar()

    try:
        total_livros = conexao.execute(
            "SELECT COUNT(*) FROM livros"
        ).fetchone()[0]

        total_usuarios = conexao.execute(
            "SELECT COUNT(*) FROM usuarios"
        ).fetchone()[0]

        emprestimos_ativos = conexao.execute(
            "SELECT COUNT(*) FROM emprestimos WHERE status = 'Emprestado'"
        ).fetchone()[0]

        livros_atrasados = conexao.execute(
            """
            SELECT COUNT(*)
            FROM emprestimos
            WHERE status = 'Emprestado'
              AND data_prevista_devolucao < date('now', 'localtime')
            """
        ).fetchone()[0]

        reservas_ativas = conexao.execute(
            "SELECT COUNT(*) FROM reservas WHERE status = 'Ativa'"
        ).fetchone()[0]

        devolucoes_realizadas = conexao.execute(
            "SELECT COUNT(*) FROM emprestimos WHERE status = 'Devolvido'"
        ).fetchone()[0]

        livros_disponiveis = conexao.execute(
            "SELECT COALESCE(SUM(disponivel), 0) FROM livros"
        ).fetchone()[0]

        livros_indisponiveis = conexao.execute(
            "SELECT COUNT(*) FROM livros WHERE disponivel <= 0"
        ).fetchone()[0]

        usuarios_suspensos = conexao.execute(
            "SELECT COUNT(*) FROM usuarios WHERE status = 'Suspenso'"
        ).fetchone()[0]

        emprestimos_mes = [
            {"mes": linha[0], "total": linha[1]}
            for linha in conexao.execute(
                """
                SELECT substr(data_emprestimo, 1, 7) AS mes, COUNT(*) AS total
                FROM emprestimos
                GROUP BY mes
                ORDER BY mes
                """
            ).fetchall()
        ]

        livros_mais_emprestados = [
            {"titulo": linha[0], "total": linha[1]}
            for linha in conexao.execute(
                """
                SELECT l.titulo, COUNT(*) AS total
                FROM emprestimos e
                JOIN livros l ON l.id = e.livro_id
                GROUP BY l.id
                ORDER BY total DESC
                LIMIT 5
                """
            ).fetchall()
        ]

        acervo_categoria = [
            {"categoria": linha[0], "total": linha[1]}
            for linha in conexao.execute(
                """
                SELECT COALESCE(categoria, 'Sem categoria'), COUNT(*)
                FROM livros
                GROUP BY categoria
                ORDER BY COUNT(*) DESC
                """
            ).fetchall()
        ]

        emprestimos_categoria = [
            {"categoria": linha[0], "total": linha[1]}
            for linha in conexao.execute(
                """
                SELECT COALESCE(l.categoria, 'Sem categoria'), COUNT(*)
                FROM emprestimos e
                JOIN livros l ON l.id = e.livro_id
                GROUP BY l.categoria
                ORDER BY COUNT(*) DESC
                """
            ).fetchall()
        ]

        ultimos_emprestimos = [
            {
                "usuario_nome": linha[0],
                "livro_titulo": linha[1],
                "data_emprestimo": linha[2],
                "data_prevista_devolucao": linha[3],
                "status": linha[4],
            }
            for linha in conexao.execute(
                """
                SELECT u.nome, l.titulo, e.data_emprestimo,
                       e.data_prevista_devolucao, e.status
                FROM emprestimos e
                JOIN usuarios u ON u.id = e.usuario_id
                JOIN livros l ON l.id = e.livro_id
                ORDER BY e.data_emprestimo DESC, e.id DESC
                LIMIT 8
                """
            ).fetchall()
        ]

        livros_atrasados_lista = [
            {
                "livro_titulo": linha[0],
                "usuario_nome": linha[1],
                "dias_atraso": linha[2],
            }
            for linha in conexao.execute(
                """
                SELECT l.titulo, u.nome,
                       CAST(julianday('now', 'localtime')
                            - julianday(e.data_prevista_devolucao) AS INTEGER)
                FROM emprestimos e
                JOIN usuarios u ON u.id = e.usuario_id
                JOIN livros l ON l.id = e.livro_id
                WHERE e.status = 'Emprestado'
                  AND e.data_prevista_devolucao < date('now', 'localtime')
                ORDER BY 3 DESC
                LIMIT 8
                """
            ).fetchall()
        ]

        return {
            "totalLivros": total_livros,
            "totalUsuarios": total_usuarios,
            "emprestimosAtivos": emprestimos_ativos,
            "livrosAtrasados": livros_atrasados,
            "reservasAtivas": reservas_ativas,
            "devolucoesRealizadas": devolucoes_realizadas,
            "livrosDisponiveis": livros_disponiveis,
            "livrosIndisponiveis": livros_indisponiveis,
            "usuariosSuspensos": usuarios_suspensos,
            "emprestimosMes": emprestimos_mes,
            "livrosMaisEmprestados": livros_mais_emprestados,
            "acervoCategoria": acervo_categoria,
            "emprestimosCategoria": emprestimos_categoria,
            "ultimosEmprestimos": ultimos_emprestimos,
            "livrosAtrasadosLista": livros_atrasados_lista,
        }
    finally:
        conexao.close()


def buscar_usuario_por_email(email):
    conexao = conectar()

    usuario = conexao.execute(
        """
        SELECT *
        FROM usuarios
        WHERE email = ?
        """,
        (email,)
    ).fetchone()

    conexao.close()

    return usuario


def buscar_usuario_por_cpf(cpf):
    conexao = conectar()

    usuario = conexao.execute(
        """
        SELECT *
        FROM usuarios
        WHERE cpf = ?
        """,
        (cpf,)
    ).fetchone()

    conexao.close()

    return usuario


def buscar_usuario_por_matricula(matricula):
    conexao = conectar()

    usuario = conexao.execute(
        """
        SELECT *
        FROM usuarios
        WHERE matricula = ?
        """,
        (matricula,)
    ).fetchone()

    conexao.close()

    return usuario


def cadastrar_usuario(
    nome,
    cpf,
    data_nascimento,
    email,
    telefone,
    matricula,
    curso,
    tipo_usuario,
    senha
):
    conexao = conectar()

    conexao.execute(
        """
        INSERT INTO usuarios (
            nome,
            cpf,
            data_nascimento,
            email,
            telefone,
            matricula,
            curso,
            tipo_usuario,
            senha
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            nome,
            cpf,
            data_nascimento,
            email,
            telefone,
            matricula,
            curso,
            tipo_usuario,
            senha
        )
    )

    conexao.commit()
    conexao.close()