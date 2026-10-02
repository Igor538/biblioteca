let dadosPerfil = null;

document.addEventListener('DOMContentLoaded', function () {
        carregarPerfil();
    setupPerfilForm();
});

function carregarPerfil() {
    showLoading();
    API.get('/api/meus-dados')
        .then(data => {
            dadosPerfil = data;
            renderizarPerfil(data);
        })
        .catch(err => showToast('Erro ao carregar dados: ' + err.message, 'error'))
        .finally(() => hideLoading());
}

function renderizarPerfil(u) {
    document.getElementById('perfilAvatar').textContent = (u.nome || '?').trim().charAt(0).toUpperCase();
    document.getElementById('perfilNome').textContent = u.nome || '—';
    document.getElementById('perfilEmail').textContent = u.email || '—';
    document.getElementById('perfilBadges').innerHTML =
        getStatusBadge(u.tipo_usuario) + getStatusBadge(u.status);
    document.getElementById('perfilProntuario').textContent = u.prontuario || '-';
    document.getElementById('perfilCurso').textContent = u.curso || '-';
    document.getElementById('perfilTelefone').textContent = u.telefone || '-';
    document.getElementById('perfilEndereco').textContent = u.endereco || '-';
    document.getElementById('perfilCategoria').textContent = u.tipo_usuario || '-';
    document.getElementById('perfilLimite').textContent = `${u.limite_livros || 0} livros`;
    document.getElementById('perfilPrazo').textContent = `${u.prazo_dias || 0} dias`;

    document.getElementById('perfilNomeInput').value = u.nome || '';
    document.getElementById('perfilEmailInput').value = u.email || '';
    document.getElementById('perfilTelefoneInput').value = u.telefone || '';
    document.getElementById('perfilCursoInput').value = u.curso || '';
    document.getElementById('perfilEnderecoInput').value = u.endereco || '';

    const existente = document.getElementById('perfilPenalidadeBanner');
    if (existente) existente.remove();

    if (u.penalidades && u.penalidades.length > 0) {
        const lista = u.penalidades.map(p => `
            <li><strong>${escapeHtml(p.descricao || 'Penalidade')}</strong>
                <span style="display:block;font-size:12px;color:var(--ink-faint)">
                    Suspensão até ${formatDate(p.data_fim)}${p.dias_suspensao ? ` (${p.dias_suspensao} dias)` : ''}
                </span>
            </li>`).join('');
        const card = document.createElement('div');
        card.id = 'perfilPenalidadeBanner';
        card.className = 'alert-banner alert-banner-danger';
        card.style.margin = '0 0 18px';
        card.innerHTML = `<svg class="ic" aria-hidden="true"><use href="#i-alert"></use></svg>
            <div><strong>Você possui suspensão ativa.</strong><ul style="margin-top:6px;padding-left:18px">${lista}</ul></div>`;
        document.getElementById('perfilView').insertBefore(card, document.getElementById('perfilView').firstChild);
    }
}

function setupPerfilForm() {
    const form = document.getElementById('perfilForm');
    form.addEventListener('submit', function (e) {
        e.preventDefault();
        const dados = {
            nome: document.getElementById('perfilNomeInput').value,
            email: document.getElementById('perfilEmailInput').value,
            telefone: document.getElementById('perfilTelefoneInput').value,
            curso: document.getElementById('perfilCursoInput').value,
            endereco: document.getElementById('perfilEnderecoInput').value,
        };

        showLoading();
        API.put('/api/meus-dados', dados)
            .then(data => {
                showToast(data.mensagem || 'Dados atualizados com sucesso!', 'success');
                carregarPerfil();
            })
            .catch(err => showToast('Erro: ' + err.message, 'error'))
            .finally(() => hideLoading());
    });
}
