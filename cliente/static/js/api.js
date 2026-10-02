// ===============================
// CONFIGURAÇÃO DA API
// ===============================

// Ao ser servido pelo próprio Flask (documentado), usa caminhos relativos:
// funciona em http/https e em qualquer porta (incluindo acesso pelo celular).
// Ao abrir como arquivo local (file://), conecta em http://localhost:5000.
const API_BASE = window.location.protocol === 'file:'
    ? 'http://localhost:5000'
    : '';


// ===============================
// SESSÃO (token)
// ===============================

const Sessao = {
    TOKEN_KEY: 'biblioteca_token',
    USER_KEY: 'biblioteca_usuario',

    get token() {
        return localStorage.getItem(this.TOKEN_KEY);
    },

    get usuario() {
        try {
            return JSON.parse(localStorage.getItem(this.USER_KEY) || 'null');
        } catch {
            return null;
        }
    },

    salvar(token, usuario) {
        localStorage.setItem(this.TOKEN_KEY, token);
        localStorage.setItem(this.USER_KEY, JSON.stringify(usuario));
    },

    limpar() {
        localStorage.removeItem(this.TOKEN_KEY);
        localStorage.removeItem(this.USER_KEY);
    },

    autenticado() {
        return !!this.token;
    },

    precisaLogin() {
        if (!this.autenticado()) {
            window.location.href = '/login';
            return true;
        }
        return false;
    }
};


// ===============================
// CLIENTE DA API
// ===============================

const API = {

    async request(endpoint, options = {}) {

        const headers = {
            'Content-Type': 'application/json',
            ...(options.headers || {})
        };

        if (Sessao.token) {
            headers['Authorization'] = `Bearer ${Sessao.token}`;
        }

        const config = {
            headers,
            ...options,
        };

        try {

            const response = await fetch(
                `${API_BASE}${endpoint}`,
                config
            );

            if (response.status === 401 && Sessao.autenticado()) {
                Sessao.limpar();
                if (!window.location.pathname.endsWith('/login')) {
                    window.location.href = '/login';
                }
            }

            const data = await response.json();

            if (!response.ok) {
                throw new Error(
                    data.erro ||
                    `Erro ${response.status}: ${response.statusText}`
                );
            }

            return data;

        } catch (error) {

            if (
                error.name === 'TypeError' &&
                error.message === 'Failed to fetch'
            ) {
                throw new Error(
                    'Não foi possível conectar ao servidor. Verifique se o Flask está rodando e se o IP está correto.'
                );
            }

            throw error;

        }

    },

    get(endpoint) {
        return this.request(endpoint, { method: 'GET' });
    },

    post(endpoint, body) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(body)
        });
    },

    put(endpoint, body) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(body)
        });
    },

    delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }

};


// ===============================
// LOADING
// ===============================

let loadingCount = 0;

function showLoading() {
    loadingCount++;
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) overlay.classList.add('show');
}

function hideLoading() {
    loadingCount = Math.max(0, loadingCount - 1);
    if (loadingCount === 0) {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) overlay.classList.remove('show');
    }
}


// ===============================
// TOASTS
// ===============================

function showToast(message, type = 'info') {

    const container = document.getElementById('toastContainer');

    if (!container) {
        alert(message);
        return;
    }

    const icons = {
        success: '#i-check-c',
        error: '#i-alert',
        info: '#i-info',
        warning: '#i-alert'
    };

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.setAttribute('role', type === 'error' ? 'alert' : 'status');

    const ic = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    ic.setAttribute('class', 'ic');
    ic.setAttribute('aria-hidden', 'true');
    const use = document.createElementNS('http://www.w3.org/2000/svg', 'use');
    use.setAttribute('href', icons[type] || icons.info);
    ic.appendChild(use);

    const span = document.createElement('span');
    span.textContent = message;

    const btn = document.createElement('button');
    btn.className = 'close-toast';
    btn.setAttribute('aria-label', 'Fechar');
    btn.textContent = '×';

    toast.appendChild(ic);
    toast.appendChild(span);
    toast.appendChild(btn);

    btn.addEventListener('click', () => toast.remove());

    container.appendChild(toast);

    setTimeout(() => {
        if (toast.parentNode) {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100%)';
            toast.style.transition = 'all 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }
    }, 4000);

}


// ===============================
// SEGURANÇA DE HTML
// ===============================

function escapeHtml(texto) {
    if (texto === null || texto === undefined) return '';
    return String(texto)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}


// ===============================
// DATAS
// ===============================

function parseDateOnly(dateStr) {
    if (!dateStr) return new Date(NaN);
    const parts = dateStr.split('T')[0].split('-');
    return new Date(
        parseInt(parts[0]),
        parseInt(parts[1]) - 1,
        parseInt(parts[2]),
        12, 0, 0
    );
}

function formatDate(dateStr) {
    if (!dateStr) return '-';
    const parts = dateStr.split('T')[0].split('-');
    if (parts.length === 3) {
        return `${parts[2]}/${parts[1]}/${parts[0]}`;
    }
    return dateStr;
}

function hojeISO() {
    return new Date().toISOString().split('T')[0];
}

function addDiasISO(dias) {
    const d = new Date();
    d.setDate(d.getDate() + dias);
    return d.toISOString().split('T')[0];
}


// ===============================
// STATUS / BADGES
// ===============================

function getStatusBadge(status) {

    const map = {
        'Emprestado': '<span class="status-badge status-warning">Emprestado</span>',
        'Devolvido': '<span class="status-badge status-success">Devolvido</span>',
        'Atrasado': '<span class="status-badge status-danger">Atrasado</span>',
        'Disponível': '<span class="status-badge status-info">Disponível</span>',
        'Indisponível': '<span class="status-badge status-danger">Indisponível</span>',
        'Reservado': '<span class="status-badge status-warning">Reservado</span>',
        'Ativa': '<span class="status-badge status-warning">Ativa</span>',
        'Disponível_Reserva': '<span class="status-badge status-success">Disponível p/ retirada</span>',
        'Cancelada': '<span class="status-badge status-danger">Cancelada</span>',
        'Concluída': '<span class="status-badge status-success">Concluída</span>',
        'Pendente': '<span class="status-badge status-warning">Pendente</span>',
        'Em Análise': '<span class="status-badge status-info">Em Análise</span>',
        'Recusada': '<span class="status-badge status-danger">Recusada</span>',
        'Ativo': '<span class="status-badge status-success">Ativo</span>',
        'Suspenso': '<span class="status-badge status-danger">Suspenso</span>',
        'Inativo': '<span class="status-badge status-danger">Inativo</span>',
        'Administrador': '<span class="status-badge status-info">Administrador</span>',
        'Bibliotecário': '<span class="status-badge status-success">Bibliotecário</span>',
        'Usuário': '<span class="status-badge status-info">Usuário</span>',
        'Servidor': '<span class="status-badge status-info">Servidor</span>',
        'Discente Regular': '<span class="status-badge status-success">Discente Regular</span>',
        'Discente FIC': '<span class="status-badge status-warning">Discente FIC</span>',
        'Terceirizado': '<span class="status-badge status-danger">Terceirizado</span>',
    };

    return (
        map[status] ||
        `<span class="status-badge status-info">${escapeHtml(status)}</span>`
    );
}

function statusLivro(livro) {
    if (livro.quantidade === 0) return 'Indisponível';
    if (livro.disponivel > 0) return 'Disponível';
    return 'Emprestado';
}


// ===============================
// MODAIS
// ===============================

function abrirModal(id) {
    const modal = document.getElementById(id);
    if (modal) {
        modal.classList.add('show');
        const firstInput = modal.querySelector('input, select, textarea');
        if (firstInput) setTimeout(() => firstInput.focus(), 60);
    }
}

function fecharModal(id) {
    const modal = document.getElementById(id);
    if (modal) modal.classList.remove('show');
}

function fecharModais() {
    document.querySelectorAll('.modal.show').forEach(m => m.classList.remove('show'));
}

function confirmar(mensagem, titulo = 'Confirmar', icone = '#i-alert') {
    return new Promise((resolve) => {
        let container = document.getElementById('confirmModalGenerico');

        if (!container) {
            container = document.createElement('div');
            container.id = 'confirmModalGenerico';
            container.className = 'modal';
            container.innerHTML = `
                <div class="modal-content modal-sm">
                    <div class="modal-header">
                        <h3><svg class="ic" aria-hidden="true"><use href="${icone}"></use></svg> ${titulo}</h3>
                        <button class="modal-close" aria-label="Fechar"><svg class="ic" aria-hidden="true"><use href="#i-close"></use></svg></button>
                    </div>
                    <div class="modal-body"><p id="confirmMsg"></p></div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary btn-cancelar">Cancelar</button>
                        <button type="button" class="btn btn-danger btn-confirmar">Confirmar</button>
                    </div>
                </div>
            `;
            document.body.appendChild(container);
        }

        container.querySelector('#confirmMsg').textContent = mensagem;
        container.classList.add('show');

        const onCancelar = () => {
            container.classList.remove('show');
            cleanup();
            resolve(false);
        };
        const onConfirmar = () => {
            container.classList.remove('show');
            cleanup();
            resolve(true);
        };
        const onClose = () => {
            container.classList.remove('show');
            cleanup();
            resolve(false);
        };
        const onOverlay = (e) => {
            if (e.target === container) {
                container.classList.remove('show');
                cleanup();
                resolve(false);
            }
        };

        function cleanup() {
            container.querySelector('.btn-cancelar').removeEventListener('click', onCancelar);
            container.querySelector('.btn-confirmar').removeEventListener('click', onConfirmar);
            container.querySelector('.modal-close').removeEventListener('click', onClose);
            container.removeEventListener('click', onOverlay);
        }

        container.querySelector('.btn-cancelar').addEventListener('click', onCancelar);
        container.querySelector('.btn-confirmar').addEventListener('click', onConfirmar);
        container.querySelector('.modal-close').addEventListener('click', onClose);
        container.addEventListener('click', onOverlay);
    });
}


// ===============================
// PAGINAÇÃO
// ===============================

function criarPaginacao(container, paginaAtual, totalPaginas, aoMudar) {
    const el = document.getElementById(container);
    if (!el) return;

    el.innerHTML = '';

    if (totalPaginas <= 1) {
        el.innerHTML = '';
        return;
    }

    const btnAnt = document.createElement('button');
    btnAnt.className = 'btn btn-sm btn-secondary';
    btnAnt.textContent = '‹ Anterior';
    btnAnt.disabled = paginaAtual <= 1;
    btnAnt.addEventListener('click', () => aoMudar(paginaAtual - 1));
    el.appendChild(btnAnt);

    for (let p = 1; p <= totalPaginas; p++) {
        if (totalPaginas > 7 && p > 2 && p < totalPaginas - 1 && Math.abs(p - paginaAtual) > 1) {
            continue;
        }
        const btn = document.createElement('button');
        btn.className = `btn btn-sm ${p === paginaAtual ? 'btn-primary' : 'btn-secondary'}`;
        btn.textContent = p;
        btn.addEventListener('click', () => aoMudar(p));
        el.appendChild(btn);
    }

    const btnProx = document.createElement('button');
    btnProx.className = 'btn btn-sm btn-secondary';
    btnProx.textContent = 'Próximo ›';
    btnProx.disabled = paginaAtual >= totalPaginas;
    btnProx.addEventListener('click', () => aoMudar(paginaAtual + 1));
    el.appendChild(btnProx);
}

function paginar(items, pagina, porPagina = 10) {
    const inicio = (pagina - 1) * porPagina;
    return items.slice(inicio, inicio + porPagina);
}


// ===============================
// SKELETON LOADING
// ===============================

function skeletonTabela(colunas, linhas = 5, idBody) {
    const tbody = document.getElementById(idBody);
    if (!tbody) return;
    let html = '';
    for (let i = 0; i < linhas; i++) {
        html += `<tr class="skeleton-row">`;
        for (let c = 0; c < colunas; c++) {
            html += `<td><span class="skeleton-bar" style="width:${55 + (c * 9) % 40}%"></span></td>`;
        }
        html += `</tr>`;
    }
    tbody.innerHTML = html;
}

function skeletonCards(qtd, containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    let html = '';
    for (let i = 0; i < qtd; i++) {
        html += `<div class="skeleton-card"><span class="skeleton-bar" style="height:18px;width:60%"></span>
                 <span class="skeleton-bar" style="height:34px;width:45%;margin-top:14px"></span></div>`;
    }
    container.innerHTML = html;
}


// ===============================
// UTILITÁRIOS
// ===============================

function debounce(fn, ms = 300) {
    let t;
    return function (...args) {
        clearTimeout(t);
        t = setTimeout(() => fn.apply(this, args), ms);
    };
}

function pluralizar(total, singular, plural) {
    return total === 1 ? singular : plural;
}
