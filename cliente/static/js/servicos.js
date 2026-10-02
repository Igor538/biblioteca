let todasSolicitacoes = [];
let solicitacoesFiltradas = [];
let paginaServico = 1;
const POR_PAGINA_SERVICO = 12;
let isStaff = false;

document.addEventListener('DOMContentLoaded', function () {
        const usuario = Sessao.usuario;
    isStaff = usuario && (usuario.perfil === 'Administrador' || usuario.perfil === 'Bibliotecário');

    setupServicoForm();
    setupRespostaModal();
    carregarSolicitacoes();
    carregarTipos();
});

function setupServicoForm() {
    const form = document.getElementById('servicoForm');
    const tipo = document.getElementById('servicoTipo');

    tipo.addEventListener('change', () => {
        const wrap = document.getElementById('servicoCamposAdicionais');
        wrap.innerHTML = '';
        if (tipo.value === 'Ficha Catalográfica') {
            wrap.innerHTML = `
                <div class="form-row">
                    <div class="form-group">
                        <label for="fichaTitulo">Título do trabalho</label>
                        <input type="text" id="fichaTitulo">
                    </div>
                    <div class="form-group">
                        <label for="fichaAutor">Autor(a)</label>
                        <input type="text" id="fichaAutor">
                    </div>
                </div>`;
        }
        if (tipo.value === 'Sugestão de Aquisição') {
            wrap.innerHTML = `
                <div class="form-row">
                    <div class="form-group">
                        <label for="sugestaoTitulo">Título sugerido</label>
                        <input type="text" id="sugestaoTitulo">
                    </div>
                    <div class="form-group">
                        <label for="sugestaoAutor">Autor(a)</label>
                        <input type="text" id="sugestaoAutor">
                    </div>
                </div>`;
        }
    });

    form.addEventListener('submit', function (e) {
        e.preventDefault();
        const dados = {
            tipo: tipo.value,
            descricao: document.getElementById('servicoDescricao').value,
        };

        const fichaTitulo = document.getElementById('fichaTitulo');
        const fichaAutor = document.getElementById('fichaAutor');
        const sugestaoTitulo = document.getElementById('sugestaoTitulo');
        const sugestaoAutor = document.getElementById('sugestaoAutor');

        if (tipo.value === 'Ficha Catalográfica') {
            dados.dados_json = {
                titulo: fichaTitulo ? fichaTitulo.value : '',
                autor: fichaAutor ? fichaAutor.value : '',
            };
            if (!dados.dados_json.titulo) {
                showToast('Informe o título do trabalho.', 'warning');
                return;
            }
        }
        if (tipo.value === 'Sugestão de Aquisição') {
            dados.dados_json = {
                titulo: sugestaoTitulo ? sugestaoTitulo.value : '',
                autor: sugestaoAutor ? sugestaoAutor.value : '',
            };
            if (!dados.dados_json.titulo) {
                showToast('Informe o título sugerido.', 'warning');
                return;
            }
        }

        showLoading();
        API.post('/api/servicos', dados)
            .then(data => {
                showToast(data.mensagem || 'Solicitação enviada!', 'success');
                form.reset();
                document.getElementById('servicoCamposAdicionais').innerHTML = '';
                carregarSolicitacoes();
            })
            .catch(err => showToast('Erro: ' + err.message, 'error'))
            .finally(() => hideLoading());
    });
}

function carregarTipos() {
    API.get('/api/servicos/tipos')
        .then(tipos => {
            const select = document.getElementById('servicoTipo');
            select.innerHTML = '<option value="">Selecione o tipo...</option>';
            (tipos || []).forEach(t => {
                const opt = document.createElement('option');
                opt.value = t;
                opt.textContent = t;
                select.appendChild(opt);
            });
        })
        .catch(err => showToast('Erro ao carregar tipos: ' + err.message, 'error'));
}

function carregarSolicitacoes() {
    showLoading();
    skeletonTabela(6, 6, 'servicosBody');

    API.get('/api/servicos')
        .then(data => {
            todasSolicitacoes = data;
            aplicarFiltrosServico();
        })
        .catch(err => showToast('Erro ao carregar solicitações: ' + err.message, 'error'))
        .finally(() => hideLoading());
}

function aplicarFiltrosServico() {
    solicitacoesFiltradas = todasSolicitacoes.slice();
    const totalPaginas = Math.max(1, Math.ceil(solicitacoesFiltradas.length / POR_PAGINA_SERVICO));
    if (paginaServico > totalPaginas) paginaServico = totalPaginas;
    const pagina = paginar(solicitacoesFiltradas, paginaServico, POR_PAGINA_SERVICO);
    renderizarServicos(pagina);

    criarPaginacao('servicosPaginacao', paginaServico, totalPaginas, p => {
        paginaServico = p;
        aplicarFiltrosServico();
    });
}

function renderizarServicos(solicitacoes) {
    const tbody = document.getElementById('servicosBody');
    tbody.innerHTML = '';

    if (solicitacoes.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="empty-table">Nenhuma solicitação encontrada.</td></tr>';
        return;
    }

    solicitacoes.forEach(s => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><strong>${escapeHtml(s.usuario_nome || Sessao.usuario.nome)}</strong></td>
            <td>${escapeHtml(s.tipo || '-')}</td>
            <td style="max-width:320px">${escapeHtml(s.descricao || '-')}</td>
            <td style="font-family:var(--font-mono);font-size:12px">${formatDate(s.data_solicitacao)}</td>
            <td>${getStatusBadge(s.status)}</td>
            <td>
                ${isStaff ? `
                    <button class="btn btn-sm btn-secondary" onclick="abrirRespostaModal(${s.id})" title="Atualizar solicitação">
                        <svg class="ic" aria-hidden="true"><use href="#i-edit"></use></svg> Atualizar
                    </button>
                ` : (s.resposta ? `<span style="font-size:11px;color:var(--ink-faint)">${escapeHtml(s.resposta)}</span>` : '')}
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function setupRespostaModal() {
    const modal = document.getElementById('servicoRespostaModal');
    modal.querySelectorAll('.modal-close, [data-fechar]').forEach(btn => {
        btn.addEventListener('click', () => fecharModal('servicoRespostaModal'));
    });
    modal.addEventListener('click', (e) => {
        if (e.target === modal) fecharModal('servicoRespostaModal');
    });

    document.getElementById('btnSalvarResposta').addEventListener('click', salvarResposta);
}

function abrirRespostaModal(id) {
    const sol = todasSolicitacoes.find(s => s.id === id);
    if (!sol) return;
    document.getElementById('servicoRespostaId').value = id;
    document.getElementById('servicoRespostaStatus').value = sol.status || 'Pendente';
    document.getElementById('servicoRespostaTexto').value = sol.resposta || '';
    abrirModal('servicoRespostaModal');
}

function salvarResposta() {
    const id = document.getElementById('servicoRespostaId').value;
    const status = document.getElementById('servicoRespostaStatus').value;
    const resposta = document.getElementById('servicoRespostaTexto').value;

    showLoading();
    API.put(`/api/servicos/${id}`, { status, resposta })
        .then(data => {
            showToast(data.mensagem || 'Solicitação atualizada!', 'success');
            fecharModal('servicoRespostaModal');
            carregarSolicitacoes();
        })
        .catch(err => showToast('Erro: ' + err.message, 'error'))
        .finally(() => hideLoading());
}
