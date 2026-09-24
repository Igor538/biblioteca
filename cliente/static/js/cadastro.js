document.addEventListener("DOMContentLoaded", function () {

    const form = document.getElementById("cadastroForm");

    const nome = document.getElementById("nome");
    const email = document.getElementById("email");
    const senha = document.getElementById("senha");
    const confirmarSenha = document.getElementById("confirmar_senha");

    const mensagem = document.getElementById("mensagem");

    form.addEventListener("submit", async function (event) {

        event.preventDefault();

        mensagem.textContent = "";
        mensagem.className = "";

        const nomeValor = nome.value.trim();
        const emailValor = email.value.trim();
        const senhaValor = senha.value;
        const confirmarSenhaValor = confirmarSenha.value;

        // Validação do nome
        if (nomeValor.length < 3) {

            mensagem.textContent = "Digite seu nome completo.";
            mensagem.className = "mensagem-erro";

            nome.focus();

            return;
        }

        // Validação do e-mail
        if (!emailValor.includes("@")) {

            mensagem.textContent = "Digite um e-mail válido.";
            mensagem.className = "mensagem-erro";

            email.focus();

            return;
        }

        // Validação da senha
        if (senhaValor.length < 6) {

            mensagem.textContent = "A senha deve ter pelo menos 6 caracteres.";
            mensagem.className = "mensagem-erro";

            senha.focus();

            return;
        }

        // Confirmação da senha
        if (senhaValor !== confirmarSenhaValor) {

            mensagem.textContent = "As senhas não são iguais.";
            mensagem.className = "mensagem-erro";

            confirmarSenha.focus();

            return;
        }

        try {

            const dados = new FormData();

            dados.append("nome", nomeValor);
            dados.append("email", emailValor);
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
