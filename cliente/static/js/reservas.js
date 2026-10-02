let todasReservas = [];
let reservasFiltradas = [];
let paginaReserva = 1;
const POR_PAGINA_RESERVA = 12;

document.addEventListener('DOMContentLoaded', function () {
        const usuario = Sessao.usuario;
    const isUsuario = usuario && usuario.perfil === 'Usuário';

    document.getElementById('btnNovaReserva').addEventListener('click', () => abrirFormReserva());
    document.getElementById('btnCancelarReservaForm').addEventListener('click', () => fecharFormReserva());
    document.getElementById('reservaForm').addEventListener('submit', enviarReserva);
    document.getElementById('livroReserva').addEventListener('change', mostrarInfoLivro);
    setupSearchReserva();

    carregarReservas();

    if (isUsuario) {
        document.getElementById('reservaHeadActions').style.display = '';
        const livroParam = new URLSearchParams(window.location.search).get('livro');
        preencherLivros().then(() => {
            if (livroParam) {
                document.getElementById('livroReserva').value = livroParam;
                mostrarInfoLivro();
                abrirFormReserva();
            }
        });
    }
});

function preencherLivros() {
    return API.get('/api/livros')
        .then(livros => {
            const select = document.getElementById('livroReserva');
            select.innerHTML = '<option value="">Selecione um livro...</option>';
            const indisponiveis = livros.filter(l => l.disponivel <= 0 && l.quantidade > 0);
            const disponiveis = livros.filter(l => l.disponivel > 0);
            indisponiveis.forEach(l => {
                const opt = document.createElement('option');
                opt.value = l.id;
                opt.textContent = `${l.titulo} — ${l.autor}`;
                opt.dataset.disponivel = l.disponivel;
                opt.dataset.quantidade = l.quantidade;
                select.appendChild(opt);
            });
            disponiveis.forEach(l => {
                const opt = document.createElement('option');
                opt.value = l.id;
                opt.textContent = `${l.titulo} — ${l.autor}`;
                opt.dataset.disponivel = l.disponivel;
                opt.dataset.quantidade = l.quantidade;
                select.appendChild(opt);
            });
            return livros;
        })
        .catch(err => showToast('Erro ao carregar livros: ' + err.message, 'error'));
}

function abrirFormReserva() {
    document.getElementById('reservaFormCard').style.display = '';
    document.getElementById('reservaFormCard').scrollIntoView({ behavior: 'smooth', block: 'start' });
    const first = document.getElementById('livroReserva');
    if (first) setTimeout(() => first.focus(), 60);
}

function fecharFormReserva() {
    document.getElementById('reservaFormCard').style.display = 'none';
    document.getElementById('reservaForm').reset();
    document.getElementById('reservaInfoBox').style.display = 'none';
}

function mostrarInfoLivro() {
    const select = document.getElementById('livroReserva');
    const box = document.getElementById('reservaInfoBox');
    const opt = select.selectedOptions[0];
    if (!opt || !opt.value) {
        box.style.display = 'none';
        return;
    }
    const disp = parseInt(opt.dataset.disponivel || '0', 10);
    const qtd = parseInt(opt.dataset.quantidade || '0', 10);
    if (disp > 0) {
        box.innerHTML = `<svg class="ic" aria-hidden="true"><use href="#i-info"></use></svg>
            Esta obra possui <strong>${disp}</strong> exemplar(es) disponível(is). Você pode retirá-la diretamente na biblioteca.</strong>`;
        box.classList.remove('suspensao-box');
        box.classList.add('alert-banner');
    } else if (qtd > 0) {
        box.innerHTML = `<svg class="ic" aria-hidden="true"><use href="#i-alert"></use></svg>
            Obra temporariamente esgotada. Ao reservar, você entrará na fila e será avisado quando um exemplar ficar disponível.`;
        box.classList.remove('alert-banner');
        box.classList.add('suspensao-box');
    } else {
        box.innerHTML = `<svg class="ic" aria-hidden="true"><use href="#i-alert"></use></svg>
            Este livro ainda não possui exemplares no acervo.`;
        box.classList.remove('alert-banner');
        box.classList.add('suspensao-box');
    }
    box.style.display = 'flex';
}

function enviarReserva(e) {
    e.preventDefault();
    const livroId = document.getElementById('livroReserva').value;
    if (!livroId) {
        showToast('Selecione um livro.', 'warning');
        return;
    }

    showLoading();
    API.post('/api/reservas', { livro_id: parseInt(livroId, 10) })
        .then(data => {
            showToast(data.mensagem || 'Reserva realizada com sucesso!', 'success');
            fecharFormReserva();
            carregarReservas();
        })
        .catch(err => showToast('Erro: ' + err.message, 'error'))
        .finally(() => hideLoading());
}

function carregarReservas() {
    showLoading();
    skeletonTabela(6, 6, 'reservasBody');

    API.get('/api/reservas')
        .then(data => {
            todasReservas = data;
            aplicarFiltrosReserva();
        })
        .catch(err => showToast('Erro ao carregar reservas: ' + err.message, 'error'))
        .finally(() => hideLoading());
}

function setupSearchReserva() {
    const input = document.getElementById('searchReserva');
    if (input) {
        input.addEventListener('input', debounce(() => aplicarFiltrosReserva(), 250));
    }
}

function aplicarFiltrosReserva() {
    const termo = (document.getElementById('searchReserva').value || '').toLowerCase();
    reservasFiltradas = todasReservas.filter(r => {
        if (!termo) return true;
        const texto = `${r.livro_titulo || ''} ${r.usuario_nome || ''} ${r.usuario_email || ''}`.toLowerCase();
        return texto.includes(termo);
    });

    const totalPaginas = Math.max(1, Math.ceil(reservasFiltradas.length / POR_PAGINA_RESERVA));
    if (paginaReserva > totalPaginas) paginaReserva = totalPaginas;
    const pagina = paginar(reservasFiltradas, paginaReserva, POR_PAGINA_RESERVA);
    renderizarReservas(pagina);

    criarPaginacao('reservasPaginacao', paginaReserva, totalPaginas, p => {
        paginaReserva = p;
        aplicarFiltrosReserva();
    });
}

function renderizarReservas(reservas) {
    const tbody = document.getElementById('reservasBody');
    tbody.innerHTML = '';

    if (reservas.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="empty-table">Nenhuma reserva encontrada.</td></tr>';
        return;
    }

    const usuario = Sessao.usuario;
    const isUsuario = usuario && usuario.perfil === 'Usuário';

    reservas.forEach(r => {
        const podeCancelar = !isUsuario || r.status === 'Ativa' || r.status === 'Disponível';
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><strong>${escapeHtml(r.livro_titulo || '-')}</strong></td>
            <td>${isUsuario ? escapeHtml(usuario.nome) : `${escapeHtml(r.usuario_nome || '-')}<div style="font-size:11px;color:var(--ink-faint);font-family:var(--font-mono)">${escapeHtml(r.usuario_email || '')}</div>`}</td>
            <td style="font-family:var(--font-mono);font-size:12px">${formatDate(r.data_reserva)}</td>
            <td><span class="status-badge status-info">#${r.posicao || '-'}</span></td>
            <td>${getStatusBadge(r.status === 'Disponível' ? 'Disponível_Reserva' : r.status)}</td>
            <td>
                ${podeCancelar ? `
                    <button class="btn btn-sm btn-delete" onclick="cancelarReserva(${r.id})" title="Cancelar reserva" aria-label="Cancelar reserva">
                        <svg class="ic" aria-hidden="true"><use href="#i-trash"></use></svg>
                    </button>
                ` : ''}
            </td>
        `;
        tbody.appendChild(tr);
    });
}

async function cancelarReserva(id) {
    const reserva = todasReservas.find(r => r.id === id);
    const ok = await confirmar(
        `Cancelar a reserva de "${reserva ? reserva.livro_titulo : ''}"?`,
        'Cancelar reserva',
        '#i-alert'
    );
    if (!ok) return;

    showLoading();
    API.delete(`/api/reservas/${id}`)
        .then(data => {
            showToast(data.mensagem || 'Reserva cancelada.', 'success');
            carregarReservas();
        })
        .catch(err => showToast('Erro: ' + err.message, 'error'))
        .finally(() => hideLoading());
}
