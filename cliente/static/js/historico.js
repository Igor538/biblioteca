let todosHistorico = [];
let historicoFiltrado = [];
let paginaHistorico = 1;
const POR_PAGINA_HISTORICO = 12;
let somenteAtivos = false;

document.addEventListener('DOMContentLoaded', function () {
        const usuario = Sessao.usuario;
    if (usuario && usuario.perfil === 'Usuário') {
        const sub = document.getElementById('historicoSubtitulo');
        if (sub) sub.textContent = 'Seu histórico de empréstimos na biblioteca';
    }
    setupSearch();
    carregarHistorico();
});

function carregarHistorico() {
    showLoading();
    skeletonTabela(7, 8, 'historicoBody');

    API.get('/api/emprestimos/historico')
        .then(data => {
            todosHistorico = data;
            aplicarFiltros();
        })
        .catch(err => showToast('Erro ao carregar histórico: ' + err.message, 'error'))
        .finally(() => hideLoading());
}

function setupSearch() {
    const input = document.getElementById('searchHistorico');
    if (input) {
        input.addEventListener('input', debounce(() => aplicarFiltros(), 250));
    }

    const btn = document.getElementById('btnFiltrarAtivos');
    if (btn) {
        btn.addEventListener('click', () => {
            somenteAtivos = !somenteAtivos;
            btn.classList.toggle('btn-primary', somenteAtivos);
            btn.classList.toggle('btn-secondary', !somenteAtivos);
            btn.textContent = somenteAtivos ? 'Todos os registros' : 'Somente ativos';
            paginaHistorico = 1;
            aplicarFiltros();
        });
    }
}

function aplicarFiltros() {
    const termo = (document.getElementById('searchHistorico').value || '').toLowerCase();

    historicoFiltrado = todosHistorico.filter(e => {
        if (somenteAtivos && e.status !== 'Emprestado') return false;
        if (termo) {
            const texto = `${e.usuario_nome || ''} ${e.livro_titulo || ''}`.toLowerCase();
            if (!texto.includes(termo)) return false;
        }
        return true;
    });

    const totalPaginas = Math.max(1, Math.ceil(historicoFiltrado.length / POR_PAGINA_HISTORICO));
    if (paginaHistorico > totalPaginas) paginaHistorico = totalPaginas;
    const pagina = paginar(historicoFiltrado, paginaHistorico, POR_PAGINA_HISTORICO);
    renderizarHistorico(pagina);

    criarPaginacao('historicoPaginacao', paginaHistorico, totalPaginas, p => {
        paginaHistorico = p;
        aplicarFiltros();
    });
}

function renderizarHistorico(registros) {
    const tbody = document.getElementById('historicoBody');
    tbody.innerHTML = '';

    if (registros.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="empty-table">Nenhum registro encontrado.</td></tr>';
        return;
    }

    registros.forEach(e => {
        const atrasado = e.status === 'Emprestado' && e.dias_atraso > 0;
        const statusBadge = atrasado ? getStatusBadge('Atrasado') : getStatusBadge(e.status);
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><strong>${escapeHtml(e.usuario_nome || '-')}</strong></td>
            <td>${escapeHtml(e.livro_titulo || '-')}</td>
            <td style="font-family:var(--font-mono);font-size:12px">${formatDate(e.data_emprestimo)}</td>
            <td style="font-family:var(--font-mono);font-size:12px">${formatDate(e.data_prevista_devolucao)}</td>
            <td style="font-family:var(--font-mono);font-size:12px">${formatDate(e.data_devolucao)}</td>
            <td>${e.renovacoes || 0}</td>
            <td>${statusBadge}</td>
        `;
        tbody.appendChild(tr);
    });
}
