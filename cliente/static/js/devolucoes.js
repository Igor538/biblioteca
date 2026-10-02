let emprestimosAtivos = [];
let paginaDevolucao = 1;
const POR_PAGINA_DEVOLUCAO = 10;
let devolucaoId = null;

document.addEventListener('DOMContentLoaded', function () {
        carregarEmprestimosAtivos();
    setupDevolucoes();
});

function carregarEmprestimosAtivos() {
    showLoading();
    skeletonTabela(7, 6, 'devolucoesBody');

    API.get('/api/emprestimos/ativos')
        .then(data => {
            emprestimosAtivos = data;
            renderizarAtivos();
        })
        .catch(err => showToast('Erro ao carregar empréstimos: ' + err.message, 'error'))
        .finally(() => hideLoading());
}

function renderizarAtivos() {
    const tbody = document.getElementById('devolucoesBody');
    tbody.innerHTML = '';

    const termo = (document.getElementById('searchEmprestimo').value || '').toLowerCase();
    const filtrados = emprestimosAtivos.filter(e => {
        if (!termo) return true;
        return `${e.usuario_nome} ${e.livro_titulo}`.toLowerCase().includes(termo);
    });

    if (filtrados.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="empty-table">Nenhum empréstimo ativo encontrado.</td></tr>';
        return;
    }

    const totalPaginas = Math.max(1, Math.ceil(filtrados.length / POR_PAGINA_DEVOLUCAO));
    if (paginaDevolucao > totalPaginas) paginaDevolucao = totalPaginas;

    paginar(filtrados, paginaDevolucao, POR_PAGINA_DEVOLUCAO).forEach(e => {
        const atrasado = e.dias_atraso > 0;
        const tr = document.createElement('tr');
        tr.className = atrasado ? 'row-warning' : '';
        tr.innerHTML = `
            <td><strong>${escapeHtml(e.usuario_nome)}</strong></td>
            <td>${escapeHtml(e.livro_titulo)}</td>
            <td>${formatDate(e.data_emprestimo)}</td>
            <td>${formatDate(e.data_prevista_devolucao)}</td>
            <td>${atrasado
                ? `<span class="status-badge status-danger">${e.dias_atraso} dia(s)</span>`
                : `<span class="status-badge status-success">Em dia</span>`}</td>
            <td><span class="status-badge ${atrasado ? 'status-danger' : 'status-warning'}">${atrasado ? 'Atrasado' : 'Emprestado'}</span></td>
            <td>
                <button class="btn btn-sm btn-success" onclick="abrirConfirmacao(${e.id})" aria-label="Devolver livro">
                    <svg class="ic" aria-hidden="true"><use href="#i-return"></use></svg> Devolver
                </button>
            </td>
        `;
        tbody.appendChild(tr);
    });

    criarPaginacao('devolucoesPaginacao', paginaDevolucao, totalPaginas, p => {
        paginaDevolucao = p;
        renderizarAtivos();
    });
}

function abrirConfirmacao(id) {
    const e = emprestimosAtivos.find(x => x.id === id);
    if (!e) return;

    devolucaoId = id;
    document.getElementById('confirmMessage').textContent = `Confirmar devolução do livro "${e.livro_titulo}"?`;
    document.getElementById('devolucaoInfo').innerHTML = `
        <p><strong>Usuário:</strong> ${escapeHtml(e.usuario_nome)}</p>
        <p><strong>Livro:</strong> ${escapeHtml(e.livro_titulo)}</p>
        <p><strong>Data Limite:</strong> ${formatDate(e.data_prevista_devolucao)}</p>
    `;

    const preview = document.getElementById('suspensaoPreview');
    if (e.dias_atraso > 0) {
        const suspensao = e.dias_atraso * 2;
        preview.style.display = 'block';
        document.getElementById('suspensaoPreviewText').innerHTML =
            `<strong>Penalidade:</strong> ${e.dias_atraso} dia(s) de atraso = <strong>${suspensao} dia(s) de suspensão</strong> do usuário.`;
    } else {
        preview.style.display = 'none';
    }

    abrirModal('confirmModal');
}

function setupDevolucoes() {
    document.getElementById('confirmDevolucao').addEventListener('click', function () {
        if (!devolucaoId) return;
        showLoading();
        API.put(`/api/emprestimos/${devolucaoId}`, { acao: 'devolver' })
            .then(data => {
                showToast(data.mensagem || 'Devolução realizada com sucesso!', 'success');
                fecharModal('confirmModal');
                carregarEmprestimosAtivos();
            })
            .catch(err => showToast('Erro: ' + err.message, 'error'))
            .finally(() => hideLoading());
    });

    document.getElementById('searchEmprestimo').addEventListener('input', debounce(() => {
        paginaDevolucao = 1;
        renderizarAtivos();
    }, 250));

    document.querySelectorAll('#confirmModal .modal-close, #confirmModal .modal-close-btn').forEach(el => {
        el.addEventListener('click', () => fecharModal('confirmModal'));
    });

    const modal = document.getElementById('confirmModal');
    modal.addEventListener('click', (e) => {
        if (e.target === modal) fecharModal('confirmModal');
    });
}
