import sys
from functools import wraps
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from flask import (
    Flask,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import generate_password_hash, check_password_hash

from database import (
    criar_tabela_usuarios,
    buscar_usuario_por_email,
    buscar_usuario_por_cpf,
    buscar_usuario_por_matricula,
    buscar_usuario_por_id,
    cadastrar_usuario,
    dados_dashboard,
)

# ============================================================
# CONFIGURAÇÃO DO FLASK
# ============================================================

app = Flask(
    __name__,
    template_folder="../cliente/templates",
    static_folder="../cliente/static"
)

app.secret_key = "biblioteca-chave-secreta-trocar-em-producao"


# ============================================================
# INICIALIZAÇÃO DO BANCO
# ============================================================

from database import inicializar_banco
inicializar_banco()
criar_tabela_usuarios()

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

    email = request.form.get("email", "").strip()
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

    usuario = buscar_usuario_por_email(email)

    if usuario is None:
        return jsonify({
            "sucesso": False,
            "mensagem": "E-mail ou senha inválidos."
        }), 401

    try:
        senha_correta = check_password_hash(usuario["senha"], senha)
    except Exception as erro:
        print(f"Erro ao verificar senha: {erro}")
        return jsonify({
            "sucesso": False,
            "mensagem": "Erro ao verificar o login."
        }), 500

    if not senha_correta:
        return jsonify({
            "sucesso": False,
            "mensagem": "E-mail ou senha inválidos."
        }), 401

    session.clear()
    session["usuario_id"] = usuario["id"]
    session["usuario_nome"] = usuario["nome"]
    session["usuario_email"] = usuario["email"]

    rotulos_perfil = {
        "Administrador": "Administrador",
        "Bibliotecário": "Bibliotecário",
        "Usuário": "Leitor",
    }
    perfil = usuario["perfil"] if "perfil" in usuario.keys() else "Usuário"
    tipo = usuario["tipo_usuario"] if "tipo_usuario" in usuario.keys() else None
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

@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():

    if request.method == "GET":
        return render_template("cadastro.html")

    nome = request.form.get("nome", "").strip()
    cpf = request.form.get("cpf", "").strip()
    data_nascimento = request.form.get("data_nascimento", "").strip()
    email = request.form.get("email", "").strip()
    telefone = request.form.get("telefone", "").strip()
    matricula = request.form.get("matricula", "").strip()
    curso = request.form.get("curso", "").strip()
    tipo_usuario = request.form.get("tipo_usuario", "").strip()
    senha = request.form.get("senha", "")

    if not nome:
        return jsonify({"sucesso": False, "mensagem": "O nome é obrigatório."}), 400

    if not cpf:
        return jsonify({"sucesso": False, "mensagem": "O CPF é obrigatório."}), 400

    if not data_nascimento:
        return jsonify({"sucesso": False, "mensagem": "A data de nascimento é obrigatória."}), 400

    if not email:
        return jsonify({"sucesso": False, "mensagem": "O e-mail é obrigatório."}), 400

    if not telefone:
        return jsonify({"sucesso": False, "mensagem": "O telefone é obrigatório."}), 400

    if not tipo_usuario:
        return jsonify({"sucesso": False, "mensagem": "Informe quem você é."}), 400

    tipos_permitidos = ["Aluno", "Professor", "Servidor", "Outro"]
    if tipo_usuario not in tipos_permitidos:
        return jsonify({"sucesso": False, "mensagem": "Tipo de usuário inválido para cadastro público."}), 400

    if tipo_usuario in ["Aluno", "Professor"]:
        if not matricula:
            return jsonify({"sucesso": False, "mensagem": "A matrícula é obrigatória."}), 400
        if not curso:
            return jsonify({"sucesso": False, "mensagem": "O curso é obrigatório."}), 400
    elif tipo_usuario == "Servidor":
        if not matricula:
            return jsonify({"sucesso": False, "mensagem": "A matrícula funcional é obrigatória."}), 400

    if not senha:
        return jsonify({"sucesso": False, "mensagem": "A senha é obrigatória."}), 400

    if len(senha) < 6:
        return jsonify({"sucesso": False, "mensagem": "A senha deve ter pelo menos 6 caracteres."}), 400

    if buscar_usuario_por_email(email):
        return jsonify({"sucesso": False, "mensagem": "Este e-mail já está cadastrado."}), 409

    if buscar_usuario_por_cpf(cpf):
        return jsonify({"sucesso": False, "mensagem": "Este CPF já está cadastrado."}), 409

    if matricula and buscar_usuario_por_matricula(matricula):
        return jsonify({"sucesso": False, "mensagem": "Esta matrícula já está cadastrada."}), 409

    senha_hash = generate_password_hash(senha)

    try:
        cadastrar_usuario(
            nome=nome,
            cpf=cpf,
            data_nascimento=data_nascimento,
            email=email,
            telefone=telefone,
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
    "consulta": "consulta.html",
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


def _registrar_paginas():
    for rota, template in _PAGINAS.items():
        def view(template=template):
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

    return jsonify({
        "sucesso": True,
        "usuario": {
            "id": usuario["id"],
            "nome": usuario["nome"],
            "email": usuario["email"],
            "perfil": usuario["perfil"] if "perfil" in usuario.keys() else None,
            "tipo_usuario": usuario["tipo_usuario"] if "tipo_usuario" in usuario.keys() else None,
        }
    }), 200


@app.route("/api/dashboard")
def api_dashboard():
    if not usuario_logado():
        return jsonify({
            "sucesso": False,
            "erro": "Não autenticado."
        }), 401

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
        host="127.0.0.1",
        port=5000,
        debug=True
    )
