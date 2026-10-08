let logsAuditoria = [];
let logsFiltrados = [];
let paginaAuditoria = 1;
const POR_PAGINA_AUDITORIA = 15;

document.addEventListener('DOMContentLoaded', function () {
        document.getElementById('btnExportarBackup').addEventListener('click', exportarBackup);
    setupSearchAuditoria();
    carregarAuditoria();
});

function carregarAuditoria() {
    showLoading();
    skeletonTabela(4, 10, 'auditoriaBody');

    Promise.all([API.get('/api/auditoria'), API.get('/api/backup/estatisticas')])
        .then(([logs, stats]) => {
            logsAuditoria = logs;
            renderizarStats(stats);
            aplicarFiltrosAuditoria();
        })
        .catch(err => showToast('Erro ao carregar auditoria: ' + err.message, 'error'))
        .finally(() => hideLoading());
}

function renderizarStats(stats) {
    const grid = document.getElementById('auditoriaStats');
    const totalRegistros = logsAuditoria.length;
    const totalUsuarios = stats.usuarios || 0;
    const totalLivros = stats.livros || 0;
    const totalEmprestimos = stats.emprestimos || 0;

    grid.innerHTML = `
        <div class="stat-card"><p class="stat-label">Registros de auditoria</p><p class="stat-number">${totalRegistros}</p></div>
        <div class="stat-card"><p class="stat-label">Usuários</p><p class="stat-number">${totalUsuarios}</p></div>
        <div class="stat-card"><p class="stat-label">Livros</p><p class="stat-number">${totalLivros}</p></div>
        <div class="stat-card"><p class="stat-label">Empréstimos</p><p class="stat-number">${totalEmprestimos}</p></div>
    `;
}

function setupSearchAuditoria() {
    const input = document.getElementById('searchAuditoria');
    if (input) {
        input.addEventListener('input', debounce(() => aplicarFiltrosAuditoria(), 250));
    }
}

function aplicarFiltrosAuditoria() {
    const termo = (document.getElementById('searchAuditoria').value || '').toLowerCase();
    logsFiltrados = logsAuditoria.filter(l => {
        if (!termo) return true;
        return `${l.operacao || ''} ${l.usuario_responsavel || ''}`.toLowerCase().includes(termo);
    });

    const totalPaginas = Math.max(1, Math.ceil(logsFiltrados.length / POR_PAGINA_AUDITORIA));
    if (paginaAuditoria > totalPaginas) paginaAuditoria = totalPaginas;
    const pagina = paginar(logsFiltrados, paginaAuditoria, POR_PAGINA_AUDITORIA);
    renderizarLogs(pagina);

    criarPaginacao('auditoriaPaginacao', paginaAuditoria, totalPaginas, p => {
        paginaAuditoria = p;
        aplicarFiltrosAuditoria();
    });
}

function renderizarLogs(logs) {
    const tbody = document.getElementById('auditoriaBody');
    tbody.innerHTML = '';

    if (logs.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" class="empty-table">Nenhum registro encontrado.</td></tr>';
        return;
    }

    logs.forEach(l => {
        let detalhes = '';
        try {
            const dados = JSON.parse(l.dados_afetados || 'null');
            if (dados) {
                detalhes = JSON.stringify(dados).slice(0, 140);
            }
        } catch (e) {
            detalhes = String(l.dados_afetados || '').slice(0, 140);
        }

        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td style="font-family:var(--font-mono);font-size:12px">${formatDate(l.data_hora)}</td>
            <td>${escapeHtml(l.usuario_responsavel || 'Sistema')}</td>
            <td>${getStatusBadge(l.operacao)}</td>
            <td style="max-width:340px;font-family:var(--font-mono);font-size:11.5px;color:var(--ink-soft)">${escapeHtml(detalhes) || '—'}</td>
        `;
        tbody.appendChild(tr);
    });
}

function exportarBackup() {
    const ok = confirmar(
        'Exportar um backup completo do banco de dados (JSON)?',
        'Exportar backup',
        '#i-download'
    );
    ok.then(confirmado => {
        if (!confirmado) return;
        showLoading();
        API.get('/api/backup/exportar')
            .then(data => {
                const blob = new Blob(
                    [JSON.stringify(data.data, null, 2)],
                    { type: 'application/json' }
                );
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `backup-biblioteca-${new Date().toISOString().slice(0, 10)}.json`;
                document.body.appendChild(a);
                a.click();
                a.remove();
                URL.revokeObjectURL(url);
                showToast(data.mensagem || 'Backup exportado com sucesso!', 'success');
            })
            .catch(err => showToast('Erro ao exportar backup: ' + err.message, 'error'))
            .finally(() => hideLoading());
    });
}
