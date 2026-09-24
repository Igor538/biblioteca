document.addEventListener("DOMContentLoaded", function () {

    const form = document.getElementById("cadastroForm");

    const nome = document.getElementById("nome");
    const cpf = document.getElementById("cpf");
    const dataNascimento = document.getElementById("data_nascimento");
    const email = document.getElementById("email");
    const telefone = document.getElementById("telefone");
    const matricula = document.getElementById("matricula");
    const curso = document.getElementById("curso");
    const setor = document.getElementById("setor");
    const tipoUsuario = document.getElementById("tipo_usuario");
    const senha = document.getElementById("senha");
    const confirmarSenha = document.getElementById("confirmar_senha");

    const mensagem = document.getElementById("mensagem");


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
        const setorValor = setor.value.trim();
        const tipoUsuarioValor = tipoUsuario.value;
        const senhaValor = senha.value;
        const confirmarSenhaValor = confirmarSenha.value;


        if (nomeValor.length < 3) {

            mensagem.textContent = "Digite seu nome completo.";
            mensagem.className = "mensagem-erro";

            nome.focus();

            return;
        }


        if (cpfValor.length === 0) {

            mensagem.textContent = "Digite seu CPF.";
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


        if (telefoneValor.length === 0) {

            mensagem.textContent = "Digite seu telefone.";
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


        if (setorValor.length === 0) {

            mensagem.textContent = "Digite seu setor.";
            mensagem.className = "mensagem-erro";

            setor.focus();

            return;
        }


        if (tipoUsuarioValor === "") {

            mensagem.textContent = "Selecione quem você é.";
            mensagem.className = "mensagem-erro";

            tipoUsuario.focus();

            return;
        }


        if (senhaValor.length < 6) {

            mensagem.textContent = "A senha deve ter pelo menos 6 caracteres.";
            mensagem.className = "mensagem-erro";

            senha.focus();

            return;
        }


        if (senhaValor !== confirmarSenhaValor) {

            mensagem.textContent = "As senhas não são iguais.";
            mensagem.className = "mensagem-erro";

            confirmarSenha.focus();

            return;
        }


        try {

            const dados = new FormData();

            dados.append("nome", nomeValor);
            dados.append("cpf", cpfValor);
            dados.append("data_nascimento", dataNascimentoValor);
            dados.append("email", emailValor);
            dados.append("telefone", telefoneValor);
            dados.append("matricula", matriculaValor);
            dados.append("curso", cursoValor);
            dados.append("setor", setorValor);
            dados.append("tipo_usuario", tipoUsuarioValor);
            dados.append("senha", senhaValor);


            const resposta = await fetch("/cadastro", {
                method: "POST",
                body: dados
            });


            const resultado = await resposta.json();


            if (resultado.sucesso) {

                mensagem.textContent = resultado.mensagem;
                mensagem.className = "mensagem-sucesso";

                form.reset();

            } else {

                mensagem.textContent = resultado.mensagem;
                mensagem.className = "mensagem-erro";
            }


        } catch (erro) {

            mensagem.textContent = "Erro ao realizar o cadastro.";
            mensagem.className = "mensagem-erro";

            console.error(erro);
        }

    });

});