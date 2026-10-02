let resultadoBusca = [];
let paginaConsulta = 1;
const POR_PAGINA_CONSULTA = 12;

document.addEventListener('DOMContentLoaded', function () {
        setupBusca();
    setupDetalheModal();
});

function setupBusca() {
    const input = document.getElementById('searchTermo');
    const btn = document.getElementById('btnBuscar');
    const campo = document.getElementById('campoBusca');

    function executar() {
        const termo = input.value.trim();
        if (!termo) {
            showToast('Digite um termo para buscar.', 'warning');
            return;
        }
        paginaConsulta = 1;
        realizarBusca(termo, campo.value);
    }

    btn.addEventListener('click', executar);
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') executar();
    });
}

function realizarBusca(termo, campo) {
    showLoading();
    const grid = document.getElementById('consultaGrid');
    grid.innerHTML = '';

    const params = new URLSearchParams({ q: termo });
    if (campo) params.set('campo', campo);

    API.get(`/api/busca?${params.toString()}`)
        .then(data => {
            resultadoBusca = data.resultados || [];
            const contagem = document.getElementById('consultaContagem');
            if (contagem) {
                contagem.textContent = `${resultadoBusca.length} ${pluralizar(resultadoBusca.length, 'obra encontrada', 'obras encontradas')}`;
            }
            renderizarResultados();
        })
        .catch(err => {
            grid.innerHTML = `<div class="card" style="grid-column:1/-1;padding:40px;text-align:center;color:var(--oxblood)">Erro na busca: ${escapeHtml(err.message)}</div>`;
            const contagem = document.getElementById('consultaContagem');
            if (contagem) contagem.textContent = '';
        })
        .finally(() => hideLoading());
}

function renderizarResultados() {
    const grid = document.getElementById('consultaGrid');
    grid.innerHTML = '';

    if (resultadoBusca.length === 0) {
        grid.innerHTML = '<div class="card" style="grid-column:1/-1;padding:40px;text-align:center;color:var(--ink-faint)">Nenhum resultado encontrado.</div>';
        return;
    }

    const totalPaginas = Math.max(1, Math.ceil(resultadoBusca.length / POR_PAGINA_CONSULTA));
    if (paginaConsulta > totalPaginas) paginaConsulta = totalPaginas;
    const pagina = paginar(resultadoBusca, paginaConsulta, POR_PAGINA_CONSULTA);

    const usuario = Sessao.usuario;
    const podeReservar = usuario && usuario.perfil === 'Usuário';

    pagina.forEach(livro => {
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
                <button class="btn btn-sm btn-secondary" onclick="verDetalheConsulta(${livro.id})" title="Ver detalhes">
                    <svg class="ic" aria-hidden="true"><use href="#i-eye"></use></svg> Detalhes
                </button>
                ${podeReservar ? `
                    <a class="btn btn-sm btn-primary" href="/reservas?livro=${livro.id}" title="Reservar">
                        <svg class="ic" aria-hidden="true"><use href="#i-reserve"></use></svg> Reservar
                    </a>
                ` : ''}
            </div>
        `;
        grid.appendChild(card);
    });

    criarPaginacao('consultaPaginacao', paginaConsulta, totalPaginas, p => {
        paginaConsulta = p;
        renderizarResultados();
    });
}

function verDetalheConsulta(id) {
    const livro = resultadoBusca.find(l => l.id === id);
    if (!livro) return;

    const st = statusLivro(livro);
    const body = document.getElementById('detalheConsultaBody');
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
    abrirModal('detalheConsultaModal');
}

function setupDetalheModal() {
    const modal = document.getElementById('detalheConsultaModal');
    modal.querySelectorAll('.modal-close, .modal-close-btn').forEach(btn => {
        btn.addEventListener('click', () => fecharModal('detalheConsultaModal'));
    });
    modal.addEventListener('click', (e) => {
        if (e.target === modal) fecharModal('detalheConsultaModal');
    });
}
