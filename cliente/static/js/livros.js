let todosLivros = [];
let livrosFiltrados = [];
let paginaAtual = 1;
const POR_PAGINA = 12;
let modoGrade = true;

document.addEventListener('DOMContentLoaded', function () {
        carregarLivros();
    setupLivrosModal();
    setupSearch();
    setupCategorias();
});

function isAdmin() {
    const u = Sessao.usuario;
    return u && (u.perfil === 'Administrador' || u.perfil === 'Bibliotecário');
}

function carregarLivros() {
    showLoading();
    skeletonCards(8, 'livrosGrid');

    API.get('/api/livros')
        .then(data => {
            todosLivros = data;
            preencherFiltroCategorias(data);
            aplicarFiltros();
        })
        .catch(err => {
            document.getElementById('livrosGrid').innerHTML =
                `<div class="card" style="grid-column:1/-1;padding:40px;text-align:center;color:var(--oxblood)">` +
                `Erro ao carregar livros: ${escapeHtml(err.message)}</div>`;
        })
        .finally(() => hideLoading());
}

function preencherFiltroCategorias(livros) {
    const select = document.getElementById('filtroCategoria');
    if (!select) return;
    const categorias = [...new Set(livros.map(l => l.categoria).filter(Boolean))].sort();
    const atual = select.value;
    select.innerHTML = '<option value="">Todas as categorias</option>';
    categorias.forEach(c => {
        const opt = document.createElement('option');
        opt.value = c;
        opt.textContent = c;
        select.appendChild(opt);
    });
    if (atual) select.value = atual;
}

function aplicarFiltros() {
    const termo = (document.getElementById('searchLivro').value || '').toLowerCase();
    const categoria = document.getElementById('filtroCategoria').value;
    const status = document.getElementById('filtroStatus').value;

    livrosFiltrados = todosLivros.filter(l => {
        if (termo) {
            const texto = `${l.titulo} ${l.subtitulo || ''} ${l.autor} ${l.isbn} ${l.editora || ''} ${l.assuntos || ''}`.toLowerCase();
            if (!texto.includes(termo)) return false;
        }
        if (categoria && l.categoria !== categoria) return false;
        if (status) {
            const st = statusLivro(l);
            if (st !== status) return false;
        }
        return true;
    });

    const contagem = document.getElementById('livrosContagem');
    if (contagem) {
        contagem.textContent = `${livrosFiltrados.length} ${pluralizar(livrosFiltrados.length, 'obra encontrada', 'obras encontradas')}`;
    }

    paginaAtual = 1;
    renderizarLivros();
}

function renderizarLivros() {
    const totalPaginas = Math.max(1, Math.ceil(livrosFiltrados.length / POR_PAGINA));
    if (paginaAtual > totalPaginas) paginaAtual = totalPaginas;

    const pagina = paginar(livrosFiltrados, paginaAtual, POR_PAGINA);

    if (modoGrade) {
        renderizarGrade(pagina);
    } else {
        renderizarTabela(pagina);
    }

    criarPaginacao('livrosPaginacao', paginaAtual, totalPaginas, p => {
        paginaAtual = p;
        renderizarLivros();
    });
}

function renderizarGrade(livros) {
    const grid = document.getElementById('livrosGrid');
    document.getElementById('livrosTableWrap').style.display = 'none';
    grid.style.display = 'grid';
    grid.innerHTML = '';

    if (livros.length === 0) {
        grid.innerHTML = '<div class="card" style="grid-column:1/-1;padding:40px;text-align:center;color:var(--ink-faint)">Nenhum livro encontrado.</div>';
        return;
    }

    livros.forEach(livro => {
        const st = statusLivro(livro);
        const card = document.createElement('article');
        card.className = 'livro-card';
        card.innerHTML = `
            <div class="livro-card-cap">
                <svg class="ic" aria-hidden="true"><use href="#i-book"></use></svg>
                <span class="livro-card-categoria">${escapeHtml(livro.categoria || 'Sem categoria')}</span>
                <span class="livro-card-status">${getStatusBadge(st)}</span>
            </div>
            <div class="livro-card-body">
                <h4 title="${escapeHtml(livro.titulo)}">${escapeHtml(livro.titulo)}</h4>
                <span class="livro-autor">${escapeHtml(livro.autor)}</span>
                ${livro.subtitulo ? `<span class="livro-autor">${escapeHtml(livro.subtitulo)}</span>` : ''}
                <div class="livro-card-meta">
                    <span>${livro.disponivel} disp.</span>
                    <span>${escapeHtml(livro.localizacao || '—')}</span>
                </div>
            </div>
            <div class="livro-card-acoes">
                <button class="btn btn-sm btn-secondary" onclick="verDetalhes(${livro.id})" title="Ver detalhes">
                    <svg class="ic" aria-hidden="true"><use href="#i-eye"></use></svg> Detalhes
                </button>
                ${isAdmin() ? `
                    <button class="btn btn-sm btn-edit" onclick="editarLivro(${livro.id})" title="Editar" aria-label="Editar livro">
                        <svg class="ic" aria-hidden="true"><use href="#i-edit"></use></svg>
                    </button>
                    <button class="btn btn-sm btn-delete" onclick="excluirLivro(${livro.id})" title="Excluir" aria-label="Excluir livro">
                        <svg class="ic" aria-hidden="true"><use href="#i-trash"></use></svg>
                    </button>
                ` : ''}
            </div>
        `;
        grid.appendChild(card);
    });
}

function renderizarTabela(livros) {
    const grid = document.getElementById('livrosGrid');
    document.getElementById('livrosTableWrap').style.display = '';
    grid.style.display = 'none';
    const tbody = document.getElementById('livrosBody');
    tbody.innerHTML = '';

    if (livros.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="empty-table">Nenhum livro encontrado.</td></tr>';
        return;
    }

    livros.forEach(livro => {
        const st = statusLivro(livro);
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><strong>${escapeHtml(livro.titulo)}</strong></td>
            <td>${escapeHtml(livro.autor)}</td>
            <td>${escapeHtml(livro.categoria || '-')}</td>
            <td>${livro.ano || '-'}</td>
            <td>${livro.quantidade}</td>
            <td>${getStatusBadge(st)}</td>
            <td>
                <button class="btn btn-sm btn-secondary" onclick="verDetalhes(${livro.id})" title="Detalhes" aria-label="Ver detalhes do livro">
                    <svg class="ic" aria-hidden="true"><use href="#i-eye"></use></svg>
                </button>
                ${isAdmin() ? `
                    <button class="btn btn-sm btn-edit" onclick="editarLivro(${livro.id})" title="Editar" aria-label="Editar livro">
                        <svg class="ic" aria-hidden="true"><use href="#i-edit"></use></svg>
                    </button>
                    <button class="btn btn-sm btn-delete" onclick="excluirLivro(${livro.id})" title="Excluir" aria-label="Excluir livro">
                        <svg class="ic" aria-hidden="true"><use href="#i-trash"></use></svg>
                    </button>
                ` : ''}
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function verDetalhes(id) {
    const livro = todosLivros.find(l => l.id === id);
    if (!livro) return;

    const st = statusLivro(livro);
    const body = document.getElementById('detalheLivroBody');
    body.innerHTML = `
        <div style="display:flex;gap:22px;flex-wrap:wrap;margin-bottom:20px">
            <div class="livro-card-cap" style="width:140px;height:190px;flex-shrink:0">
                <svg class="ic" aria-hidden="true"><use href="#i-book"></use></svg>
            </div>
            <div style="flex:1;min-width:220px">
                <h3 style="font-size:1.4rem;margin-bottom:6px">${escapeHtml(livro.titulo)}</h3>
                ${livro.subtitulo ? `<p style="color:var(--ink-soft);margin-bottom:4px">${escapeHtml(livro.subtitulo)}</p>` : ''}
                <p style="margin-bottom:10px">${escapeHtml(livro.autor)}</p>
                ${getStatusBadge(st)}
            </div>
        </div>
        <dl class="info-list">
            <div class="info-item"><dt>ISBN</dt><dd>${escapeHtml(livro.isbn)}</dd></div>
            <div class="info-item"><dt>Editora</dt><dd>${escapeHtml(livro.editora || '-')}</dd></div>
            <div class="info-item"><dt>Local de Publicação</dt><dd>${escapeHtml(livro.local_publicacao || '-')}</dd></div>
            <div class="info-item"><dt>Ano</dt><dd>${livro.ano || '-'}</dd></div>
            <div class="info-item"><dt>Categoria</dt><dd>${escapeHtml(livro.categoria || '-')}</dd></div>
            <div class="info-item"><dt>Localização</dt><dd>${escapeHtml(livro.localizacao || '-')}</dd></div>
            <div class="info-item"><dt>Quantidade</dt><dd>${livro.quantidade}</dd></div>
            <div class="info-item"><dt>Disponíveis</dt><dd>${livro.disponivel}</dd></div>
            <div class="info-item"><dt>Páginas</dt><dd>${livro.numero_paginas || '-'}</dd></div>
            <div class="info-item"><dt>Série</dt><dd>${escapeHtml(livro.serie || '-')}</dd></div>
            <div class="info-item"><dt>Coleção</dt><dd>${escapeHtml(livro.colecao || '-')}</dd></div>
            <div class="info-item"><dt>Volume</dt><dd>${escapeHtml(livro.volume || '-')}</dd></div>
            <div class="info-item"><dt>Assuntos</dt><dd>${escapeHtml(livro.assuntos || '-')}</dd></div>
            <div class="info-item"><dt>Palavras-chave</dt><dd>${escapeHtml(livro.palavras_chave || '-')}</dd></div>
        </dl>
        ${livro.resumo ? `
            <div style="margin-top:18px">
                <p style="font-family:var(--font-mono);font-size:10px;letter-spacing:.14em;text-transform:uppercase;color:var(--ink-faint);margin-bottom:6px">Resumo</p>
                <p style="line-height:1.6;color:var(--ink-soft)">${escapeHtml(livro.resumo)}</p>
            </div>` : ''}
    `;
    abrirModal('detalheLivroModal');
}

function setupLivrosModal() {
    const modal = document.getElementById('livroModal');
    const btnNovo = document.getElementById('btnNovoLivro');
    const form = document.getElementById('livroForm');

    btnNovo.addEventListener('click', () => abrirModalLivro());

    modal.querySelectorAll('.modal-close, .modal-close-btn').forEach(btn => {
        btn.addEventListener('click', () => fecharModal('livroModal'));
    });

    modal.addEventListener('click', (e) => {
        if (e.target === modal) fecharModal('livroModal');
    });

    const detalheModal = document.getElementById('detalheLivroModal');
    if (detalheModal) {
        detalheModal.querySelectorAll('.modal-close, .modal-close-btn').forEach(btn => {
            btn.addEventListener('click', () => fecharModal('detalheLivroModal'));
        });
        detalheModal.addEventListener('click', (e) => {
            if (e.target === detalheModal) fecharModal('detalheLivroModal');
        });
    }

    form.addEventListener('submit', function (e) {
        e.preventDefault();
        const livroId = document.getElementById('livroId').value;
        const dados = {
            titulo: document.getElementById('titulo').value,
            subtitulo: document.getElementById('subtitulo').value,
            autor: document.getElementById('autor').value,
            editora: document.getElementById('editora').value,
            local_publicacao: document.getElementById('local_publicacao').value,
            isbn: document.getElementById('isbn').value,
            ano: parseInt(document.getElementById('ano').value) || null,
            numero_paginas: parseInt(document.getElementById('numero_paginas').value) || null,
            serie: document.getElementById('serie').value,
            colecao: document.getElementById('colecao').value,
            volume: document.getElementById('volume').value,
            assuntos: document.getElementById('assuntos').value,
            palavras_chave: document.getElementById('palavras_chave').value,
            resumo: document.getElementById('resumo').value,
            categoria: document.getElementById('categoria').value,
            localizacao: document.getElementById('localizacao').value,
            quantidade: parseInt(document.getElementById('quantidade').value) || 0,
        };

        showLoading();
        const request = livroId
            ? API.put(`/api/livros/${livroId}`, dados)
            : API.post('/api/livros', dados);

        request
            .then(data => {
                showToast(data.mensagem || 'Operação realizada com sucesso!', 'success');
                fecharModal('livroModal');
                carregarLivros();
            })
            .catch(err => showToast('Erro: ' + err.message, 'error'))
            .finally(() => hideLoading());
    });
}

function abrirModalLivro(livro = null) {
    const form = document.getElementById('livroForm');
    const title = document.getElementById('modalTitle');

    form.reset();
    document.getElementById('livroId').value = '';

    if (livro) {
        title.textContent = 'Editar Livro';
        document.getElementById('livroId').value = livro.id;
        document.getElementById('titulo').value = livro.titulo || '';
        document.getElementById('subtitulo').value = livro.subtitulo || '';
        document.getElementById('autor').value = livro.autor || '';
        document.getElementById('editora').value = livro.editora || '';
        document.getElementById('local_publicacao').value = livro.local_publicacao || '';
        document.getElementById('isbn').value = livro.isbn || '';
        document.getElementById('ano').value = livro.ano || '';
        document.getElementById('numero_paginas').value = livro.numero_paginas || '';
        document.getElementById('serie').value = livro.serie || '';
        document.getElementById('colecao').value = livro.colecao || '';
        document.getElementById('volume').value = livro.volume || '';
        document.getElementById('assuntos').value = livro.assuntos || '';
        document.getElementById('palavras_chave').value = livro.palavras_chave || '';
        document.getElementById('resumo').value = livro.resumo || '';
        document.getElementById('categoria').value = livro.categoria || '';
        document.getElementById('localizacao').value = livro.localizacao || '';
        document.getElementById('quantidade').value = livro.quantidade;
    } else {
        title.textContent = 'Novo Livro';
    }

    abrirModal('livroModal');
}

function editarLivro(id) {
    const livro = todosLivros.find(l => l.id === id);
    if (livro) {
        abrirModalLivro(livro);
    } else {
        showToast('Livro não encontrado.', 'error');
    }
}

async function excluirLivro(id) {
    const livro = todosLivros.find(l => l.id === id);
    const ok = await confirmar(`Excluir a obra "${livro ? livro.titulo : ''}"? Esta ação não pode ser desfeita.`);
    if (!ok) return;

    showLoading();
    API.delete(`/api/livros/${id}`)
        .then(data => {
            showToast(data.mensagem || 'Livro excluído com sucesso!', 'success');
            carregarLivros();
        })
        .catch(err => showToast('Erro: ' + err.message, 'error'))
        .finally(() => hideLoading());
}

function setupSearch() {
    const searchInput = document.getElementById('searchLivro');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(() => aplicarFiltros(), 250));
    }

    const filtroCat = document.getElementById('filtroCategoria');
    const filtroSt = document.getElementById('filtroStatus');
    if (filtroCat) filtroCat.addEventListener('change', aplicarFiltros);
    if (filtroSt) filtroSt.addEventListener('change', aplicarFiltros);

    const btnView = document.getElementById('btnAlternarView');
    if (btnView) {
        btnView.addEventListener('click', function () {
            modoGrade = !modoGrade;
            document.getElementById('viewLabel').textContent = modoGrade ? 'Grade' : 'Tabela';
            renderizarLivros();
        });
    }
}

function setupCategorias() {
    // preenche o select do modal com as categorias existentes, além das padrão
}
