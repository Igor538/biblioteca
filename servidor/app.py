import logging
import os
import secrets
import sys
import time
import uuid
from datetime import date, timedelta
from functools import wraps
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from flask import (
    Flask,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.exceptions import HTTPException
from werkzeug.security import generate_password_hash, check_password_hash

from database import (
    buscar_usuario_por_email,
    buscar_usuario_por_cpf,
    buscar_usuario_por_matricula,
    buscar_usuario_por_id,
    cadastrar_usuario,
    dados_dashboard,
)
from seguranca import (
    HASH_FICTICIO,
    aplicar_cabecalhos_seguranca,
    bool_env,
    ip_cliente,
    limite_cadastro,
    limite_login,
    limite_login_ip,
    validar_origem_requisicao,
    validar_senha_forte,
)
from validators import limpar_texto, validar_email

# ============================================================
# CONFIGURAÇÃO DO FLASK
# ============================================================

app = Flask(
    __name__,
    template_folder="../cliente/templates",
    static_folder="../cliente/static"
)


def _int_env(nome, padrao):
    try:
        return int(os.environ.get(nome, padrao))
    except (TypeError, ValueError):
        return int(padrao)


logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
log = logging.getLogger("biblioteca")

_AMBIENTE = (
    os.environ.get("APP_ENV") or os.environ.get("FLASK_ENV") or "development"
).strip().lower()
_PRODUCAO = _AMBIENTE in ("production", "producao", "prod")

_chave = (os.environ.get("SECRET_KEY") or "").strip()
if not _chave:
    if _PRODUCAO:
        raise RuntimeError(
            "Defina a variavel de ambiente SECRET_KEY antes de iniciar em producao."
        )
    _chave = secrets.token_hex(32)
    log.warning(
        "SECRET_KEY nao definida; usando chave temporaria de desenvolvimento. "
        "As sessoes serao invalidadas ao reiniciar."
    )
app.secret_key = _chave

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=bool_env(
        "SESSION_COOKIE_SECURE",
        _PRODUCAO
        or os.environ.get("APP_BASE_URL", "").strip().lower().startswith("https://"),
    ),
    PERMANENT_SESSION_LIFETIME=timedelta(hours=_int_env("SESSION_HORAS", 8)),
    MAX_CONTENT_LENGTH=_int_env("MAX_CONTENT_LENGTH", 1024 * 1024),
    JSON_SORT_KEYS=False,
)

_HASH_FICTICIO = HASH_FICTICIO


# ============================================================
# CABEÇALHOS, ORIGEM E TRATAMENTO DE ERROS
# ============================================================

@app.before_request
def _antes_requisicao():
    g.request_id = uuid.uuid4().hex[:12]
    g.inicio = time.monotonic()

    if not validar_origem_requisicao():
        log.warning(
            "origem_bloqueada req=%s metodo=%s rota=%s ip=%s",
            g.request_id, request.method, request.path, ip_cliente(),
        )
        if request.path.startswith("/api/"):
            return jsonify({
                "sucesso": False,
                "erro": "Origem da requisição não permitida.",
            }), 403
        return "Origem da requisição não permitida.", 403


@app.after_request
def _depois_requisicao(resposta):
    aplicar_cabecalhos_seguranca(resposta)
    if request.path.startswith("/api/"):
        duracao = (time.monotonic() - getattr(g, "inicio", time.monotonic())) * 1000
        log.info(
            "req=%s metodo=%s rota=%s status=%s ms=%.1f",
            getattr(g, "request_id", "-"), request.method,
            request.path, resposta.status_code, duracao,
        )
    return resposta


def _resposta_erro(mensagem, status):
    if request.path.startswith("/api/"):
        return jsonify({"sucesso": False, "erro": mensagem}), status
    return mensagem, status


@app.errorhandler(400)
def _erro_400(erro):
    return _resposta_erro("Requisição inválida.", 400)


@app.errorhandler(403)
def _erro_403(erro):
    return _resposta_erro("Acesso negado.", 403)


@app.errorhandler(405)
def _erro_405(erro):
    return _resposta_erro("Método não permitido.", 405)


@app.errorhandler(413)
def _erro_413(erro):
    return _resposta_erro("Corpo da requisição muito grande.", 413)


@app.errorhandler(429)
def _erro_429(erro):
    return _resposta_erro(
        "Muitas requisições. Aguarde alguns minutos e tente novamente.", 429
    )


@app.errorhandler(Exception)
def _erro_generico(erro):
    if isinstance(erro, HTTPException):
        return erro
    log.exception("erro_interno req=%s", getattr(g, "request_id", "-"))
    return _resposta_erro("Erro interno do servidor.", 500)


# ============================================================
# INICIALIZAÇÃO DO BANCO
# ============================================================

from database import inicializar_banco
inicializar_banco()

from auth import inicializar_administradores
inicializar_administradores()


# Registrar API JSON (blueprints)
from routes.auth import auth_bp
from routes.auditoria import auditoria_bp
from routes.backup import backup_bp
from routes.busca import busca_bp
from routes.emprestimos import emprestimos_bp
from routes.livros import livros_bp
from routes.notificacoes import notificacoes_bp
from routes.penalidades import penalidades_bp
from routes.relatorios import relatorios_bp
from routes.reservas import reservas_bp
from routes.servicos import servicos_bp
from routes.usuarios import usuarios_bp

app.register_blueprint(auth_bp)
app.register_blueprint(auditoria_bp, url_prefix="/api")
app.register_blueprint(backup_bp, url_prefix="/api")
app.register_blueprint(busca_bp, url_prefix="/api")
app.register_blueprint(emprestimos_bp, url_prefix="/api")
app.register_blueprint(livros_bp, url_prefix="/api")
app.register_blueprint(notificacoes_bp, url_prefix="/api")
app.register_blueprint(penalidades_bp, url_prefix="/api")
app.register_blueprint(relatorios_bp, url_prefix="/api")
app.register_blueprint(reservas_bp, url_prefix="/api")
app.register_blueprint(servicos_bp, url_prefix="/api")
app.register_blueprint(usuarios_bp, url_prefix="/api")


# ============================================================
# HELPERS
# ============================================================

def usuario_logado():
    """Retorna True se existe usuário autenticado na sessão."""
    return "usuario_id" in session


def requer_login(view):
    """Redireciona para /login se não houver sessão ativa."""
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not usuario_logado():
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapper


# ============================================================
# PÁGINA INICIAL
# ============================================================

@app.route("/")
def index():
    return render_template("index.html")


# ============================================================
# LOGIN
# ============================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "GET":
        return render_template("login.html")

    email = (limpar_texto(request.form.get("email", "")) or "").lower()[:254]
    senha = request.form.get("senha", "")

    if not email:
        return jsonify({
            "sucesso": False,
            "mensagem": "Informe o e-mail."
        }), 400

    if not senha:
        return jsonify({
            "sucesso": False,
            "mensagem": "Informe a senha."
        }), 400

    ip = ip_cliente()
    chave = f"{ip}|{email}"

    if not limite_login_ip.permitir(f"ip:{ip}"):
        log.warning("login_limitado ip=%s motivo=ip", ip)
        return jsonify({
            "sucesso": False,
            "mensagem": "Muitas tentativas de login. Aguarde alguns minutos."
        }), 429

    if not limite_login.permitir(chave):
        log.warning("login_limitado ip=%s email=%s", ip, email)
        return jsonify({
            "sucesso": False,
            "mensagem": "Muitas tentativas de login. Aguarde alguns minutos."
        }), 429

    usuario = buscar_usuario_por_email(email)

    if usuario is None:
        check_password_hash(_HASH_FICTICIO, senha)
        log.warning("login_falha ip=%s email=%s motivo=inexistente", ip, email)
        return jsonify({
            "sucesso": False,
            "mensagem": "E-mail ou senha inválidos."
        }), 401

    try:
        senha_correta = bool(usuario.get("senha")) and check_password_hash(
            usuario["senha"], senha
        )
    except Exception:
        log.exception("login_erro_hash email=%s", email)
        senha_correta = False

    if not senha_correta:
        log.warning("login_falha ip=%s email=%s motivo=senha", ip, email)
        return jsonify({
            "sucesso": False,
            "mensagem": "E-mail ou senha inválidos."
        }), 401

    if usuario.get("status") == "Inativo":
        log.warning("login_bloqueado ip=%s email=%s motivo=inativo", ip, email)
        return jsonify({
            "sucesso": False,
            "mensagem": "Conta inativa. Procure a biblioteca."
        }), 403

    limite_login.liberar(chave)

    session.clear()
    session.permanent = True
    session["usuario_id"] = usuario["id"]
    session["usuario_nome"] = usuario["nome"]
    session["usuario_email"] = usuario["email"]
    session["usuario_perfil"] = usuario.get("perfil") or "Usuário"

    try:
        from models import Auditoria
        Auditoria.registrar(
            "Login no sistema",
            {"email": email},
            usuario["nome"],
        )
    except Exception:
        log.exception("auditoria_login_falhou")

    rotulos_perfil = {
        "Administrador": "Administrador",
        "Bibliotecário": "Bibliotecário",
        "Usuário": "Leitor",
    }
    perfil = usuario.get("perfil") or "Usuário"
    tipo = usuario.get("tipo_usuario")
    rotulo = rotulos_perfil.get(perfil, perfil)

    return jsonify({
        "sucesso": True,
        "mensagem": f"Bem-vindo, {usuario['nome']}! Você é {rotulo}.",
        "usuario": {
            "id": usuario["id"],
            "nome": usuario["nome"],
            "email": usuario["email"],
            "perfil": perfil,
            "tipo_usuario": tipo,
        }
    }), 200


# ============================================================
# CADASTRO
# ============================================================

@app.route('/recuperar-senha')
def recuperar_senha_page():
    return render_template('recuperar-senha.html')

@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():

    if request.method == "GET":
        return render_template("cadastro.html")

    ip = ip_cliente()
    if not limite_cadastro.permitir(f"ip:{ip}"):
        log.warning("cadastro_limitado ip=%s", ip)
        return jsonify({
            "sucesso": False,
            "mensagem": "Muitas tentativas de cadastro. Tente novamente mais tarde."
        }), 429

    def _campo(nome_campo):
        return (limpar_texto(request.form.get(nome_campo, "")) or "").strip()

    nome = _campo("nome")
    cpf = request.form.get("cpf", "").strip()
    data_nascimento = request.form.get("data_nascimento", "").strip()
    email = _campo("email").lower()
    telefone = request.form.get("telefone", "").strip()
    matricula = request.form.get("matricula", "").strip()
    curso = _campo("curso")
    tipo_usuario = request.form.get("tipo_usuario", "").strip()
    senha = request.form.get("senha", "")

    if len(nome) < 3:
        return jsonify({"sucesso": False, "mensagem": "Informe seu nome completo."}), 400

    if len(nome) > 150:
        return jsonify({"sucesso": False, "mensagem": "O nome é muito longo."}), 400

    cpf_digitos = "".join(ch for ch in cpf if ch.isdigit())
    if len(cpf_digitos) != 11 or len(set(cpf_digitos)) == 1:
        return jsonify({"sucesso": False, "mensagem": "CPF inválido."}), 400

    if not validar_email(email):
        return jsonify({"sucesso": False, "mensagem": "E-mail inválido."}), 400

    try:
        nascimento = date.fromisoformat(data_nascimento)
    except ValueError:
        return jsonify({"sucesso": False, "mensagem": "Data de nascimento inválida."}), 400

    if nascimento > date.today():
        return jsonify({"sucesso": False, "mensagem": "Data de nascimento inválida."}), 400

    telefone_digitos = "".join(ch for ch in telefone if ch.isdigit())
    if len(telefone_digitos) not in (10, 11):
        return jsonify({"sucesso": False, "mensagem": "Telefone inválido."}), 400

    tipos_permitidos = ["Aluno", "Professor", "Servidor", "Outro"]
    if tipo_usuario not in tipos_permitidos:
        return jsonify({"sucesso": False, "mensagem": "Tipo de usuário inválido para cadastro público."}), 400

    if matricula and (not matricula.isdigit() or len(matricula) > 20):
        return jsonify({"sucesso": False, "mensagem": "Matrícula inválida."}), 400

    if len(curso) > 150:
        return jsonify({"sucesso": False, "mensagem": "O curso é muito longo."}), 400

    if tipo_usuario in ["Aluno", "Professor"]:
        if not matricula:
            return jsonify({"sucesso": False, "mensagem": "A matrícula é obrigatória."}), 400
        if not curso:
            return jsonify({"sucesso": False, "mensagem": "O curso é obrigatório."}), 400
    elif tipo_usuario == "Servidor":
        if not matricula:
            return jsonify({"sucesso": False, "mensagem": "A matrícula funcional é obrigatória."}), 400

    erro_senha = validar_senha_forte(senha)
    if erro_senha:
        return jsonify({"sucesso": False, "mensagem": erro_senha}), 400

    if buscar_usuario_por_email(email):
        return jsonify({"sucesso": False, "mensagem": "Este e-mail já está cadastrado."}), 409

    if buscar_usuario_por_cpf(cpf_digitos):
        return jsonify({"sucesso": False, "mensagem": "Este CPF já está cadastrado."}), 409

    if matricula and buscar_usuario_por_matricula(matricula):
        return jsonify({"sucesso": False, "mensagem": "Esta matrícula já está cadastrada."}), 409

    senha_hash = generate_password_hash(senha, method="scrypt")

    try:
        cadastrar_usuario(
            nome=nome,
            cpf=cpf_digitos,
            data_nascimento=nascimento.isoformat(),
            email=email,
            telefone=telefone_digitos,
            matricula=matricula or None,
            curso=curso or None,
            tipo_usuario=tipo_usuario,
            senha=senha_hash,
            perfil="Usuário",
        )
    except Exception as erro:
        print(f"Erro ao cadastrar usuário: {erro}")
        return jsonify({"sucesso": False, "mensagem": "Não foi possível realizar o cadastro."}), 500

    return jsonify({
        "sucesso": True,
        "mensagem": f"Cadastro realizado com sucesso! Sua conta foi criada como \"{tipo_usuario}\" com perfil de Leitor. Faça login para acessar.",
    }), 200


# ============================================================
# SISTEMA / DASHBOARD
# ============================================================

@app.route("/sistema")
@requer_login
def sistema():
    return render_template("dashboard.html")

# consulta publica

@app.route("/catalogo")
def catalogo_publico():
    return render_template("catalogo.html")

@app.route("/consulta")
def consulta_publica():
    return render_template("consulta.html")


# ============================================================
# LOGOUT
# ============================================================

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ============================================================
# OUTRAS PÁGINAS (protegidas)
# ============================================================

_PAGINAS = {
    "emprestimos": "emprestimos.html",
    "usuarios": "usuarios.html",
    "reservas": "reservas.html",
    "relatorios": "relatorios.html",
    "historico": "historico.html",
    "devolucoes": "devolucoes.html",
    "livros": "livros.html",
    "notificacoes": "notificacoes.html",
    "meu-perfil": "meu-perfil.html",
    "servicos": "servicos.html",
    "auditoria": "auditoria.html",
    "sobre": "sobre.html",
}

# Páginas restritas por perfil (além de exigirem login).
_PAGINAS_RESTRITAS = {
    "livros": ("Administrador", "Bibliotecário"),
    "usuarios": ("Administrador", "Bibliotecário"),
    "emprestimos": ("Administrador", "Bibliotecário"),
    "devolucoes": ("Administrador", "Bibliotecário"),
    "relatorios": ("Administrador", "Bibliotecário"),
    "auditoria": ("Administrador",),
}


def _registrar_paginas():
    for rota, template in _PAGINAS.items():
        def view(template=template, rota=rota):
            perfis = _PAGINAS_RESTRITAS.get(rota)
            if perfis and session.get("usuario_perfil") not in perfis:
                return redirect(url_for("sistema"))
            return render_template(template)
        view = requer_login(view)
        view.__name__ = "pagina_" + rota.replace("-", "_").replace("ç", "c")
        app.add_url_rule(
            "/" + rota,
            endpoint=view.__name__,
            view_func=view,
            methods=["GET"],
        )


_registrar_paginas()


# ============================================================
# COMPATIBILIDADE DE ROTAS ANTIGAS
# ============================================================

@app.route("/home")
def home():
    return redirect("/")


@app.route("/index")
def index_page():
    return redirect("/")


@app.route("/dashboard")
def dashboard():
    return redirect("/sistema")


@app.route("/<string:pagina>.html")
def pagina_html(pagina):
    """Redireciona URLs antigas como /dashboard.html para a rota correta."""
    if pagina == "dashboard":
        return redirect("/sistema")
    if pagina == "home":
        return redirect("/")
    if pagina == "index":
        return redirect("/")
    if pagina in _PAGINAS:
        return redirect("/" + pagina)
    return redirect("/")


# ============================================================
# APIS (sempre JSON)
# ============================================================

@app.route("/api/usuario")
def api_usuario():
    if not usuario_logado():
        return jsonify({
            "sucesso": False,
            "erro": "Não autenticado."
        }), 401

    usuario = buscar_usuario_por_id(session["usuario_id"])

    if usuario is None:
        session.clear()
        return jsonify({"sucesso": False, "erro": "Usuário não encontrado."}), 404

    if usuario.get("status") == "Inativo":
        session.clear()
        return jsonify({"sucesso": False, "erro": "Conta inativa."}), 401

    session["usuario_perfil"] = usuario.get("perfil") or "Usuário"

    return jsonify({
        "sucesso": True,
        "usuario": {
            "id": usuario["id"],
            "nome": usuario["nome"],
            "email": usuario["email"],
            "perfil": usuario.get("perfil"),
            "tipo_usuario": usuario.get("tipo_usuario"),
            "status": usuario.get("status"),
        }
    }), 200


@app.route("/api/dashboard")
def api_dashboard():
    if not usuario_logado():
        return jsonify({
            "sucesso": False,
            "erro": "Não autenticado."
        }), 401

    usuario = buscar_usuario_por_id(session["usuario_id"])
    if not usuario or usuario.get("perfil") not in ("Administrador", "Bibliotecário"):
        return jsonify({
            "sucesso": False,
            "erro": "Acesso restrito à equipe da biblioteca."
        }), 403

    try:
        dados = dados_dashboard()
    except Exception as erro:
        print(f"Erro ao carregar dashboard: {erro}")
        return jsonify({
            "sucesso": False,
            "erro": "Erro ao carregar os dados do dashboard."
        }), 500

    return jsonify({
        "sucesso": True,
        "dados": dados
    }), 200


# ============================================================
# TRATAMENTO DE ERRO 404
# ============================================================

@app.errorhandler(404)
def pagina_nao_encontrada(erro):
    if request.path.startswith("/api/"):
        return jsonify({
            "sucesso": False,
            "erro": "Recurso não encontrado."
        }), 404

    return """
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <title>Página não encontrada</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background: #f5f7fa;
                display: flex;
                align-items: center;
                justify-content: center;
                min-height: 100vh;
                margin: 0;
            }

            .box {
                background: white;
                padding: 40px;
                border-radius: 12px;
                text-align: center;
                box-shadow: 0 10px 30px rgba(0,0,0,.08);
            }

            h1 {
                margin-top: 0;
            }

            a {
                color: #2563eb;
                text-decoration: none;
                font-weight: bold;
            }
        </style>
    </head>

    <body>
        <div class="box">
            <h1>404</h1>
            <p>A página solicitada não foi encontrada.</p>
            <a href="/">Voltar para o início</a>
        </div>
    </body>
    </html>
    """, 404


# ============================================================
# EXECUTAR SERVIDOR
# ============================================================

if __name__ == "__main__":

    app.run(
        host=os.environ.get("HOST", "127.0.0.1"),
        port=_int_env("PORT", 5000),
        debug=bool_env("FLASK_DEBUG", False),
    )
