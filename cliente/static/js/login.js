document.addEventListener("DOMContentLoaded", function () {

    const form = document.getElementById("loginForm");

    const email = document.getElementById("email");

    const senha = document.getElementById("senha");

    const mensagem = document.getElementById("mensagem");


    form.addEventListener("submit", async function (event) {

        event.preventDefault();

        mensagem.textContent = "";

        mensagem.className = "";


        const dados = new FormData();

        dados.append("email", email.value.trim());

        dados.append("senha", senha.value);


        try {

            const resposta = await fetch("/login", {
                method: "POST",
                body: dados
            });


            const resultado = await resposta.json();


            mensagem.textContent = resultado.mensagem;


            if (resultado.sucesso) {

                mensagem.className = "mensagem-sucesso";

            } else {

                mensagem.className = "mensagem-erro";

            }


        } catch (erro) {

            mensagem.textContent = "Erro ao realizar o login.";

            mensagem.className = "mensagem-erro";

            console.error(erro);

        }

    });

});