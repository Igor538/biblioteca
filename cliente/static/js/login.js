document.addEventListener("DOMContentLoaded", () => {

    const formulario = document.querySelector("#loginForm");
    const mensagem = document.querySelector("#mensagem");

    if (!formulario) {
        console.error("Formulário de login não encontrado.");
        return;
    }

    formulario.addEventListener("submit", async (evento) => {

        evento.preventDefault();

        // ----------------------------------------------------
        // LIMPAR MENSAGEM
        // ----------------------------------------------------

        if (mensagem) {
            mensagem.textContent = "";
            mensagem.className = "";
        }

        // ----------------------------------------------------
        // PEGAR DADOS DO FORMULÁRIO
        // ----------------------------------------------------

        const dados = new FormData(formulario);

        const email = dados.get("email");
        const senha = dados.get("senha");

        // ----------------------------------------------------
        // VALIDAÇÃO NO FRONTEND
        // ----------------------------------------------------

        if (!email || !email.trim()) {

            mostrarMensagem(
                "Informe o e-mail.",
                "mensagem-erro"
            );

            return;
        }

        if (!senha) {

            mostrarMensagem(
                "Informe a senha.",
                "mensagem-erro"
            );

            return;
        }

        // ----------------------------------------------------
        // DESABILITAR BOTÃO
        // ----------------------------------------------------

        const botao = formulario.querySelector(
            'button[type="submit"]'
        );

        if (botao) {
            botao.disabled = true;
        }

        try {

            // ------------------------------------------------
            // ENVIAR LOGIN PARA O FLASK
            // ------------------------------------------------

            const resposta = await fetch("/login", {
                method: "POST",
                body: dados
            });

            // ------------------------------------------------
            // VERIFICAR RESPOSTA HTTP
            // ------------------------------------------------

            if (!resposta.ok) {

                throw new Error(
                    `Erro HTTP: ${resposta.status}`
                );
            }

            // ------------------------------------------------
            // CONVERTER RESPOSTA PARA JSON
            // ------------------------------------------------

            const resultado = await resposta.json();

            // ------------------------------------------------
            // LOGIN CORRETO
            // ------------------------------------------------

            if (resultado.sucesso) {

                mostrarMensagem(
                    resultado.mensagem,
                    "mensagem-sucesso"
                );

                /*
                 * IMPORTANTE:
                 *
                 * Depois do login o usuário vai para:
                 *
                 * /sistema
                 *
                 * Essa rota existe no app.py.
                 */

                setTimeout(() => {
                    window.location.href = "/sistema";
                }, 300);

            }

            // ------------------------------------------------
            // LOGIN INCORRETO
            // ------------------------------------------------

            else {

                mostrarMensagem(
                    resultado.mensagem,
                    "mensagem-erro"
                );

            }

        }

        // ----------------------------------------------------
        // ERRO DE COMUNICAÇÃO
        // ----------------------------------------------------

        catch (erro) {

            console.error(
                "Erro ao realizar login:",
                erro
            );

            mostrarMensagem(
                "Erro ao realizar o login. Verifique se o servidor está funcionando.",
                "mensagem-erro"
            );

        }

        // ----------------------------------------------------
        // REATIVAR BOTÃO
        // ----------------------------------------------------

        finally {

            if (botao) {
                botao.disabled = false;
            }

        }

    });


    // ========================================================
    // FUNÇÃO PARA MOSTRAR MENSAGEM
    // ========================================================

    function mostrarMensagem(texto, classe) {

        if (!mensagem) {
            return;
        }

        mensagem.textContent = texto;
        mensagem.className = classe;
    }

});
