import os
import queue
import threading
from pathlib import Path


def _load_env():
    p = Path(__file__).resolve().parent.parent / '.env'
    if p.exists():
        for line in p.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                os.environ.setdefault(k.strip(), v.strip())


_load_env()

import psycopg
from contextlib import contextmanager

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


# ------------------------------------------------------------
# POOL DE CONEXOES
#
# Abrir uma conexao no Neon custa ~1s. Antes, cada consulta abria e
# fechava uma conexao nova. Agora as conexoes sao reaproveitadas em um
# pool: "close()" apenas devolve a conexao para o pool.
# ------------------------------------------------------------

_pool = queue.LifoQueue()
_PERMISSOES = threading.Semaphore(int(os.environ.get("DB_POOL_SIZE", "5")))


class _ConexaoPool:
    def __init__(self, conexao):
        self._conexao = conexao
        self._liberada = False

    def __getattr__(self, nome):
        return getattr(self._conexao, nome)

    @property
    def closed(self):
        return self._conexao.closed

    def close(self):
        if self._liberada:
            return
        self._liberada = True
        if self._conexao.closed:
            _PERMISSOES.release()
            return
        _pool.put_nowait(self)
        _PERMISSOES.release()

    def __enter__(self):
        return self

    def __exit__(self, tipo, valor, traceback):
        return self._conexao.__exit__(tipo, valor, traceback)


def _nova_conexao():
    return psycopg.connect(DATABASE_URL, row_factory=_flex_row, autocommit=True)


def conectar():
    if not DATABASE_URL:
        raise RuntimeError("Defina DATABASE_URL.")
    _PERMISSOES.acquire()
    try:
        conexao = _pool.get_nowait()
        if conexao.closed:
            conexao = _ConexaoPool(_nova_conexao())
    except queue.Empty:
        conexao = _ConexaoPool(_nova_conexao())
    conexao._liberada = False
    return conexao


# ------------------------------------------------------------
# HELPERS GENERICOS (usados por models.py e routes/*)
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
    finally:
        conexao.close()


def execute_insert(sql, params=None):
    conexao = conectar()
    try:
        cursor = conexao.execute(sql.replace("?", "%s"), params or [])
        if "RETURNING" in sql.upper():
            linha = cursor.fetchone()
            return list(linha.values())[0] if linha else None
        return cursor.lastrowid
    finally:
        conexao.close()


def _executar(conexao, sql, params=None):
    return conexao.execute(sql.replace("?", "%s"), params or [])


@contextmanager
def transacao():
    conexao = conectar()
    real = conexao._conexao
    real.autocommit = False
    try:
        yield conexao
        real.commit()
    except Exception:
        real.rollback()
        raise
    finally:
        try:
            real.autocommit = True
        except Exception:
            pass
        conexao.close()


TOKEN_TABELA_SQL = """
CREATE TABLE IF NOT EXISTS tokens_recuperacao (
    token VARCHAR(64) PRIMARY KEY,
    usuario_id INTEGER NOT NULL,
    data_expiracao TIMESTAMP NOT NULL,
    usado BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT fk_tokens_recuperacao_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
)
"""


def inicializar_banco():
    esquema = Path(__file__).resolve().parent.parent / 'banco' / 'esquema_postgres.sql'
    try:
        conexao = conectar()
        try:
            existe = conexao.execute("SELECT to_regclass('public.usuarios')").fetchone()
            if not (existe and list(existe.values())[0] is not None):
                conexao.execute(esquema.read_text(encoding='utf-8-sig'))
            conexao.execute(TOKEN_TABELA_SQL)
        finally:
            conexao.close()
    except Exception:
        conexao = conectar()
        try:
            conexao.execute(esquema.read_text(encoding='utf-8-sig'))
        finally:
            conexao.close()


def buscar_usuario_por_id(usuario_id):
    conexao = conectar()
    try:
        return conexao.execute(
            "SELECT * FROM usuarios WHERE id = %s",
            (usuario_id,)
        ).fetchone()
    finally:
        conexao.close()


def dados_dashboard():
    conexao = conectar()
    try:
        totais = conexao.execute(
            """
            SELECT
                (SELECT COUNT(*) FROM livros) AS total_livros,
                (SELECT COUNT(*) FROM usuarios) AS total_usuarios,
                (SELECT COUNT(*) FROM emprestimos WHERE status = 'Emprestado') AS emprestimos_ativos,
                (SELECT COUNT(*) FROM emprestimos
                  WHERE status = 'Emprestado'
                    AND data_prevista_devolucao::date < CURRENT_DATE) AS livros_atrasados,
                (SELECT COUNT(*) FROM reservas WHERE status = 'Ativa') AS reservas_ativas,
                (SELECT COUNT(*) FROM emprestimos WHERE status = 'Devolvido') AS devolucoes_realizadas,
                (SELECT COALESCE(SUM(disponivel), 0) FROM livros) AS livros_disponiveis,
                (SELECT COUNT(*) FROM livros WHERE disponivel <= 0) AS livros_indisponiveis,
                (SELECT COUNT(*) FROM usuarios WHERE status = 'Suspenso') AS usuarios_suspensos
            """
        ).fetchone()

        total_livros = totais["total_livros"]
        total_usuarios = totais["total_usuarios"]
        emprestimos_ativos = totais["emprestimos_ativos"]
        livros_atrasados = totais["livros_atrasados"]
        reservas_ativas = totais["reservas_ativas"]
        devolucoes_realizadas = totais["devolucoes_realizadas"]
        livros_disponiveis = totais["livros_disponiveis"]
        livros_indisponiveis = totais["livros_indisponiveis"]
        usuarios_suspensos = totais["usuarios_suspensos"]

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
    try:
        return conexao.execute(
            "SELECT * FROM usuarios WHERE email = %s",
            (email,)
        ).fetchone()
    finally:
        conexao.close()


def buscar_usuario_por_cpf(cpf):
    conexao = conectar()
    try:
        return conexao.execute(
            "SELECT * FROM usuarios WHERE cpf = %s",
            (cpf,)
        ).fetchone()
    finally:
        conexao.close()


def buscar_usuario_por_matricula(matricula):
    conexao = conectar()
    try:
        return conexao.execute(
            "SELECT * FROM usuarios WHERE matricula = %s",
            (matricula,)
        ).fetchone()
    finally:
        conexao.close()


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
    try:
        conexao.execute(
            """
            INSERT INTO usuarios (
                nome, cpf, data_nascimento, email, telefone,
                matricula, curso, tipo_usuario, senha, perfil
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                nome, cpf, data_nascimento, email, telefone,
                matricula, curso, tipo_usuario, senha, perfil
            )
        )
    finally:
        conexao.close()
