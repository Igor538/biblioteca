"""Modelos CRUD e regras de negócio do sistema de biblioteca."""

import json
from datetime import date, timedelta
from database import query, query_one, execute, execute_insert, transacao, _executar
from werkzeug.security import generate_password_hash
import validators as vd


# ============================================================
# REGRAS DE EMPRÉSTIMO POR CATEGORIA
# ============================================================
CATEGORIA_REGRAS = {
    "Servidor":        {"limite": 8, "prazo": 21},
    "Discente Regular": {"limite": 6, "prazo": 7},
    "Discente FIC":     {"limite": 2, "prazo": 7},
    "Terceirizado":     {"limite": 2, "prazo": 7},
}

MAX_RENOVACOES = 3

COLUNAS_USUARIO = [
    "nome", "email", "telefone", "endereco", "prontuario", "curso",
    "ano_ingresso", "tipo_usuario", "perfil", "senha", "status"
]

# Colunas seguras para consulta pública (nunca inclui o hash de senha)
CAMPOS_PUBLICOS_USUARIO = [
    "u.id", "u.nome", "u.email", "u.telefone", "u.endereco", "u.prontuario",
    "u.curso", "u.ano_ingresso", "u.tipo_usuario", "u.perfil", "u.status",
    "u.data_cadastro"
]

COLUNAS_LIVRO = [
    "titulo", "subtitulo", "autor", "editora", "local_publicacao", "ano",
    "isbn", "assuntos", "palavras_chave", "numero_paginas", "serie",
    "colecao", "volume", "resumo", "imagem_capa", "categoria",
    "localizacao", "quantidade", "disponivel"
]


def _filtra_campos(dados, colunas):
    return {k: v for k, v in dados.items() if k in colunas}


def _preparar_senha(senha):
    """Gera hash seguro para a senha, a menos que já seja um hash (ex.: importações)."""
    if not senha:
        return None
    if senha.startswith(("scrypt:", "pbkdf2:", "sha256:")):
        return senha
    return generate_password_hash(senha)


# ============================================================
# AUDITORIA
# ============================================================
class Auditoria:
    TABLE = "auditoria_logs"

    @staticmethod
    def registrar(operacao, dados_afetados=None, responsavel=None):
        try:
            dados_json = json.dumps(dados_afetados, ensure_ascii=False, default=str) \
                if dados_afetados is not None else None
            execute(
                f"INSERT INTO {Auditoria.TABLE} (usuario_responsavel, operacao, dados_afetados) VALUES (?, ?, ?)",
                [responsavel, operacao, dados_json]
            )
        except Exception:
            # Auditoria nunca deve impedir a operação principal
            pass

    @staticmethod
    def listar(limite=None):
        sql = f"SELECT * FROM {Auditoria.TABLE} ORDER BY data_hora DESC"
        if limite:
            sql += f" LIMIT {int(limite)}"
        return query(sql)

    @staticmethod
    def buscar_por_periodo(inicio=None, fim=None, operacao=None):
        where = []
        params = []
        if inicio:
            where.append("data_hora >= ?")
            params.append(inicio)
        if fim:
            where.append("data_hora <= ?")
            params.append(fim)
        if operacao:
            where.append("operacao LIKE ?")
            params.append(f"%{operacao}%")
        where_sql = ("WHERE " + " AND ".join(where)) if where else ""
        return query(
            f"SELECT * FROM {Auditoria.TABLE} {where_sql} ORDER BY data_hora DESC",
            params
        )


# ============================================================
# NOTIFICAÇÕES
# ============================================================
class Notificacao:
    TABLE = "notificacoes"

    @staticmethod
    def criar(usuario_id, tipo, mensagem):
        execute(
            f"INSERT INTO {Notificacao.TABLE} (usuario_id, tipo, mensagem) VALUES (?, ?, ?)",
            [usuario_id, tipo, mensagem]
        )

    @staticmethod
    def listar_usuario(usuario_id):
        return query(
            f"SELECT * FROM {Notificacao.TABLE} WHERE usuario_id = ? ORDER BY data_criacao DESC",
            [usuario_id]
        )

    @staticmethod
    def nao_lidas(usuario_id):
        result = query_one(
            f"SELECT COUNT(*) AS total FROM {Notificacao.TABLE} WHERE usuario_id = ? AND lida = 0",
            [usuario_id]
        )
        return result["total"] if result else 0

    @staticmethod
    def marcar_lida(notificacao_id, usuario_id):
        return execute(
            f"UPDATE {Notificacao.TABLE} SET lida = 1 WHERE id = ? AND usuario_id = ?",
            [notificacao_id, usuario_id]
        )

    @staticmethod
    def marcar_todas_lidas(usuario_id):
        return execute(
            f"UPDATE {Notificacao.TABLE} SET lida = 1 WHERE usuario_id = ?",
            [usuario_id]
        )


# ============================================================
# PENALIDADES (suspensão = dobro dos dias de atraso)
# ============================================================
class Penalidade:
    TABLE = "penalidades"

    @staticmethod
    def aplicar(usuario_id, dias_atraso, emprestimo_id=None, descricao=None):
        """Registra suspensão. Suspensão = dobro dos dias de atraso por material."""
        dias_suspensao = dias_atraso * 2
        hoje = date.today()
        data_fim = hoje + timedelta(days=dias_suspensao)

        execute(
            f"""INSERT INTO {Penalidade.TABLE}
                (usuario_id, emprestimo_id, dias_atraso, dias_suspensao, data_inicio, data_fim, status, descricao)
                VALUES (?, ?, ?, ?, ?, ?, 'Ativa', ?)""",
            [usuario_id, emprestimo_id, dias_atraso, dias_suspensao, hoje, data_fim, descricao]
        )
        # Suspende o usuário
        execute("UPDATE usuarios SET status = 'Suspenso' WHERE id = ?", [usuario_id])
        Notificacao.criar(
            usuario_id, "suspensao",
            f"Você foi suspenso por {dias_atraso} dia(s) de atraso. "
            f"Suspensão de {dias_suspensao} dia(s) aplicada até {data_fim.isoformat()}."
        )
        return dias_suspensao

    @staticmethod
    def atualizar_status_usuario(usuario_id):
        """Se nenhuma penalidade estiver ativa, libera o usuário."""
        ativa = query_one(
            f"""SELECT COUNT(*) AS total FROM {Penalidade.TABLE}
                WHERE usuario_id = ? AND status = 'Ativa' AND data_fim >= CURRENT_DATE""",
            [usuario_id]
        )
        if not ativa or ativa["total"] == 0:
            execute(
                "UPDATE usuarios SET status = 'Ativo' WHERE id = ? AND status = 'Suspenso'",
                [usuario_id]
            )
            return True
        return False

    @staticmethod
    def esta_suspenso(usuario_id):
        ativa = query_one(
            f"""SELECT COUNT(*) AS total FROM {Penalidade.TABLE}
                WHERE usuario_id = ? AND status = 'Ativa' AND data_fim >= CURRENT_DATE""",
            [usuario_id]
        )
        return bool(ativa and ativa["total"] > 0)

    @staticmethod
    def ativas_usuario(usuario_id):
        return query(
            f"""SELECT * FROM {Penalidade.TABLE}
                WHERE usuario_id = ? AND status = 'Ativa'
                ORDER BY data_fim DESC""",
            [usuario_id]
        )

    @staticmethod
    def listar():
        return query(
            f"""SELECT p.*, u.nome AS usuario_nome
                FROM {Penalidade.TABLE} p
                JOIN usuarios u ON p.usuario_id = u.id
                ORDER BY p.data_registro DESC"""
        )


# ============================================================
# USUÁRIO
# ============================================================
class Usuario:
    TABLE = "usuarios"

    @staticmethod
    def listar():
        colunas = ", ".join(CAMPOS_PUBLICOS_USUARIO)
        return query(
            f"""SELECT {colunas},
                       COALESCE((SELECT COUNT(*) FROM emprestimos e
                                 WHERE e.usuario_id = u.id AND e.status = 'Emprestado'), 0) AS emprestimos_ativos
                FROM {Usuario.TABLE} u
                ORDER BY u.id DESC"""
        )

    @staticmethod
    def buscar(id):
        colunas = ", ".join(CAMPOS_PUBLICOS_USUARIO)
        return query_one(f"SELECT {colunas} FROM {Usuario.TABLE} u WHERE u.id = ?", [id])

    @staticmethod
    def buscar_por_email(email):
        return query_one(f"SELECT * FROM {Usuario.TABLE} WHERE email = ?", [email])

    @staticmethod
    def buscar_por_prontuario(prontuario):
        return query_one(f"SELECT * FROM {Usuario.TABLE} WHERE prontuario = ?", [prontuario])

    @staticmethod
    def criar(dados):
        dados = vd.limpar_campos(dict(dados), ["nome", "email", "telefone", "endereco", "prontuario", "curso"])
        faltantes = vd.campos_obrigatorios(dados, ["nome", "email"])
        if faltantes:
            raise ValueError(f"Campos obrigatórios não preenchidos: {', '.join(faltantes)}")
        if not vd.validar_email(dados.get("email", "")):
            raise ValueError("E-mail inválido.")
        if not vd.validar_telefone(dados.get("telefone", "")):
            raise ValueError("Telefone inválido. Use o formato (11) 99999-0000.")
        if not vd.validar_prontuario(dados.get("prontuario", "")):
            raise ValueError("Prontuário inválido. Use o formato CV0000000.")
        categoria = dados.get("tipo_usuario", "Discente Regular")
        if not vd.validar_categoria(categoria):
            raise ValueError("Categoria inválida.")

        campos = _filtra_campos(dados, COLUNAS_USUARIO)
        if "senha" in campos:
            campos["senha"] = _preparar_senha(campos["senha"])
        colunas = ", ".join(campos.keys())
        valores = list(campos.values())
        placeholders = ", ".join(["?"] * len(campos))

        novo_id = execute_insert(
            f"INSERT INTO {Usuario.TABLE} ({colunas}) VALUES ({placeholders}) RETURNING id",
            valores
        )
        Auditoria.registrar("Cadastro de Usuário", {"id": novo_id, "nome": dados.get("nome")})
        return novo_id

    @staticmethod
    def atualizar(id, dados):
        dados = vd.limpar_campos(dict(dados), ["nome", "email", "telefone", "endereco", "prontuario", "curso"])
        if "email" in dados and not vd.validar_email(dados.get("email", "")):
            raise ValueError("E-mail inválido.")
        if "telefone" in dados and not vd.validar_telefone(dados.get("telefone", "")):
            raise ValueError("Telefone inválido. Use o formato (11) 99999-0000.")
        if "prontuario" in dados and not vd.validar_prontuario(dados.get("prontuario", "")):
            raise ValueError("Prontuário inválido. Use o formato CV0000000.")

        campos = _filtra_campos(dados, COLUNAS_USUARIO)
        if not campos:
            return 0
        if "senha" in campos:
            campos["senha"] = _preparar_senha(campos["senha"])
        colunas = ", ".join([f"{k} = ?" for k in campos])
        valores = list(campos.values()) + [id]
        execute(f"UPDATE {Usuario.TABLE} SET {colunas} WHERE id = ?", valores)
        Auditoria.registrar("Alteração de Usuário", {"id": id, "dados": {k: v for k, v in campos.items() if k != "senha"}})
        return True

    @staticmethod
    def excluir(id):
        ativos = query_one(
            "SELECT COUNT(*) AS total FROM emprestimos WHERE usuario_id = ? AND status = 'Emprestado'",
            [id]
        )
        if ativos and ativos["total"] > 0:
            raise ValueError("Não é possível excluir um usuário com empréstimos ativos.")
        execute(f"DELETE FROM {Usuario.TABLE} WHERE id = ?", [id])
        Auditoria.registrar("Exclusão de Usuário", {"id": id})
        return True

    @staticmethod
    def regras_categoria(tipo_usuario):
        return CATEGORIA_REGRAS.get(tipo_usuario, CATEGORIA_REGRAS["Discente Regular"])

    @staticmethod
    def pode_emprestar(usuario):
        """Verifica se o usuário pode realizar novo empréstimo. Retorna (ok, mensagem)."""
        if not usuario:
            return False, "Usuário não encontrado."
        Penalidade.atualizar_status_usuario(usuario["id"])
        usuario = Usuario.buscar(usuario["id"])

        if usuario["status"] == "Inativo":
            return False, "Usuário inativo. Não é possível realizar empréstimos."

        if Penalidade.esta_suspenso(usuario["id"]):
            return False, "Usuário suspenso. Bloqueado até o fim da penalidade."

        regras = Usuario.regras_categoria(usuario["tipo_usuario"])
        ativos = query_one(
            "SELECT COUNT(*) AS total FROM emprestimos WHERE usuario_id = ? AND status = 'Emprestado'",
            [usuario["id"]]
        )
        em_uso = ativos["total"] if ativos else 0
        if em_uso >= regras["limite"]:
            return False, (
                f"Limite de empréstimos atingido ({em_uso}/{regras['limite']}). "
                f"A categoria {usuario['tipo_usuario']} permite no máximo {regras['limite']} livro(s)."
            )
        return True, ""


# ============================================================
# LIVRO
# ============================================================
class Livro:
    TABLE = "livros"

    @staticmethod
    def listar():
        return query(
            f"""SELECT l.*,
                       COALESCE((SELECT COUNT(*) FROM emprestimos e
                                 WHERE e.livro_id = l.id AND e.status = 'Emprestado'), 0) AS emprestados,
                       COALESCE((SELECT COUNT(*) FROM reservas r
                                 WHERE r.livro_id = l.id AND r.status = 'Ativa'), 0) AS reservas_ativas
                FROM {Livro.TABLE} l
                ORDER BY l.id DESC"""
        )

    @staticmethod
    def buscar(id):
        return query_one(f"SELECT * FROM {Livro.TABLE} WHERE id = ?", [id])

    @staticmethod
    def buscar_por_isbn(isbn):
        return query_one(f"SELECT * FROM {Livro.TABLE} WHERE isbn = ?", [isbn])

    @staticmethod
    def criar(dados):
        dados = vd.limpar_campos(dict(dados), [
            "titulo", "subtitulo", "autor", "editora", "local_publicacao",
            "isbn", "assuntos", "palavras_chave", "serie", "colecao", "volume",
            "resumo", "imagem_capa", "categoria", "localizacao"
        ])
        faltantes = vd.campos_obrigatorios(dados, ["titulo", "autor", "isbn"])
        if faltantes:
            raise ValueError(f"Campos obrigatórios não preenchidos: {', '.join(faltantes)}")

        isbn = dados.get("isbn", "").strip()
        if not vd.validar_isbn(isbn):
            raise ValueError("ISBN inválido. Informe um ISBN-10 ou ISBN-13 válido.")
        if Livro.buscar_por_isbn(isbn):
            raise ValueError("Já existe um livro cadastrado com este ISBN.")

        quantidade = vd.inteiro(dados.get("quantidade"), 1)
        dados["quantidade"] = max(0, quantidade)
        dados["disponivel"] = dados["quantidade"]

        campos = _filtra_campos(dados, COLUNAS_LIVRO)
        colunas = ", ".join(campos.keys())
        valores = list(campos.values())
        placeholders = ", ".join(["?"] * len(campos))

        novo_id = execute_insert(
            f"INSERT INTO {Livro.TABLE} ({colunas}) VALUES ({placeholders}) RETURNING id",
            valores
        )
        Auditoria.registrar("Cadastro de Livro", {"id": novo_id, "titulo": dados.get("titulo")})
        return novo_id

    @staticmethod
    def atualizar(id, dados):
        dados = vd.limpar_campos(dict(dados), [
            "titulo", "subtitulo", "autor", "editora", "local_publicacao",
            "isbn", "assuntos", "palavras_chave", "serie", "colecao", "volume",
            "resumo", "imagem_capa", "categoria", "localizacao"
        ])
        if "isbn" in dados:
            isbn = dados["isbn"].strip()
            if not vd.validar_isbn(isbn):
                raise ValueError("ISBN inválido. Informe um ISBN-10 ou ISBN-13 válido.")
            existente = Livro.buscar_por_isbn(isbn)
            if existente and existente["id"] != id:
                raise ValueError("Já existe outro livro cadastrado com este ISBN.")

        campos = _filtra_campos(dados, COLUNAS_LIVRO)
        if "quantidade" in campos:
            emprestados = Emprestimo.contar_emprestados_por_livro(id)
            campos["quantidade"] = max(0, vd.inteiro(campos["quantidade"], 1))
            campos["disponivel"] = max(0, campos["quantidade"] - emprestados)

        if not campos:
            return 0
        colunas = ", ".join([f"{k} = ?" for k in campos])
        valores = list(campos.values()) + [id]
        execute(f"UPDATE {Livro.TABLE} SET {colunas} WHERE id = ?", valores)
        Auditoria.registrar("Edição de Livro", {"id": id, "campos": list(campos.keys())})
        return True

    @staticmethod
    def excluir(id):
        ativos = query_one(
            "SELECT COUNT(*) AS total FROM emprestimos WHERE livro_id = ? AND status = 'Emprestado'",
            [id]
        )
        if ativos and ativos["total"] > 0:
            raise ValueError("Não é possível excluir um livro com empréstimos ativos.")
        execute(f"DELETE FROM {Livro.TABLE} WHERE id = ?", [id])
        Auditoria.registrar("Exclusão de Livro", {"id": id})
        return True

    CAMPOS_BUSCA = [
        "titulo", "subtitulo", "autor", "editora", "local_publicacao",
        "isbn", "assuntos", "palavras_chave", "serie", "colecao",
        "categoria", "localizacao"
    ]

    @staticmethod
    def buscar_avancada(termo=None, campo=None):
        """Consulta ao acervo — busca por título, autor, ISBN, editora, assunto,
        palavra-chave, série, coleção. O campo é validado contra uma whitelist
        para evitar injeção de SQL."""
        base = f"SELECT * FROM {Livro.TABLE} l"
        where = []
        params = []

        if termo:
            termo_ilike = f"%{termo}%"
            if campo and campo in Livro.CAMPOS_BUSCA:
                campos_busca = [campo]
            else:
                campos_busca = Livro.CAMPOS_BUSCA
            termos = []
            for c in campos_busca:
                termos.append(f"l.{c} LIKE ?")
                params.append(termo_ilike)
            where.append("(" + " OR ".join(termos) + ")")

        where_sql = ("WHERE " + " AND ".join(where)) if where else ""
        return query(base + f" {where_sql} ORDER BY l.titulo ASC", params)


# ============================================================
# EMPRÉSTIMO
# ============================================================
class Emprestimo:
    TABLE = "emprestimos"

    @staticmethod
    def listar():
        return query(
            f"""SELECT e.id, u.nome AS usuario_nome, l.titulo AS livro_titulo,
                       e.usuario_id, e.livro_id,
                       e.data_emprestimo, e.data_prevista_devolucao, e.data_devolucao,
                       e.renovacoes, e.status,
                       (CASE WHEN e.status = 'Emprestado' AND e.data_prevista_devolucao < CURRENT_DATE
                             THEN max(CAST(julianday(CURRENT_DATE) - julianday(e.data_prevista_devolucao) AS INTEGER), 0) ELSE 0 END) AS dias_atraso
                FROM {Emprestimo.TABLE} e
                JOIN usuarios u ON e.usuario_id = u.id
                JOIN livros l ON e.livro_id = l.id
                ORDER BY e.id DESC"""
        )

    @staticmethod
    def buscar(id):
        return query_one(
            f"""SELECT e.id, u.nome AS usuario_nome, l.titulo AS livro_titulo,
                       e.usuario_id, e.livro_id, u.tipo_usuario,
                       e.data_emprestimo, e.data_prevista_devolucao, e.data_devolucao,
                       e.renovacoes, e.status
                FROM {Emprestimo.TABLE} e
                JOIN usuarios u ON e.usuario_id = u.id
                JOIN livros l ON e.livro_id = l.id
                WHERE e.id = ?""",
            [id]
        )

    @staticmethod
    def criar(dados):
        usuario_id = vd.inteiro(dados.get("usuario_id"))
        livro_id = vd.inteiro(dados.get("livro_id"))
        if not usuario_id or not livro_id:
            raise ValueError("Usuário e livro são obrigatórios.")

        usuario = Usuario.buscar(usuario_id)
        if not usuario:
            raise ValueError("Usuário não encontrado.")

        ok, motivo = Usuario.pode_emprestar(usuario)
        if not ok:
            raise ValueError(motivo)

        livro = Livro.buscar(livro_id)
        if not livro:
            raise ValueError("Livro não encontrado.")
        if livro["disponivel"] <= 0:
            raise ValueError("Livro não disponível para empréstimo.")

        # Fila de reservas: impede empréstimo se houver reserva de outro usuário
        # antes na fila. Se o solicitante for o primeiro da fila, marca como concluída.
        reservas = Reserva.fila_do_livro(livro_id)
        if reservas:
            primeiro = reservas[0]
            if primeiro["usuario_id"] != usuario_id:
                raise ValueError(
                    f"Este livro possui reservas ativas. O próximo da fila é "
                    f"{primeiro['usuario_nome']}. Entregue ao usuário com reserva ou cancele as reservas."
                )
            Reserva.marcar_concluida(primeiro["id"])

        data_emprestimo = vd.data_iso(dados.get("data_emprestimo")) or date.today()
        data_prevista = vd.data_iso(dados.get("data_prevista_devolucao"))
        if not data_prevista:
            regras = Usuario.regras_categoria(usuario["tipo_usuario"])
            data_prevista = data_emprestimo + timedelta(days=regras["prazo"])
        if data_prevista <= data_emprestimo:
            raise ValueError("A data prevista de devolução deve ser posterior à data do empréstimo.")

        with transacao() as conn:
            cur = _executar(
                conn,
                f"""INSERT INTO {Emprestimo.TABLE}
                    (usuario_id, livro_id, data_emprestimo, data_prevista_devolucao, status)
                    VALUES (?, ?, ?, ?, 'Emprestado') RETURNING id""",
                [usuario_id, livro_id, data_emprestimo, data_prevista]
            )
            emprestimo_id = cur.fetchone()["id"]

            cur = _executar(
                conn,
                "SELECT disponivel FROM livros WHERE id = ?",
                [livro_id]
            )
            disponivel = cur.fetchone()["disponivel"]
            _executar(
                conn,
                "UPDATE livros SET disponivel = ? WHERE id = ?",
                [disponivel - 1, livro_id]
            )

        regras = Usuario.regras_categoria(usuario["tipo_usuario"])
        Notificacao.criar(
            usuario_id, "emprestimo",
            f"Empréstimo de \"{livro['titulo']}\" realizado. Devolução prevista para {data_prevista.isoformat()}."
        )
        Auditoria.registrar(
            "Empréstimo realizado",
            {"emprestimo_id": emprestimo_id, "usuario": usuario["nome"], "livro": livro["titulo"]},
        )
        return emprestimo_id

    @staticmethod
    def renovar(id):
        emprestimo = Emprestimo.buscar(id)
        if not emprestimo:
            raise ValueError("Empréstimo não encontrado.")
        if emprestimo["status"] != "Emprestado":
            raise ValueError("Somente empréstimos ativos podem ser renovados.")

        if emprestimo["renovacoes"] >= MAX_RENOVACOES:
            raise ValueError(f"Limite máximo de {MAX_RENOVACOES} renovações atingido.")

        hoje = date.today()
        if date.fromisoformat(str(emprestimo["data_prevista_devolucao"])) < hoje:
            raise ValueError("Não é possível renovar um empréstimo em atraso. Realize a devolução.")

        # Não permite renovar se houver reserva (de outro usuário)
        reservas = Reserva.fila_do_livro(emprestimo["livro_id"])
        if reservas:
            for r in reservas:
                if r["usuario_id"] != emprestimo["usuario_id"]:
                    raise ValueError("Não é possível renovar: este livro possui reserva de outro usuário.")

        usuario = Usuario.buscar(emprestimo["usuario_id"])
        regras = Usuario.regras_categoria(usuario["tipo_usuario"])
        nova_data = date.fromisoformat(str(emprestimo["data_prevista_devolucao"])) + timedelta(days=regras["prazo"])

        with transacao() as conn:
            _executar(
                conn,
                f"UPDATE {Emprestimo.TABLE} SET renovacoes = renovacoes + 1, data_prevista_devolucao = ? WHERE id = ?",
                [nova_data, id]
            )
            _executar(
                conn,
                "INSERT INTO renovacoes (emprestimo_id, nova_data_prevista) VALUES (?, ?)",
                [id, nova_data]
            )

        Notificacao.criar(
            emprestimo["usuario_id"], "renovacao",
            f"Renovação de \"{emprestimo['livro_titulo']}\" realizada. Nova devolução em {nova_data.isoformat()}."
        )
        Auditoria.registrar(
            "Renovação realizada",
            {"emprestimo_id": id, "livro": emprestimo["livro_titulo"], "nova_data": nova_data.isoformat()}
        )
        return {"nova_data_prevista": nova_data.isoformat(), "renovacoes": emprestimo["renovacoes"] + 1}

    @staticmethod
    def devolver(id):
        emprestimo = Emprestimo.buscar(id)
        if not emprestimo:
            raise ValueError("Empréstimo não encontrado.")
        if emprestimo["status"] == "Devolvido":
            raise ValueError("Este livro já foi devolvido.")

        data_devolucao = date.today()
        dias_atraso = (data_devolucao - date.fromisoformat(str(emprestimo["data_prevista_devolucao"]))).days

        with transacao() as conn:
            _executar(
                conn,
                f"UPDATE {Emprestimo.TABLE} SET data_devolucao = ?, status = 'Devolvido' WHERE id = ?",
                [data_devolucao, id]
            )
            _executar(
                conn,
                "SELECT disponivel FROM livros WHERE id = ?",
                [emprestimo["livro_id"]]
            )
            _executar(
                conn,
                "UPDATE livros SET disponivel = disponivel + 1 WHERE id = ?",
                [emprestimo["livro_id"]]
            )

        resultado = {"dias_atraso": max(dias_atraso, 0), "suspensao_aplicada": 0}

        if dias_atraso > 0:
            descricao = f"Atraso de {dias_atraso} dia(s) na devolução de {emprestimo['livro_titulo']}"
            dias_suspensao = Penalidade.aplicar(
                emprestimo["usuario_id"], dias_atraso,
                emprestimo_id=id, descricao=descricao
            )
            resultado["suspensao_aplicada"] = dias_suspensao
            Auditoria.registrar(
                "Aplicação de penalidade",
                {"usuario": emprestimo["usuario_nome"], "dias_atraso": dias_atraso, "dias_suspensao": dias_suspensao}
            )
        else:
            Notificacao.criar(
                emprestimo["usuario_id"], "devolucao",
                f"Devolução de \"{emprestimo['livro_titulo']}\" registrada com sucesso."
            )

        # Notifica a fila de reservas
        proxima = Reserva.proxima_da_fila(emprestimo["livro_id"])
        if proxima:
            Reserva.notificar_disponivel(proxima["id"])
            Notificacao.criar(
                proxima["usuario_id"], "reserva_disponivel",
                f"O livro \"{emprestimo['livro_titulo']}\" reservado por você está disponível. "
                f"Procure a biblioteca para retirá-lo."
            )

        Auditoria.registrar(
            "Devolução realizada",
            {"emprestimo_id": id, "livro": emprestimo["livro_titulo"], "usuario": emprestimo["usuario_nome"]}
        )
        return resultado

    @staticmethod
    def historico():
        return query(
            f"""SELECT e.id, u.nome AS usuario_nome, l.titulo AS livro_titulo,
                       e.data_emprestimo, e.data_prevista_devolucao, e.data_devolucao,
                       e.renovacoes, e.status,
                       (CASE WHEN e.data_devolucao IS NOT NULL AND e.data_devolucao > e.data_prevista_devolucao
                             THEN CAST(julianday(e.data_devolucao) - julianday(e.data_prevista_devolucao) AS INTEGER) ELSE 0 END) AS dias_atraso
                FROM {Emprestimo.TABLE} e
                JOIN usuarios u ON e.usuario_id = u.id
                JOIN livros l ON e.livro_id = l.id
                ORDER BY e.data_emprestimo DESC, e.id DESC"""
        )

    @staticmethod
    def historico_usuario(usuario_id):
        return query(
            f"""SELECT e.*, l.titulo AS livro_titulo, l.isbn AS livro_isbn,
                       (CASE WHEN e.data_devolucao IS NOT NULL AND e.data_devolucao > e.data_prevista_devolucao
                             THEN CAST(julianday(e.data_devolucao) - julianday(e.data_prevista_devolucao) AS INTEGER) ELSE 0 END) AS dias_atraso
                FROM {Emprestimo.TABLE} e
                JOIN livros l ON e.livro_id = l.id
                WHERE e.usuario_id = ?
                ORDER BY e.data_emprestimo DESC, e.id DESC""",
            [usuario_id]
        )

    @staticmethod
    def renovacoes_do_emprestimo(emprestimo_id):
        return query(
            f"SELECT * FROM renovacoes WHERE emprestimo_id = ? ORDER BY data_renovacao DESC",
            [emprestimo_id]
        )

    @staticmethod
    def contar_emprestados():
        result = query_one(
            f"SELECT COUNT(*) AS total FROM {Emprestimo.TABLE} WHERE status = 'Emprestado'"
        )
        return result["total"] if result else 0

    @staticmethod
    def contar_emprestados_por_livro(livro_id):
        result = query_one(
            f"SELECT COUNT(*) AS total FROM {Emprestimo.TABLE} WHERE livro_id = ? AND status = 'Emprestado'",
            [livro_id]
        )
        return result["total"] if result else 0

    @staticmethod
    def contar_atrasados():
        result = query_one(
            f"SELECT COUNT(*) AS total FROM {Emprestimo.TABLE} "
            f"WHERE status = 'Emprestado' AND data_prevista_devolucao < CURRENT_DATE"
        )
        return result["total"] if result else 0

    @staticmethod
    def contar_devolvidos():
        result = query_one(
            f"SELECT COUNT(*) AS total FROM {Emprestimo.TABLE} WHERE data_devolucao IS NOT NULL"
        )
        return result["total"] if result else 0

    @staticmethod
    def listar_ativos():
        return query(
            f"""SELECT e.*, u.nome AS usuario_nome, l.titulo AS livro_titulo,
                       (CASE WHEN e.data_prevista_devolucao < CURRENT_DATE
                             THEN max(CAST(julianday(CURRENT_DATE) - julianday(e.data_prevista_devolucao) AS INTEGER), 0) ELSE 0 END) AS dias_atraso
                FROM {Emprestimo.TABLE} e
                JOIN usuarios u ON e.usuario_id = u.id
                JOIN livros l ON e.livro_id = l.id
                WHERE e.status = 'Emprestado'
                ORDER BY e.data_prevista_devolucao ASC"""
        )

    @staticmethod
    def listar_ativos_usuario(usuario_id):
        return query(
            f"""SELECT e.*, u.nome AS usuario_nome, l.titulo AS livro_titulo,
                       (CASE WHEN e.data_prevista_devolucao < CURRENT_DATE
                             THEN max(CAST(julianday(CURRENT_DATE) - julianday(e.data_prevista_devolucao) AS INTEGER), 0) ELSE 0 END) AS dias_atraso
                FROM {Emprestimo.TABLE} e
                JOIN usuarios u ON e.usuario_id = u.id
                JOIN livros l ON e.livro_id = l.id
                WHERE e.status = 'Emprestado' AND e.usuario_id = ?
                ORDER BY e.data_prevista_devolucao ASC""",
            [usuario_id]
        )


# ============================================================
# RESERVA
# ============================================================
class Reserva:
    TABLE = "reservas"

    @staticmethod
    def criar(livro_id, usuario_id):
        livro = Livro.buscar(livro_id)
        if not livro:
            raise ValueError("Livro não encontrado.")

        duplicada = query_one(
            f"SELECT COUNT(*) AS total FROM {Reserva.TABLE} "
            f"WHERE livro_id = ? AND usuario_id = ? AND status IN ('Ativa', 'Disponível')",
            [livro_id, usuario_id]
        )
        if duplicada and duplicada["total"] > 0:
            raise ValueError("Você já possui uma reserva ativa para este livro.")

        novo_id = execute_insert(
            f"INSERT INTO {Reserva.TABLE} (livro_id, usuario_id, status) "
            f"VALUES (?, ?, 'Ativa') RETURNING id",
            [livro_id, usuario_id]
        )
        Auditoria.registrar(
            "Reserva realizada",
            {"reserva_id": novo_id, "livro": livro["titulo"], "usuario_id": usuario_id}
        )
        Notificacao.criar(
            usuario_id, "reserva",
            f"Reserva de \"{livro['titulo']}\" confirmada. Você está na fila de espera."
        )
        return novo_id

    @staticmethod
    def cancelar(id, usuario_id=None):
        reserva = query_one(
            f"SELECT * FROM {Reserva.TABLE} WHERE id = ?", [id]
        )
        if not reserva:
            raise ValueError("Reserva não encontrada.")
        if usuario_id and reserva["usuario_id"] != usuario_id:
            raise ValueError("Esta reserva pertence a outro usuário.")
        if reserva["status"] not in ("Ativa", "Disponível"):
            raise ValueError("Esta reserva não está mais ativa.")

        execute(
            f"UPDATE {Reserva.TABLE} SET status = 'Cancelada' WHERE id = ?", [id]
        )
        Auditoria.registrar(
            "Cancelamento de reserva",
            {"reserva_id": id, "usuario_id": reserva["usuario_id"]}
        )
        return True

    @staticmethod
    def listar():
        return query(
            f"""SELECT r.id, r.livro_id, r.usuario_id, r.data_reserva, r.status, r.notificado,
                       l.titulo AS livro_titulo, l.disponivel AS livro_disponivel,
                       u.nome AS usuario_nome, u.email AS usuario_email,
                       (SELECT COUNT(*) FROM reservas r2
                        WHERE r2.livro_id = r.livro_id
                          AND r2.status = 'Ativa'
                          AND (r2.data_reserva < r.data_reserva
                               OR (r2.data_reserva = r.data_reserva AND r2.id <= r.id))) AS posicao
                FROM {Reserva.TABLE} r
                JOIN livros l ON r.livro_id = l.id
                JOIN usuarios u ON r.usuario_id = u.id
                ORDER BY l.titulo ASC, r.data_reserva ASC"""
        )

    @staticmethod
    def listar_usuario(usuario_id):
        return query(
            f"""SELECT r.*, l.titulo AS livro_titulo, l.disponivel AS livro_disponivel,
                       (SELECT COUNT(*) FROM reservas r2
                        WHERE r2.livro_id = r.livro_id
                          AND r2.status = 'Ativa'
                          AND (r2.data_reserva < r.data_reserva
                               OR (r2.data_reserva = r.data_reserva AND r2.id <= r.id))) AS posicao
                FROM {Reserva.TABLE} r
                JOIN livros l ON r.livro_id = l.id
                WHERE r.usuario_id = ?
                ORDER BY r.data_reserva DESC""",
            [usuario_id]
        )

    @staticmethod
    def fila_do_livro(livro_id):
        return query(
            f"""SELECT r.*, u.nome AS usuario_nome
                FROM {Reserva.TABLE} r
                JOIN usuarios u ON r.usuario_id = u.id
                WHERE r.livro_id = ? AND r.status = 'Ativa'
                ORDER BY r.data_reserva ASC""",
            [livro_id]
        )

    @staticmethod
    def proxima_da_fila(livro_id):
        return query_one(
            f"""SELECT * FROM {Reserva.TABLE}
                WHERE livro_id = ? AND status = 'Ativa'
                ORDER BY data_reserva ASC LIMIT 1""",
            [livro_id]
        )

    @staticmethod
    def notificar_disponivel(reserva_id):
        return execute(
            f"UPDATE {Reserva.TABLE} SET status = 'Disponível', notificado = 1 WHERE id = ?",
            [reserva_id]
        )

    @staticmethod
    def marcar_concluida(reserva_id):
        return execute(
            f"UPDATE {Reserva.TABLE} SET status = 'Concluída' WHERE id = ?",
            [reserva_id]
        )


# ============================================================
# SERVIÇOS AO USUÁRIO
# ============================================================
class ServicoSolicitacao:
    TABLE = "servicos_solicitacoes"

    TIPOS = [
        "Declaração de Nada Consta",
        "Ficha Catalográfica",
        "Sugestão de Aquisição",
        "Solicitação de Serviço",
    ]

    @staticmethod
    def criar(usuario_id, tipo, descricao=None, dados_json=None):
        if tipo not in ServicoSolicitacao.TIPOS:
            raise ValueError("Tipo de solicitação inválido.")
        if not descricao and not dados_json:
            raise ValueError("Descreva a solicitação.")

        novo_id = execute_insert(
            f"""INSERT INTO {ServicoSolicitacao.TABLE} (usuario_id, tipo, descricao, dados_json)
                VALUES (?, ?, ?, ?) RETURNING id""",
            [usuario_id, tipo, descricao, json.dumps(dados_json, ensure_ascii=False, default=str) if dados_json else None]
        )
        Auditoria.registrar(
            "Solicitação de serviço",
            {"solicitacao_id": novo_id, "tipo": tipo, "usuario_id": usuario_id}
        )
        return novo_id

    @staticmethod
    def listar():
        return query(
            f"""SELECT s.*, u.nome AS usuario_nome, u.email AS usuario_email
                FROM {ServicoSolicitacao.TABLE} s
                JOIN usuarios u ON s.usuario_id = u.id
                ORDER BY s.data_solicitacao DESC"""
        )

    @staticmethod
    def listar_usuario(usuario_id):
        return query(
            f"SELECT * FROM {ServicoSolicitacao.TABLE} WHERE usuario_id = ? "
            f"ORDER BY data_solicitacao DESC",
            [usuario_id]
        )

    @staticmethod
    def atualizar_status(id, status, resposta=None):
        if status not in ("Pendente", "Em Análise", "Concluída", "Recusada"):
            raise ValueError("Status inválido.")
        execute(
            f"""UPDATE {ServicoSolicitacao.TABLE}
                SET status = ?, resposta = ?, data_resposta = CURRENT_TIMESTAMP
                WHERE id = ?""",
            [status, resposta, id]
        )
        return True


# ============================================================
# SESSÃO (autenticação)
# ============================================================
class Sessao:
    TABLE = "sessoes"

    # Expiração automática da sessão (em horas)
    EXPIRA_EM_HORAS = 24

    @staticmethod
    def criar(usuario_id, token):
        return execute_insert(
            f"INSERT INTO {Sessao.TABLE} (token, usuario_id) VALUES (?, ?) RETURNING id",
            [token, usuario_id]
        )

    @staticmethod
    def buscar_por_token(token):
        sessao = query_one(
            f"""SELECT s.*, u.nome AS nome, u.email AS email, u.perfil, u.status,
                       u.tipo_usuario, u.id AS usuario_id
                FROM {Sessao.TABLE} s
                JOIN usuarios u ON s.usuario_id = u.id
                WHERE s.token = ?""",
            [token]
        )
        if not sessao:
            return None
        # Expira sessões antigas (configuração de segurança)
        if sessao.get("criada_em"):
            from datetime import datetime, timedelta
            try:
                criada = sessao["criada_em"]
                if isinstance(criada, str):
                    criada = datetime.fromisoformat(criada)
                limite = datetime.now() - timedelta(hours=Sessao.EXPIRA_EM_HORAS)
                if criada < limite:
                    Sessao.encerrar(token)
                    return None
            except (TypeError, ValueError):
                pass
        return sessao

    @staticmethod
    def encerrar(token):
        return execute(f"DELETE FROM {Sessao.TABLE} WHERE token = ?", [token])
