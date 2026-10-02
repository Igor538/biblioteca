document.addEventListener('DOMContentLoaded', async function () {
    const autenticado = await verificarSessao();
    if (!autenticado) return;

    carregarDashboard();
});

async function verificarSessao() {
    try {
        const resposta = await fetch('/api/usuario');
        if (resposta.status === 401) {
            window.location.href = '/login';
            return false;
        }
        return resposta.ok;
    } catch (erro) {
        window.location.href = '/login';
        return false;
    }
}

async function carregarDashboard() {
    showLoading();

    try {
        const resposta = await fetch('/api/dashboard');

        if (resposta.status === 401) {
            window.location.href = '/login';
            return;
        }

        const resultado = await resposta.json();

        if (!resposta.ok || !resultado.sucesso) {
            throw new Error(resultado.erro || 'Erro ao carregar dashboard.');
        }

        const dados = resultado.dados;

        document.getElementById('totalLivros').textContent = dados.totalLivros;
        document.getElementById('totalUsuarios').textContent = dados.totalUsuarios;
        document.getElementById('emprestimosAtivos').textContent = dados.emprestimosAtivos;
        document.getElementById('livrosAtrasados').textContent = dados.livrosAtrasados;
        document.getElementById('reservasAtivas').textContent = dados.reservasAtivas;
        document.getElementById('devolucoesRealizadas').textContent = dados.devolucoesRealizadas;
        document.getElementById('livrosDisponiveis').textContent = dados.livrosDisponiveis;
        document.getElementById('livrosIndisponiveis').textContent = dados.livrosIndisponiveis;
        document.getElementById('usuariosSuspensos').textContent = dados.usuariosSuspensos;

        const alerta = document.getElementById('alertaAtrasados');
        if (dados.livrosAtrasados > 0) {
            alerta.style.display = 'flex';
            document.getElementById('alertaAtrasadosText').innerHTML =
                `<strong>Atenção:</strong> ${dados.livrosAtrasados} empréstimo(s) em atraso. ` +
                `${dados.usuariosSuspensos} usuário(s) suspenso(s) por penalidades.`;
        }

        renderBarChart('chartEmprestimosMes',
            (dados.emprestimosMes || []).map(m => ({ rotulo: m.mes, valor: m.total })),
            { titulo: 'Empréstimos por mês', altura: 230 });

        renderBarChart('chartLivrosTop',
            (dados.livrosMaisEmprestados || []).map(l => ({ rotulo: l.titulo, valor: l.total })),
            { titulo: 'Livros mais emprestados', altura: 230 });

        renderDonutChart('chartAcervo',
            (dados.acervoCategoria || []).map(c => ({ rotulo: c.categoria, valor: c.total })),
            { titulo: 'Acervo por categoria', tamanho: 180 });

        renderDonutChart('chartEmprestimosCategoria',
            (dados.emprestimosCategoria || []).map(c => ({ rotulo: c.categoria, valor: c.total })),
            { titulo: 'Empréstimos por categoria', tamanho: 180 });

        preencherUltimosEmprestimos(dados.ultimosEmprestimos || []);
        preencherAtrasados(dados.livrosAtrasadosLista || []);

    } catch (erro) {
        showToast('Erro ao carregar dashboard: ' + erro.message, 'error');
    } finally {
        hideLoading();
    }
}

function preencherUltimosEmprestimos(emprestimos) {
    const tbody = document.getElementById('emprestimosBody');
    if (!tbody) return;

    tbody.innerHTML = '';

    if (emprestimos.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="empty-table">Nenhum empréstimo registrado.</td></tr>';
        return;
    }

    emprestimos.forEach(e => {
        const hoje = new Date();
        const limite = parseDateOnly(e.data_prevista_devolucao);
        const atrasado = e.status === 'Emprestado' && hoje > limite;
        const status = atrasado ? 'Atrasado' : e.status;

        const tr = document.createElement('tr');
        tr.className = atrasado ? 'row-warning' : '';
        tr.innerHTML = `
            <td>${escapeHtml(e.usuario_nome)}</td>
            <td>${escapeHtml(e.livro_titulo)}</td>
            <td>${formatDate(e.data_emprestimo)}</td>
            <td>${formatDate(e.data_prevista_devolucao)}</td>
            <td>${getStatusBadge(status)}</td>
        `;
        tbody.appendChild(tr);
    });
}

function preencherAtrasados(atrasados) {
    const tbody = document.getElementById('atrasadosBody');
    if (!tbody) return;

    tbody.innerHTML = '';

    if (atrasados.length === 0) {
        tbody.innerHTML = '<tr><td colspan="3" class="empty-table">Nenhum livro em atraso.</td></tr>';
        return;
    }

    atrasados.forEach(e => {
        const tr = document.createElement('tr');
        tr.className = 'row-warning';
        tr.innerHTML = `
            <td><strong>${escapeHtml(e.livro_titulo)}</strong></td>
            <td>${escapeHtml(e.usuario_nome)}</td>
            <td><span class="status-badge status-danger">${e.dias_atraso} dia(s)</span></td>
        `;
        tbody.appendChild(tr);
    });
}
