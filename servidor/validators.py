"""Validações de entrada e sanitização de dados."""

import re
from datetime import date


EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
TELEFONE_RE = re.compile(r"^\(?\d{2}\)?\s?9?\d{4}-?\d{4}$")
PRONTUARIO_RE = re.compile(r"^[Cc][Vv]\d{6,8}$")

CATEGORIAS = ["Servidor", "Discente Regular", "Discente FIC", "Terceirizado"]
PERFIS = ["Administrador", "Bibliotecário", "Usuário"]
STATUS_USUARIO = ["Ativo", "Suspenso", "Inativo"]


def validar_isbn(isbn):
    """Validação estrutural de ISBN-10/ISBN-13 (formato, sem dígito verificador)."""
    if not isbn:
        return False
    limpo = re.sub(r"[^0-9Xx]", "", isbn)

    if len(limpo) == 10:
        return limpo[:-1].isdigit() and limpo[-1] in "0123456789Xx"

    if len(limpo) == 13:
        return limpo.isdigit()

    return False


def validar_email(email):
    return bool(EMAIL_RE.match(email or ""))


def validar_telefone(telefone):
    if not telefone:
        return True
    return bool(TELEFONE_RE.match(telefone.strip()))


def validar_prontuario(prontuario):
    if not prontuario:
        return True
    return bool(PRONTUARIO_RE.match(prontuario.strip()))


def validar_categoria(categoria):
    return categoria in CATEGORIAS


def limpar_texto(texto):
    """Sanitiza texto simples (remove tags HTML e espaços repetidos)."""
    if texto is None:
        return None
    texto = re.sub(r"<[^>]+>", "", str(texto))
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto


def limpar_campos(dados, campos):
    """Aplica sanitização de texto nos campos indicados do dicionário."""
    for campo in campos:
        if campo in dados and dados[campo] is not None:
            dados[campo] = limpar_texto(dados[campo])
    return dados


def campos_obrigatorios(dados, campos):
    """Verifica campos obrigatórios preenchidos. Retorna lista de faltantes."""
    faltantes = []
    for campo in campos:
        valor = dados.get(campo)
        if valor is None or (isinstance(valor, str) and not valor.strip()):
            faltantes.append(campo)
    return faltantes


def inteiro(valor, padrao=None):
    try:
        return int(valor)
    except (TypeError, ValueError):
        return padrao


def data_iso(valor):
    """Converte string de data ISO para date."""
    try:
        return date.fromisoformat(str(valor))
    except (TypeError, ValueError):
        return None
