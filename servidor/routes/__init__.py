"""Helpers compartilhados das rotas da API."""

import logging

log = logging.getLogger("biblioteca")


def erro_interno(e):
    """Registra a exceção internamente e retorna mensagem genérica,
    sem vazar detalhes do sistema para o cliente."""
    log.exception("Erro interno não tratado: %s", e)
    return {"erro": "Erro interno do servidor. Tente novamente mais tarde."}
