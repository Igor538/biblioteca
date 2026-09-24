from flask import Flask, render_template, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

from database import (
    criar_tabela_usuarios,
    buscar_usuario_por_email,
    buscar_usuario_por_cpf,
    buscar_usuario_por_matricula,
    cadastrar_usuario
)


app = Flask(
    __name__,
    template_folder="../cliente/templates",
    static_folder="../cliente/static"
)


criar_tabela_usuarios()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email", "").strip()
        senha = request.form.get("senha", "")

        if not email or not senha:
            return jsonify({
                "sucesso": False,
                "mensagem": "Informe o e-mail e a senha."
            })

        usuario = buscar_usuario_por_email(email)

        if usuario is None:
            return jsonify({
                "sucesso": False,
                "mensagem": "E-mail ou senha inválidos."
            })

        if not check_password_hash(usuario["senha"], senha):
            return jsonify({
                "sucesso": False,
                "mensagem": "E-mail ou senha inválidos."
            })

        return jsonify({
            "sucesso": True,
            "mensagem": f"Bem-vindo, {usuario['nome']}!"
        })

    return render_template("login.html")


@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():

    if request.method == "POST":

        nome = request.form.get("nome", "").strip()
        cpf = request.form.get("cpf", "").strip()
        data_nascimento = request.form.get("data_nascimento", "").strip()
        email = request.form.get("email", "").strip()
        telefone = request.form.get("telefone", "").strip()
        matricula = request.form.get("matricula", "").strip()
        curso = request.form.get("curso", "").strip()
        setor = request.form.get("setor", "").strip()
        tipo_usuario = request.form.get("tipo_usuario", "").strip()
        senha = request.form.get("senha", "")


        if not nome:
            return jsonify({
                "sucesso": False,
                "mensagem": "O nome é obrigatório."
            })


        if not cpf:
            return jsonify({
                "sucesso": False,
                "mensagem": "O CPF é obrigatório."
            })


        if not data_nascimento:
            return jsonify({
                "sucesso": False,
                "mensagem": "A data de nascimento é obrigatória."
            })


        if not email:
            return jsonify({
                "sucesso": False,
                "mensagem": "O e-mail é obrigatório."
            })


        if not telefone:
            return jsonify({
                "sucesso": False,
                "mensagem": "O telefone é obrigatório."
            })


        if not matricula:
            return jsonify({
                "sucesso": False,
                "mensagem": "A matrícula é obrigatória."
            })


        if not curso:
            return jsonify({
                "sucesso": False,
                "mensagem": "O curso é obrigatório."
            })


        if not setor:
            return jsonify({
                "sucesso": False,
                "mensagem": "O setor é obrigatório."
            })


        if not tipo_usuario:
            return jsonify({
                "sucesso": False,
                "mensagem": "Informe quem você é."
            })


        if len(senha) < 6:
            return jsonify({
                "sucesso": False,
                "mensagem": "A senha deve ter pelo menos 6 caracteres."
            })


        if buscar_usuario_por_email(email):
            return jsonify({
                "sucesso": False,
                "mensagem": "Este e-mail já está cadastrado."
            })


        if buscar_usuario_por_cpf(cpf):
            return jsonify({
                "sucesso": False,
                "mensagem": "Este CPF já está cadastrado."
            })


        if buscar_usuario_por_matricula(matricula):
            return jsonify({
                "sucesso": False,
                "mensagem": "Esta matrícula já está cadastrada."
            })


        senha_hash = generate_password_hash(senha)


        try:

            cadastrar_usuario(
                nome=nome,
                cpf=cpf,
                data_nascimento=data_nascimento,
                email=email,
                telefone=telefone,
                matricula=matricula,
                curso=curso,
                setor=setor,
                tipo_usuario=tipo_usuario,
                senha=senha_hash
            )

        except Exception as erro:

            print(f"Erro ao cadastrar usuário: {erro}")

            return jsonify({
                "sucesso": False,
                "mensagem": "Não foi possível realizar o cadastro."
            })


        return jsonify({
            "sucesso": True,
            "mensagem": "Cadastro realizado com sucesso."
        })


    return render_template("cadastro.html")


if __name__ == "__main__":
    app.run(debug=True)