document.addEventListener('DOMContentLoaded', function () {
        document.getElementById('btnAtualizarRelatorios').addEventListener('click', carregarTodos);
    carregarTodos();
});

function carregarTodos() {
    showLoading();
    Promise.all([
        API.get('/api/relatorios/circulacao'),
        API.get('/api/relatorios/livros-mais-emprestados?limite=8'),
        API.get('/api/relatorios/livros-atrasados'),
        API.get('/api/relatorios/usuarios-pendencias'),
        API.get('/api/relatorios/estatisticas-acervo'),
        API.get('/api/relatorios/regras-emprestimo'),
    ])
        .then(([circulacao, topLivros, atrasados, pendencias, acervo, regras]) => {
            renderizarStats(circulacao, atrasados);
            renderizarCharts(circulacao, topLivros);
            renderizarTabelaAtrasados(atrasados);
            renderizarTabelaPendencias(pendencias);
            renderizarTabelaAcervo(acervo);
            renderizarRegras(regras);
        })
        .catch(err => showToast('Erro ao carregar relatórios: ' + err.message, 'error'))
        .finally(() => hideLoading());
}

function renderizarStats(circulacao, atrasados) {
    const grid = document.getElementById('relatoriosStats');
    const porMes = circulacao.por_mes || [];
    const totalEmprestimos6m = porMes.reduce((s, m) => s + (m.emprestimos || 0), 0);
    const totalDevolucoes6m = porMes.reduce((s, m) => s + (m.devolucoes || 0), 0);
    const totalAtrasos = atrasados.length;
    const topCategoria = (circulacao.por_categoria_usuario || [])[0];

    grid.innerHTML = `
        <div class="stat-card"><p class="stat-label">Empréstimos (6m)</p><p class="stat-number">${totalEmprestimos6m}</p></div>
        <div class="stat-card"><p class="stat-label">Devoluções (6m)</p><p class="stat-number">${totalDevolucoes6m}</p></div>
        <div class="stat-card"><p class="stat-label">Em atraso agora</p><p class="stat-number">${totalAtrasos}</p></div>
        <div class="stat-card"><p class="stat-label">Categoria que mais empresta</p><p class="stat-number" style="font-size:1.2rem">${topCategoria ? escapeHtml(topCategoria.categoria) : '—'}</p></div>
    `;
}

function renderizarCharts(circulacao, topLivros) {
    const porMes = (circulacao.por_mes || [])
        .map(m => ({
            rotulo: (m.mes || '--').slice(2),
            valor: m.emprestimos || 0
        }));
    renderBarChart('chartCirculacao', porMes, {
        titulo: 'Empréstimos por mês',
        altura: 230
    });

    const porCategoria = (circulacao.por_categoria_usuario || [])
        .map(c => ({ rotulo: c.categoria, valor: c.total }));
    renderDonutChart('chartCategoria', porCategoria, {
        titulo: 'Empréstimos por categoria',
        tamanho: 200
    });

    const top = (topLivros || []).map((l, i) => ({
        rotulo: l.titulo.length > 18 ? l.titulo.slice(0, 18) + '…' : l.titulo,
        valor: l.total_emprestimos
    }));
    renderBarChart('chartTopLivros', top, {
        titulo: 'Obras mais emprestadas',
        altura: 200
    });
}

function renderizarTabelaAtrasados(dados) {
    const tbody = document.getElementById('atrasadosBody');
    tbody.innerHTML = '';
    if (!dados || dados.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="empty-table">Nenhum empréstimo em atraso. Nenhum item atrasado.</td></tr>';
        return;
    }
    dados.forEach(e => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><strong>${escapeHtml(e.usuario_nome)}</strong><div style="font-size:11px;color:var(--ink-faint);font-family:var(--font-mono)">${escapeHtml(e.usuario_email || '')}</div></td>
            <td>${escapeHtml(e.livro_titulo)}</td>
            <td style="font-family:var(--font-mono);font-size:12px">${formatDate(e.data_emprestimo)}</td>
            <td style="font-family:var(--font-mono);font-size:12px">${formatDate(e.data_prevista_devolucao)}</td>
            <td><span class="status-badge status-danger">${e.dias_atraso} dias</span></td>
        `;
        tbody.appendChild(tr);
    });
}

function renderizarTabelaPendencias(dados) {
    const tbody = document.getElementById('pendenciasBody');
    tbody.innerHTML = '';
    if (!dados || dados.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="empty-table">Nenhum usuário com pendências.</td></tr>';
        return;
    }
    dados.forEach(u => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><strong>${escapeHtml(u.nome)}</strong><div style="font-size:11px;color:var(--ink-faint);font-family:var(--font-mono)">${escapeHtml(u.email || '')}</div></td>
            <td>${getStatusBadge(u.tipo_usuario)}</td>
            <td>${u.emprestimos_ativos}</td>
            <td>${u.atrasos > 0 ? `<span class="status-badge status-danger">${u.atrasos}</span>` : u.atrasos}</td>
            <td>${u.penalidades_ativas > 0 ? `<span class="status-badge status-warning">${u.penalidades_ativas}</span>` : u.penalidades_ativas}</td>
        `;
        tbody.appendChild(tr);
    });
}

function renderizarTabelaAcervo(dados) {
    const tbody = document.getElementById('acervoBody');
    tbody.innerHTML = '';
    if (!dados || dados.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="empty-table">Nenhum dado de acervo.</td></tr>';
        return;
    }
    dados.forEach(c => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><strong>${escapeHtml(c.categoria || 'Sem categoria')}</strong></td>
            <td>${c.total_titulos}</td>
            <td>${c.total_exemplares}</td>
            <td>${c.disponiveis}</td>
            <td>${c.emprestados}</td>
        `;
        tbody.appendChild(tr);
    });
}

function renderizarRegras(dados) {
    const tbody = document.getElementById('regrasBody');
    tbody.innerHTML = '';
    const categorias = dados.categorias || [];
    if (categorias.length === 0) {
        tbody.innerHTML = '<tr><td colspan="3" class="empty-table">Nenhuma regra cadastrada.</td></tr>';
        return;
    }
    categorias.forEach(r => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><strong>${escapeHtml(r.categoria)}</strong></td>
            <td>${r.limite_livros} livros</td>
            <td>${r.prazo_dias} dias</td>
        `;
        tbody.appendChild(tr);
    });
}
