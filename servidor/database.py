import os
from pathlib import Path
def _load_env():
    p=Path(__file__).resolve().parent.parent / '.env'
    if p.exists():
        for line in p.read_text().splitlines():
            line=line.strip()
            if line and not line.startswith('#') and '=' in line:
                k,v=line.split('=',1)
                os.environ.setdefault(k.strip(), v.strip())
_load_env()
import os
import psycopg
from psycopg.rows import dict_row
from contextlib import contextmanager
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
ESQUEMA = BASE_DIR / "banco" / "esquema.sql"

# Na Vercel o disco é somente leitura (exceto /tmp)
BANCO_DIR = Path("/tmp") if os.environ.get("VERCEL") else BASE_DIR / "banco"
BANCO_DIR.mkdir(exist_ok=True)

DATABASE = BANCO_DIR / "biblioteca.db"


DATABASE_URL = os.environ.get("DATABASE_URL")

class FlexRow(dict):
    def __getitem__(self, key):
        if isinstance(key, int):
            return list(self.values())[key]
        return super().__getitem__(key)

def _flex_row(cursor):
    def make_row(values):
        if cursor.description is None:
            return values
        return FlexRow({desc.name: val for desc, val in zip(cursor.description, values)})
    return make_row

def conectar():
    if not DATABASE_URL:
        raise RuntimeError("Defina DATABASE_URL.")
    return psycopg.connect(DATABASE_URL, row_factory=_flex_row)


# ------------------------------------------------------------
# HELPERS GENÉRICOS (usados por models.py e routes/*)
# ------------------------------------------------------------

def _linha(linha):
    return dict(linha) if linha is not None else None


def query(sql, params=None):
    conexao = conectar()
    try:
        linhas = conexao.execute(sql.replace("?", "%s"), params or []).fetchall()
        return [dict(l) for l in linhas]
    finally:
        conexao.close()


def query_one(sql, params=None):
    conexao = conectar()
    try:
        linha = conexao.execute(sql.replace("?", "%s"), params or []).fetchone()
        return _linha(linha)
    finally:
        conexao.close()


def execute(sql, params=None):
    conexao = conectar()
    try:
        conexao.execute(sql.replace("?", "%s"), params or [])
        conexao.commit()
    finally:
        conexao.close()


def execute_insert(sql, params=None):
    conexao = conectar()
    try:
        cursor = conexao.execute(sql.replace("?", "%s"), params or [])
        if "RETURNING" in sql.upper():
            linha = cursor.fetchone()
            conexao.commit()
            return list(linha.values())[0] if linha else None
        conexao.commit()
        return cursor.lastrowid
    finally:
        conexao.close()


def _executar(conexao, sql, params=None):
    return conexao.execute(sql.replace("?", "%s"), params or [])


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
    pass

def inicializar_banco():
    from pathlib import Path
    esquema = Path(__file__).resolve().parent.parent / 'banco' / 'esquema_postgres.sql'
    try:
        with conectar() as c:
            existe = c.execute("SELECT to_regclass('public.usuarios')").fetchone()
            if existe and list(existe.values())[0] is not None:
                return
            c.execute(esquema.read_text(encoding='utf-8-sig'))
            c.commit()
    except Exception:
        with conectar() as c:
            c.execute(esquema.read_text(encoding='utf-8-sig'))
            c.commit()


def buscar_usuario_por_id(usuario_id):
    conexao = conectar()

    usuario = conexao.execute(
        """
        SELECT *
        FROM usuarios
        WHERE id = %s
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
              AND data_prevista_devolucao::date < CURRENT_DATE
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
                SELECT substr(data_emprestimo::text, 1, 7) AS mes, COUNT(*) AS total
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
                       (CURRENT_DATE - e.data_prevista_devolucao::date)
                FROM emprestimos e
                JOIN usuarios u ON u.id = e.usuario_id
                JOIN livros l ON l.id = e.livro_id
                WHERE e.status = 'Emprestado'
                  AND e.data_prevista_devolucao::date < CURRENT_DATE
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
        WHERE email = %s
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
        WHERE cpf = %s
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
        WHERE matricula = %s
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
    senha,
    perfil="Usuário",
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
            senha,
            perfil
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
            senha,
            perfil
        )
    )

    conexao.commit()
    conexao.close()
