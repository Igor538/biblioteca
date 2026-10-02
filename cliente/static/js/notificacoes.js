document.addEventListener('DOMContentLoaded', function () {
        document.getElementById('btnLerTodas').addEventListener('click', marcarTodasLidas);
    carregarNotificacoes();
});

function carregarNotificacoes() {
    showLoading();
    API.get('/api/notificacoes')
        .then(data => {
            renderizarNotificacoes(data.notificacoes || [], data.nao_lidas || 0);
        })
        .catch(err => showToast('Erro ao carregar notificações: ' + err.message, 'error'))
        .finally(() => hideLoading());
}

function renderizarNotificacoes(notificacoes, naoLidas) {
    const container = document.getElementById('notificacoesList');
    const badge = document.getElementById('notifContagem');

    badge.textContent = naoLidas > 0
        ? `${naoLidas} não ${pluralizar(naoLidas, 'lida', 'lidas')}`
        : 'Tudo em dia';

    container.innerHTML = '';

    if (notificacoes.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <svg class="ic" aria-hidden="true"><use href="#i-bell"></use></svg>
                <p>Você não possui notificações.</p>
            </div>`;
        return;
    }

    const icones = {
        emprestimo: '#i-loan',
        renovacao: '#i-refresh',
        devolucao: '#i-return',
        reserva: '#i-reserve',
        reserva_disponivel: '#i-check-c',
        suspensao: '#i-alert',
    };

    notificacoes.forEach(n => {
        const item = document.createElement('div');
        item.className = `notif-item${n.lida ? '' : ' nao-lida'}`;
        item.setAttribute('data-id', n.id);
        item.innerHTML = `
            <span class="notif-ic"><svg class="ic" aria-hidden="true"><use href="${icones[n.tipo] || '#i-info'}"></use></svg></span>
            <div class="notif-item-body">
                <p>${escapeHtml(n.mensagem)}</p>
                <span class="notif-data">${formatDate(n.data_criacao)}${n.lida ? '' : ' · <strong>nova</strong>'}</span>
            </div>
            ${n.lida ? '' : `<button class="btn btn-sm btn-secondary" onclick="marcarLida(${n.id})" title="Marcar como lida">Marcar como lida</button>`}
        `;
        container.appendChild(item);
    });
}

function marcarLida(id) {
    API.put(`/api/notificacoes/${id}/lida`)
        .then(() => carregarNotificacoes())
        .catch(err => showToast('Erro: ' + err.message, 'error'));
}

function marcarTodasLidas() {
    showLoading();
    API.put('/api/notificacoes/ler-todas')
        .then(data => {
            showToast(data.mensagem || 'Todas as notificações foram marcadas como lidas.', 'success');
            carregarNotificacoes();
        })
        .catch(err => showToast('Erro: ' + err.message, 'error'))
        .finally(() => hideLoading());
}
