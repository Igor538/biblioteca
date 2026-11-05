// ===============================
// RECUPERAÇÃO DE SENHA
// ===============================

function senhaForte(senha) {
    if (senha.length < 8) return 'A senha deve ter pelo menos 8 caracteres.';
    if (senha.length > 128) return 'A senha deve ter no máximo 128 caracteres.';
    if (!/[A-Za-zÀ-ÿ]/.test(senha)) return 'A senha deve conter pelo menos uma letra.';
    if (!/\d/.test(senha)) return 'A senha deve conter pelo menos um número.';
    return null;
}

document.addEventListener('DOMContentLoaded', function () {
    const params = new URLSearchParams(window.location.search);
    const token = params.get('token');
    const mensagem = document.getElementById('mensagem');
    const formEmail = document.getElementById('formEmail');
    const formReset = document.getElementById('formReset');

    if (token) {
        formEmail.style.display = 'none';
        formReset.style.display = 'block';
    }

    function mostrar(texto, sucesso) {
        mensagem.textContent = texto;
        mensagem.className = sucesso ? 'mensagem-sucesso' : 'mensagem-erro';
    }

    document.getElementById('btnEnviar').addEventListener('click', async () => {
        const email = document.getElementById('email').value.trim();
        mensagem.textContent = '';
        mensagem.className = '';

        if (!email) {
            mostrar('Informe o e-mail.', false);
            return;
        }

        try {
            const data = await API.post('/api/esqueceu-senha', { email });
            mostrar(
                data.mensagem || 'Se o e-mail estiver cadastrado, enviaremos instruções.',
                true
            );
        } catch (erro) {
            mostrar(erro.message || 'Erro ao processar a solicitação.', false);
        }
    });

    if (token) {
        document.getElementById('btnResetar').addEventListener('click', async () => {
            const senha = document.getElementById('novaSenha').value;
            const erroSenha = senhaForte(senha);

            if (erroSenha) {
                mostrar(erroSenha, false);
                return;
            }

            try {
                const data = await API.post('/api/redefinir-senha', { token, senha });
                mostrar(data.mensagem || 'Senha redefinida com sucesso.', true);
                setTimeout(() => { window.location.href = '/login'; }, 3000);
            } catch (erro) {
                mostrar(erro.message || 'Não foi possível redefinir a senha.', false);
            }
        });
    }
});
