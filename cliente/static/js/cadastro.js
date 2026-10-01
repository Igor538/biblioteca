document.addEventListener("DOMContentLoaded", function () {

    const form = document.getElementById("cadastroForm");

    const nome = document.getElementById("nome");
    const cpf = document.getElementById("cpf");
    const dataNascimento = document.getElementById("data_nascimento");
    const email = document.getElementById("email");
    const telefone = document.getElementById("telefone");
    const matricula = document.getElementById("matricula");
    const curso = document.getElementById("curso");
    const tipoUsuario = document.getElementById("tipo_usuario");
    const senha = document.getElementById("senha");
    const confirmarSenha = document.getElementById("confirmar_senha");

    const mensagem = document.getElementById("mensagem");


    // ==========================================
    // MÁSCARA DE CPF
    // Exemplo: 123.456.789-00
    // ==========================================

    cpf.addEventListener("input", function () {

        let valor = cpf.value.replace(/\D/g, "");

        valor = valor.substring(0, 11);

        if (valor.length > 9) {

            valor =
                valor.substring(0, 3) + "." +
                valor.substring(3, 6) + "." +
                valor.substring(6, 9) + "-" +
                valor.substring(9, 11);

        } else if (valor.length > 6) {

            valor =
                valor.substring(0, 3) + "." +
                valor.substring(3, 6) + "." +
                valor.substring(6);

        } else if (valor.length > 3) {

            valor =
                valor.substring(0, 3) + "." +
                valor.substring(3);

        }

        cpf.value = valor;

    });


    // ==========================================
    // MÁSCARA DE TELEFONE
    // Exemplo: (19) 99999-9999
    // ==========================================

    telefone.addEventListener("input", function () {

        let valor = telefone.value.replace(/\D/g, "");

        valor = valor.substring(0, 11);

        if (valor.length > 10) {

            valor =
                "(" +
                valor.substring(0, 2) +
                ") " +
                valor.substring(2, 7) +
                "-" +
                valor.substring(7, 11);

        } else if (valor.length > 6) {

            valor =
                "(" +
                valor.substring(0, 2) +
                ") " +
                valor.substring(2, 6) +
                "-" +
                valor.substring(6);

        } else if (valor.length > 2) {

            valor =
                "(" +
                valor.substring(0, 2) +
                ") " +
                valor.substring(2);

        } else if (valor.length > 0) {

            valor = "(" + valor;

        }

        telefone.value = valor;

    });


    // ==========================================
    // MATRÍCULA
    // Permite somente números
    // ==========================================

    matricula.addEventListener("input", function () {

        matricula.value = matricula.value.replace(/\D/g, "");

    });


    // ==========================================
    // ENVIO DO FORMULÁRIO
    // ==========================================

    form.addEventListener("submit", async function (event) {

        event.preventDefault();

        mensagem.textContent = "";
        mensagem.className = "";


        const nomeValor = nome.value.trim();
        const cpfValor = cpf.value.trim();
        const dataNascimentoValor = dataNascimento.value;
        const emailValor = email.value.trim();
        const telefoneValor = telefone.value.trim();
        const matriculaValor = matricula.value.trim();
        const cursoValor = curso.value.trim();
        const tipoUsuarioValor = tipoUsuario.value;
        const senhaValor = senha.value;
        const confirmarSenhaValor = confirmarSenha.value;


        // ==========================================
        // VALIDAÇÕES
        // ==========================================

        if (nomeValor.length < 3) {

            mensagem.textContent = "Digite seu nome completo.";
            mensagem.className = "mensagem-erro";

            nome.focus();

            return;
        }


        const cpfNumeros = cpfValor.replace(/\D/g, "");

        if (cpfNumeros.length !== 11) {

            mensagem.textContent = "Digite um CPF válido.";
            mensagem.className = "mensagem-erro";

            cpf.focus();

            return;
        }


        if (dataNascimentoValor === "") {

            mensagem.textContent = "Informe sua data de nascimento.";
            mensagem.className = "mensagem-erro";

            dataNascimento.focus();

            return;
        }


        if (!emailValor.includes("@")) {

            mensagem.textContent = "Digite um e-mail válido.";
            mensagem.className = "mensagem-erro";

            email.focus();

            return;
        }


        const telefoneNumeros = telefoneValor.replace(/\D/g, "");

        if (
            telefoneNumeros.length !== 10 &&
            telefoneNumeros.length !== 11
        ) {

            mensagem.textContent = "Digite um telefone válido.";
            mensagem.className = "mensagem-erro";

            telefone.focus();

            return;
        }


        if (matriculaValor.length === 0) {

            mensagem.textContent = "Digite sua matrícula.";
            mensagem.className = "mensagem-erro";

            matricula.focus();

            return;
        }


        if (cursoValor.length === 0) {

            mensagem.textContent = "Digite seu curso.";
            mensagem.className = "mensagem-erro";

            curso.focus();

            return;
        }


        if (tipoUsuarioValor === "") {

            mensagem.textContent = "Selecione quem você é.";
            mensagem.className = "mensagem-erro";

            tipoUsuario.focus();

            return;
        }


        if (senhaValor.length < 6) {

            mensagem.textContent =
                "A senha deve ter pelo menos 6 caracteres.";

            mensagem.className = "mensagem-erro";

            senha.focus();

            return;
        }


        if (senhaValor !== confirmarSenhaValor) {

            mensagem.textContent =
                "As senhas não são iguais.";

            mensagem.className = "mensagem-erro";

            confirmarSenha.focus();

            return;
        }


        // ==========================================
        // ENVIO PARA O FLASK
        // ==========================================

        try {

            const dados = new FormData();


            dados.append(
                "nome",
                nomeValor
            );


            dados.append(
                "cpf",
                cpfNumeros
            );


            dados.append(
                "data_nascimento",
                dataNascimentoValor
            );


            dados.append(
                "email",
                emailValor
            );


            dados.append(
                "telefone",
                telefoneNumeros
            );


            dados.append(
                "matricula",
                matriculaValor
            );


            dados.append(
                "curso",
                cursoValor
            );


            dados.append(
                "tipo_usuario",
                tipoUsuarioValor
            );


            dados.append(
                "senha",
                senhaValor
            );


            const resposta = await fetch("/cadastro", {

                method: "POST",

                body: dados

            });


            const resultado = await resposta.json();


            if (resultado.sucesso) {

                mensagem.textContent =
                    resultado.mensagem;

                mensagem.className =
                    "mensagem-sucesso";

                form.reset();

            } else {

                mensagem.textContent =
                    resultado.mensagem;

                mensagem.className =
                    "mensagem-erro";

            }


        } catch (erro) {

            mensagem.textContent =
                "Erro ao realizar o cadastro.";

            mensagem.className =
                "mensagem-erro";

            console.error(erro);

        }

    });

});