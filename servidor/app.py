from flask import Flask, render_template, request, redirect, url_for, jsonify

app = Flask(
    __name__,
    template_folder="../cliente/templates",
    static_folder="../cliente/static"
)

usuarios = []


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        senha = request.form.get("senha")

        for usuario in usuarios:
            if usuario["email"] == email and usuario["senha"] == senha:
                return jsonify({
                    "sucesso": True,
                    "mensagem": f"Bem-vindo, {usuario['nome']}!"
                })

        return jsonify({
            "sucesso": False,
            "mensagem": "E-mail ou senha inválidos."
        })

    return render_template("login.html")


@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if request.method == "POST":
        nome = request.form.get("nome")
        email = request.form.get("email")
        senha = request.form.get("senha")

        for usuario in usuarios:
            if usuario["email"] == email:
                return jsonify({
                    "sucesso": False,
                    "mensagem": "Este e-mail já está cadastrado."
                })

        usuarios.append({
            "nome": nome,
            "email": email,
            "senha": senha
        })

        return jsonify({
            "sucesso": True,
            "mensagem": "Cadastro realizado com sucesso."
        })

    return render_template("cadastro.html")