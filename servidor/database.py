import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
BANCO_DIR = BASE_DIR / "banco"
BANCO_DIR.mkdir(exist_ok=True)

DATABASE = BANCO_DIR / "biblioteca.db"


def conectar():
    conexao = sqlite3.connect(DATABASE)
    conexao.row_factory = sqlite3.Row
    return conexao


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
            setor TEXT NOT NULL,
            tipo_usuario TEXT NOT NULL,
            senha TEXT NOT NULL
        )
    """)

    conexao.commit()
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
    setor,
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
            setor,
            tipo_usuario,
            senha
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            nome,
            cpf,
            data_nascimento,
            email,
            telefone,
            matricula,
            curso,
            setor,
            tipo_usuario,
            senha
        )
    )

    conexao.commit()
    conexao.close()