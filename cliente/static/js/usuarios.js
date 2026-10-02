let todosUsuarios = [];
let paginaUsuario = 1;
const POR_PAGINA_USUARIO = 12;

document.addEventListener('DOMContentLoaded', function () {
        carregarUsuarios();
    setupUsuariosModal();
    setupSearch();
});

function carregarUsuarios() {
    showLoading();
    skeletonTabela(7, 6, 'usuariosBody');

    API.get('/api/usuarios')
        .then(data => {
            todosUsuarios = data;
            aplicarFiltrosUsuarios();
        })
        .catch(err => showToast('Erro ao carregar usuários: ' + err.message, 'error'))
        .finally(() => hideLoading());
}

function aplicarFiltrosUsuarios() {
    const termo = (document.getElementById('searchUsuario').value || '').toLowerCase();
    const categoria = document.getElementById('filtroCategoria').value;
    const status = document.getElementById('filtroStatus').value;

    const filtrados = todosUsuarios.filter(u => {
        if (termo) {
            const texto = `${u.nome} ${u.email || ''} ${u.prontuario || ''} ${u.curso || ''}`.toLowerCase();
            if (!texto.includes(termo)) return false;
        }
        if (categoria && u.tipo_usuario !== categoria) return false;
        if (status && u.status !== status) return false;
        return true;
    });

    const contagem = document.getElementById('usuariosContagem');
    if (contagem) {
        contagem.textContent = `${filtrados.length} ${pluralizar(filtrados.length, 'usuário', 'usuários')}`;
    }

    const totalPaginas = Math.max(1, Math.ceil(filtrados.length / POR_PAGINA_USUARIO));
    if (paginaUsuario > totalPaginas) paginaUsuario = totalPaginas;

    const pagina = paginar(filtrados, paginaUsuario, POR_PAGINA_USUARIO);
    renderizarUsuarios(pagina);

    criarPaginacao('usuariosPaginacao', paginaUsuario, totalPaginas, p => {
        paginaUsuario = p;
        aplicarFiltrosUsuarios();
    });
}

function renderizarUsuarios(usuarios) {
    const tbody = document.getElementById('usuariosBody');
    tbody.innerHTML = '';

    if (usuarios.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="empty-table">Nenhum usuário encontrado.</td></tr>';
        return;
    }

    usuarios.forEach(u => {
        const limite = { 'Servidor': 8, 'Discente Regular': 6, 'Discente FIC': 2, 'Terceirizado': 2 }[u.tipo_usuario] || 6;
        const emUso = u.emprestimos_ativos || 0;
        const pct = Math.min(100, Math.round((emUso / limite) * 100));

        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>
                <strong>${escapeHtml(u.nome)}</strong>
                <div style="font-size:11px;color:var(--ink-faint);font-family:var(--font-mono)">${escapeHtml(u.curso || '—')}</div>
            </td>
            <td>${escapeHtml(u.prontuario || '-')}</td>
            <td>${escapeHtml(u.email)}</td>
            <td>${getStatusBadge(u.tipo_usuario)}</td>
            <td style="min-width:120px">
                <span style="font-family:var(--font-mono);font-size:12px">${emUso}/${limite}</span>
                <div class="progress" style="margin-top:4px" aria-label="Uso do limite de empréstimos">
                    <div class="progress-fill ${pct >= 100 ? 'danger' : pct >= 75 ? 'warn' : ''}" style="width:${pct}%"></div>
                </div>
            </td>
            <td>${getStatusBadge(u.status)}</td>
            <td>
                <div class="acoes-grupo">
                    <button class="btn btn-sm btn-secondary" onclick="verUsuario(${u.id})" title="Ver detalhes" aria-label="Ver detalhes">
                        <svg class="ic" aria-hidden="true"><use href="#i-eye"></use></svg>
                    </button>
                    <button class="btn btn-sm btn-edit" onclick="editarUsuario(${u.id})" title="Editar" aria-label="Editar usuário">
                        <svg class="ic" aria-hidden="true"><use href="#i-edit"></use></svg>
                    </button>
                    <button class="btn btn-sm btn-delete" onclick="excluirUsuario(${u.id})" title="Excluir" aria-label="Excluir usuário">
                        <svg class="ic" aria-hidden="true"><use href="#i-trash"></use></svg>
                    </button>
                </div>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function setupUsuariosModal() {
    const modal = document.getElementById('usuarioModal');
    const btnNovo = document.getElementById('btnNovoUsuario');
    const form = document.getElementById('usuarioForm');

    btnNovo.addEventListener('click', () => abrirModalUsuario());

    modal.querySelectorAll('.modal-close, .modal-close-btn').forEach(btn => {
        btn.addEventListener('click', () => fecharModal('usuarioModal'));
    });

    modal.addEventListener('click', (e) => {
        if (e.target === modal) fecharModal('usuarioModal');
    });

    form.addEventListener('submit', function (e) {
        e.preventDefault();
        const usuarioId = document.getElementById('usuarioId').value;
        const dados = {
            nome: document.getElementById('nome').value,
            email: document.getElementById('email').value,
            telefone: document.getElementById('telefone').value,
            endereco: document.getElementById('endereco').value,
            prontuario: document.getElementById('prontuario').value,
            curso: document.getElementById('curso').value,
            ano_ingresso: parseInt(document.getElementById('ano_ingresso').value) || null,
            tipo_usuario: document.getElementById('tipo_usuario').value,
            perfil: document.getElementById('perfil').value,
            status: document.getElementById('status').value,
        };

        showLoading();
        const request = usuarioId
            ? API.put(`/api/usuarios/${usuarioId}`, dados)
            : API.post('/api/usuarios', dados);

        request
            .then(data => {
                showToast(data.mensagem || 'Operação realizada com sucesso!', 'success');
                fecharModal('usuarioModal');
                carregarUsuarios();
            })
            .catch(err => showToast('Erro: ' + err.message, 'error'))
            .finally(() => hideLoading());
    });
}

function abrirModalUsuario(usuario = null) {
    const form = document.getElementById('usuarioForm');
    const title = document.getElementById('modalTitleUsuario');

    form.reset();
    document.getElementById('usuarioId').value = '';

    if (usuario) {
        title.textContent = 'Editar Usuário';
        document.getElementById('usuarioId').value = usuario.id;
        document.getElementById('nome').value = usuario.nome;
        document.getElementById('email').value = usuario.email;
        document.getElementById('telefone').value = usuario.telefone || '';
        document.getElementById('endereco').value = usuario.endereco || '';
        document.getElementById('prontuario').value = usuario.prontuario || '';
        document.getElementById('curso').value = usuario.curso || '';
        document.getElementById('ano_ingresso').value = usuario.ano_ingresso || '';
        document.getElementById('tipo_usuario').value = usuario.tipo_usuario || 'Discente Regular';
        document.getElementById('perfil').value = usuario.perfil || 'Usuário';
        document.getElementById('status').value = usuario.status || 'Ativo';
    } else {
        title.textContent = 'Novo Usuário';
    }

    abrirModal('usuarioModal');
}

function editarUsuario(id) {
    const usuario = todosUsuarios.find(u => u.id === id);
    if (usuario) {
        abrirModalUsuario(usuario);
    } else {
        showToast('Usuário não encontrado.', 'error');
    }
}

function verUsuario(id) {
    const u = todosUsuarios.find(x => x.id === id);
    if (!u) return;

    const limite = { 'Servidor': 8, 'Discente Regular': 6, 'Discente FIC': 2, 'Terceirizado': 2 }[u.tipo_usuario] || 6;
    const prazo = { 'Servidor': 21, 'Discente Regular': 7, 'Discente FIC': 7, 'Terceirizado': 7 }[u.tipo_usuario] || 7;

    let container = document.getElementById('usuarioDetalheModal');
    if (!container) {
        container = document.createElement('div');
        container.id = 'usuarioDetalheModal';
        container.className = 'modal';
        container.innerHTML = `
            <div class="modal-content modal-lg">
                <div class="modal-header">
                    <h3><svg class="ic" aria-hidden="true"><use href="#i-users"></use></svg> Detalhes do Usuário</h3>
                    <button class="modal-close" aria-label="Fechar"><svg class="ic" aria-hidden="true"><use href="#i-close"></use></svg></button>
                </div>
                <div class="modal-body" id="usuarioDetalheBody"></div>
            </div>
        `;
        document.body.appendChild(container);
        container.querySelector('.modal-close').addEventListener('click', () => fecharModal('usuarioDetalheModal'));
        container.addEventListener('click', (e) => { if (e.target === container) fecharModal('usuarioDetalheModal'); });
    }

    container.querySelector('#usuarioDetalheBody').innerHTML = `
        <div class="profile-card" style="margin-bottom:18px">
            <span class="profile-avatar">${escapeHtml((u.nome || '?')[0].toUpperCase())}</span>
            <div class="profile-card-body">
                <h3>${escapeHtml(u.nome)}</h3>
                <p class="profile-meta">${escapeHtml(u.email)}</p>
                <div style="margin-top:8px;display:flex;gap:8px;flex-wrap:wrap">
                    ${getStatusBadge(u.tipo_usuario)}${getStatusBadge(u.status)}
                </div>
            </div>
        </div>
        <dl class="info-list">
            <div class="info-item"><dt>Prontuário</dt><dd>${escapeHtml(u.prontuario || '-')}</dd></div>
            <div class="info-item"><dt>Curso</dt><dd>${escapeHtml(u.curso || '-')}</dd></div>
            <div class="info-item"><dt>Ano de Ingresso</dt><dd>${u.ano_ingresso || '-'}</dd></div>
            <div class="info-item"><dt>Telefone</dt><dd>${escapeHtml(u.telefone || '-')}</dd></div>
            <div class="info-item"><dt>Endereço</dt><dd>${escapeHtml(u.endereco || '-')}</dd></div>
            <div class="info-item"><dt>Perfil</dt><dd>${escapeHtml(u.perfil)}</dd></div>
            <div class="info-item"><dt>Limite de Empréstimos</dt><dd><strong>${limite} livros</strong></dd></div>
            <div class="info-item"><dt>Prazo de Devolução</dt><dd><strong>${prazo} dias</strong></dd></div>
            <div class="info-item"><dt>Empréstimos Ativos</dt><dd>${u.emprestimos_ativos || 0}</dd></div>
            <div class="info-item"><dt>Data de Cadastro</dt><dd>${formatDate(u.data_cadastro)}</dd></div>
        </dl>
    `;
    abrirModal('usuarioDetalheModal');
}

async function excluirUsuario(id) {
    const usuario = todosUsuarios.find(u => u.id === id);
    const ok = await confirmar(`Excluir o usuário "${usuario ? usuario.nome : ''}"? Empréstimos e reservas vinculados serão removidos.`);
    if (!ok) return;

    showLoading();
    API.delete(`/api/usuarios/${id}`)
        .then(data => {
            showToast(data.mensagem || 'Usuário excluído com sucesso!', 'success');
            carregarUsuarios();
        })
        .catch(err => showToast('Erro: ' + err.message, 'error'))
        .finally(() => hideLoading());
}

function setupSearch() {
    const searchInput = document.getElementById('searchUsuario');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(() => aplicarFiltrosUsuarios(), 250));
    }

    const filtroCat = document.getElementById('filtroCategoria');
    const filtroSt = document.getElementById('filtroStatus');
    if (filtroCat) filtroCat.addEventListener('change', () => { paginaUsuario = 1; aplicarFiltrosUsuarios(); });
    if (filtroSt) filtroSt.addEventListener('change', () => { paginaUsuario = 1; aplicarFiltrosUsuarios(); });
}
