// ===============================
// APP SHELL — elemento compartilhado entre todas as páginas
// Sidebar por perfil, topbar, modo escuro, ícones, notificações
// ===============================

// -------------------------------
// SPRITE DE ÍCONES (injetado via JS para todas as páginas)
// -------------------------------
(function injetarSprite() {
    const SPRITE = `
<svg xmlns="http://www.w3.org/2000/svg" style="display:none" aria-hidden="true">
    <symbol id="i-book-open" viewBox="0 0 24 24"><path d="M12 5.5C10.4 4.4 7.9 4.1 4.5 4.6v14.2c3.4-.5 5.9-.2 7.5 1.2 1.6-1.4 4.1-1.7 7.5-1.2V4.6c-3.4-.5-5.9-.2-7.5 1.2Z"/><path d="M12 5.5v14.5"/></symbol>
    <symbol id="i-book" viewBox="0 0 24 24"><path d="M4.5 19.5A2.5 2.5 0 0 1 7 17H19.5V3H7a2.5 2.5 0 0 0-2.5 2.5v14Z"/><path d="M9.5 3v7.5l2.2-1.6 2.2 1.6V3"/></symbol>
    <symbol id="i-dash" viewBox="0 0 24 24"><rect x="3.5" y="3.5" width="7.2" height="7.2"/><rect x="13.3" y="3.5" width="7.2" height="7.2"/><rect x="3.5" y="13.3" width="7.2" height="7.2"/><path class="fill" d="M13.3 20.5h7.2v-7.2h-7.2v7.2Z"/></symbol>
    <symbol id="i-users" viewBox="0 0 24 24"><circle cx="9" cy="8" r="3.2"/><path d="M3.8 19.2c.6-3.1 2.8-4.7 5.2-4.7s4.6 1.6 5.2 4.7"/><circle cx="16.6" cy="9.3" r="2.3"/><path d="M15.6 14.7c2.3.2 4 1.7 4.6 4"/></symbol>
    <symbol id="i-loan" viewBox="0 0 24 24"><rect x="3.2" y="4" width="14" height="16" rx="1"/><path d="M8 8.5h11.5M16.5 5.8l2.7 2.7-2.7 2.7"/></symbol>
    <symbol id="i-return" viewBox="0 0 24 24"><rect x="6.8" y="4" width="14" height="16" rx="1"/><path d="M16 8.5H4.5M7.5 5.8 4.8 8.5l2.7 2.7"/></symbol>
    <symbol id="i-edit" viewBox="0 0 24 24"><path d="M4 20l4.4-1L18.5 9a2.2 2.2 0 0 0-3.1-3.1L5.3 16 4 20Z"/><path d="m13.6 6.2 2.7 2.7"/></symbol>
    <symbol id="i-trash" viewBox="0 0 24 24"><path d="M4 6h16"/><path d="M9 6V4h6v2"/><path d="M6.4 6l.9 14h9.4l.9-14"/><path d="M10 10.5v5.5M14 10.5v5.5"/></symbol>
    <symbol id="i-plus" viewBox="0 0 24 24"><path d="M12 5v14M5 12h14"/></symbol>
    <symbol id="i-search" viewBox="0 0 24 24"><circle cx="11" cy="11" r="6.3"/><path d="m15.8 15.8 4.6 4.6"/></symbol>
    <symbol id="i-menu" viewBox="0 0 24 24"><path d="M4 7h16M4 12h16M4 17h10"/></symbol>
    <symbol id="i-close" viewBox="0 0 24 24"><path d="m6 6 12 12M18 6 6 18"/></symbol>
    <symbol id="i-lamp" viewBox="0 0 24 24"><path d="M7.2 3h9.6l-1.6 6.2H8.8L7.2 3Z"/><path d="M9.2 9.2V11a2.8 2.8 0 0 0 2.8 2.8 2.8 2.8 0 0 0 2.8-2.8V9.2"/><path d="M12 13.8v3.6M9.5 20.4h5"/><path d="M19.4 6.4 21 7.2M4.6 6.4 3 7.2"/></symbol>
    <symbol id="i-lamp-off" viewBox="0 0 24 24"><path d="M7.2 3h9.6l-1.6 6.2H8.8L7.2 3Z"/><path d="M9.2 9.2V11a2.8 2.8 0 0 0 2.8 2.8 2.8 2.8 0 0 0 2.8-2.8V9.2"/><path d="M12 13.8v3.6M9.5 20.4h5"/><path d="M4.5 20 20 4"/></symbol>
    <symbol id="i-logout" viewBox="0 0 24 24"><path d="M14 4.5h3.5A1.5 1.5 0 0 1 19 6v12a1.5 1.5 0 0 1-1.5 1.5H14"/><path d="M10.5 8.5 7 12l3.5 3.5"/><path d="M7 12h9.5"/></symbol>
    <symbol id="i-check" viewBox="0 0 24 24"><path d="m5 12.5 4.5 4.5L19 7.5"/></symbol>
    <symbol id="i-check-c" viewBox="0 0 24 24"><circle cx="12" cy="12" r="8.5"/><path d="m8.4 12.5 2.4 2.4 4.8-4.8"/></symbol>
    <symbol id="i-alert" viewBox="0 0 24 24"><path d="M12 4.2 3.6 19h16.8L12 4.2Z"/><path d="M12 10v4.2M12 16.8v.4"/></symbol>
    <symbol id="i-info" viewBox="0 0 24 24"><circle cx="12" cy="12" r="8.5"/><path d="M12 11.2v5M12 7.6v.4"/></symbol>
    <symbol id="i-arrow" viewBox="0 0 24 24"><path d="M4.5 12h15M14 6.5 19.5 12 14 17.5"/></symbol>
    <symbol id="i-undo" viewBox="0 0 24 24"><path d="M4 9.5h9.5a4.5 4.5 0 0 1 0 9H11"/><path d="M8 5.5 4 9.5l4 4"/></symbol>
    <symbol id="i-refresh" viewBox="0 0 24 24"><path d="M20 11.5A8 8 0 0 0 5.2 8.2L4 9.5"/><path d="M4 4.5v5h5"/><path d="M4 12.5A8 8 0 0 0 18.8 15.8L20 14.5"/><path d="M20 19.5v-5h-5"/></symbol>
    <symbol id="i-reserve" viewBox="0 0 24 24"><path d="M6 3.5h12v17l-6-4-6 4v-17Z"/><path d="M9.5 8h5"/></symbol>
    <symbol id="i-history" viewBox="0 0 24 24"><circle cx="12" cy="12" r="8"/><path d="M12 7.5V12l3 2"/></symbol>
    <symbol id="i-user" viewBox="0 0 24 24"><circle cx="12" cy="8" r="3.5"/><path d="M5.5 20c.8-3.4 3.2-5.2 6.5-5.2s5.7 1.8 6.5 5.2"/></symbol>
    <symbol id="i-chart" viewBox="0 0 24 24"><path d="M4 20h16"/><path d="M6.5 20v-6M11 20V8M15.5 20v-9M19.5 20V5"/></symbol>
    <symbol id="i-service" viewBox="0 0 24 24"><path d="M12 3.5 4 7v5c0 4.6 3.4 8.2 8 9 4.6-.8 8-4.4 8-9V7l-8-3.5Z"/><path d="m8.5 12 2.3 2.3 4.7-4.7"/></symbol>
    <symbol id="i-audit" viewBox="0 0 24 24"><rect x="4.5" y="3.5" width="15" height="17"/><path d="M9 3.5V7h6V3.5"/><path d="M8.5 12h7M8.5 16h7"/></symbol>
    <symbol id="i-bell" viewBox="0 0 24 24"><path d="M6 9a6 6 0 0 1 12 0c0 5 2 6 2 6H4s2-1 2-6Z"/><path d="M10 19a2 2 0 0 0 4 0"/></symbol>
    <symbol id="i-file" viewBox="0 0 24 24"><path d="M6 3.5h8l4 4v13H6v-17Z"/><path d="M14 3.5v4h4"/><path d="M9 12h6M9 16h6"/></symbol>
    <symbol id="i-download" viewBox="0 0 24 24"><path d="M12 3.5V15"/><path d="m7.5 10.5 4.5 4.5 4.5-4.5"/><path d="M5 20h14"/></symbol>
    <symbol id="i-clock" viewBox="0 0 24 24"><circle cx="12" cy="12" r="8"/><path d="M12 7.5V12l3 2"/></symbol>
    <symbol id="i-calendar" viewBox="0 0 24 24"><rect x="4" y="5" width="16" height="15.5"/><path d="M4 9.5h16M8.5 3v4M15.5 3v4"/></symbol>
    <symbol id="i-mail" viewBox="0 0 24 24"><rect x="3.5" y="5.5" width="17" height="13" rx="1"/><path d="m4.5 7 7.5 5.5L19.5 7"/></symbol>
    <symbol id="i-phone" viewBox="0 0 24 24"><path d="M5 4h4l1.5 4-2 1.5a12 12 0 0 0 6 6L16 13.5l4 1.5v4a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2Z"/></symbol>
    <symbol id="i-eye" viewBox="0 0 24 24"><path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12Z"/><circle cx="12" cy="12" r="2.8"/></symbol>
    <symbol id="i-warning" viewBox="0 0 24 24"><path d="M12 4.2 3.6 19h16.8L12 4.2Z"/><path d="M12 10v4.2M12 16.8v.4"/></symbol>
    <symbol id="i-tag" viewBox="0 0 24 24"><path d="m3.5 12 8.5-8.5h8v8L11.5 20.5 3.5 12Z"/><circle cx="15.5" cy="8.5" r="1.3" class="fill"/></symbol>
</svg>`;
    const div = document.createElement('div');
    div.innerHTML = SPRITE;
    while (div.firstChild) {
        document.body.appendChild(div.firstChild);
    }
})();


// -------------------------------
// NAVEGAÇÃO POR PERFIL
// -------------------------------
const NAV_ITENS = [
    { secao: 'Seções' },
    { href: '/sistema', icono: '#i-dash', rotulo: 'Dashboard', perfis: ['Administrador', 'Bibliotecário', 'Usuário'] },
    { href: '/consulta', icono: '#i-search', rotulo: 'Consulta ao Acervo', perfis: ['Administrador', 'Bibliotecário', 'Usuário'] },
    { href: '/livros', icono: '#i-book', rotulo: 'Livros', perfis: ['Administrador', 'Bibliotecário'] },
    { href: '/usuarios', icono: '#i-users', rotulo: 'Usuários', perfis: ['Administrador', 'Bibliotecário'] },
    { href: '/emprestimos', icono: '#i-loan', rotulo: 'Empréstimos', perfis: ['Administrador', 'Bibliotecário'] },
    { href: '/devolucoes', icono: '#i-return', rotulo: 'Devoluções', perfis: ['Administrador', 'Bibliotecário'] },
    { href: '/reservas', icono: '#i-reserve', rotulo: 'Reservas', perfis: ['Administrador', 'Bibliotecário', 'Usuário'] },
    { href: '/historico', icono: '#i-history', rotulo: 'Histórico', perfis: ['Administrador', 'Bibliotecário', 'Usuário'] },
    { href: '/meu-perfil', icono: '#i-user', rotulo: 'Meu Pergamum', perfis: ['Usuário'] },
    { secao: 'Gestão' },
    { href: '/relatorios', icono: '#i-chart', rotulo: 'Relatórios', perfis: ['Administrador', 'Bibliotecário'] },
    { href: '/servicos', icono: '#i-service', rotulo: 'Serviços ao Usuário', perfis: ['Administrador', 'Bibliotecário', 'Usuário'] },
    { href: '/auditoria', icono: '#i-audit', rotulo: 'Auditoria e Logs', perfis: ['Administrador'] },
    { secao: 'Institucional' },
    { href: '/sobre', icono: '#i-info', rotulo: 'Sobre o Sistema', perfis: ['Administrador', 'Bibliotecário', 'Usuário'] },
];

const ROTULO_PERFIL = {
    'Administrador': 'Administrador',
    'Bibliotecário': 'Bibliotecário',
    'Usuário': 'Leitor'
};


// -------------------------------
// RENDERIZAÇÃO DA SIDEBAR
// -------------------------------
function renderizarSidebar(usuario) {
    const nav = document.getElementById('sidebarNav');
    const userInfo = document.getElementById('sidebarUserInfo');
    const avatar = document.getElementById('sidebarUserAvatar');

    if (!usuario) return;

    if (avatar) {
        avatar.textContent = (usuario.nome || '?').trim().charAt(0).toUpperCase();
    }

    if (userInfo) {
        userInfo.innerHTML = `
            <span class="sidebar-user-name">${escapeHtml(usuario.nome)}</span>
            <span class="sidebar-user-role">${ROTULO_PERFIL[usuario.perfil] || usuario.perfil}</span>
        `;

        let logout = document.getElementById('logoutBtn');
        if (!logout) {
            logout = document.createElement('a');
            logout.href = '/login';
            logout.className = 'sidebar-logout';
            logout.id = 'logoutBtn';
            logout.title = 'Sair';
            logout.setAttribute('aria-label', 'Sair do sistema');
            logout.innerHTML = '<svg class="ic" aria-hidden="true"><use href="#i-logout"></use></svg>';
            const userCard = userInfo.closest('.sidebar-user');
            if (userCard) userCard.appendChild(logout);
        }
        logout.addEventListener('click', (e) => {
            e.preventDefault();
            encerrarSessao();
        });
    }

    if (!nav) return;

    const paginaAtual = window.location.pathname.split('/').pop();

    let html = '';
    NAV_ITENS.forEach(item => {
        if (item.secao) {
            html += `<span class="nav-section">${item.secao}</span>`;
            return;
        }
        if (!item.perfis.includes(usuario.perfil)) return;
        const ativo = ('/' + paginaAtual) === item.href ? ' active' : '';
        html += `
            <a href="${item.href}" class="nav-item${ativo}">
                <svg class="ic" aria-hidden="true"><use href="${item.icono}"></use></svg>
                <span>${item.rotulo}</span>
            </a>
        `;
    });
    nav.innerHTML = html;

    nav.querySelectorAll('.nav-item').forEach(link => {
        link.addEventListener('click', () => {
            if (window.innerWidth < 768) fecharSidebarMobile();
        });
    });
}


// -------------------------------
// NOTIFICAÇÕES — badge na topbar
// -------------------------------
function renderizarBadgeNotificacoes() {
    const right = document.querySelector('.topbar-right');
    if (!right) return;

    const btn = document.createElement('a');
    btn.href = '/notificacoes';
    btn.className = 'btn-icon notif-btn';
    btn.title = 'Notificações';
    btn.setAttribute('aria-label', 'Notificações');
    btn.innerHTML = `
        <svg class="ic" aria-hidden="true"><use href="#i-bell"></use></svg>
        <span class="notif-badge" id="notifBadge" style="display:none">0</span>
    `;
    right.appendChild(btn);

    carregarContagemNotificacoes();
}

function carregarContagemNotificacoes() {
    if (!Sessao.autenticado()) return;
    API.get('/api/notificacoes/nao-lidas')
        .then(data => {
            const badge = document.getElementById('notifBadge');
            if (!badge) return;
            const total = data.nao_lidas || 0;
            badge.style.display = total > 0 ? 'inline-flex' : 'none';
            badge.textContent = total > 99 ? '99+' : total;
        })
        .catch(() => {});
}


// -------------------------------
// MODO ESCURO
// -------------------------------
function aplicarModoEscuro() {
    const ativo = localStorage.getItem('darkMode') === 'true';
    document.body.classList.toggle('dark-mode', ativo);
    const icon = document.querySelector('#darkModeToggle .ic use');
    if (icon) icon.setAttribute('href', ativo ? '#i-lamp' : '#i-lamp-off');
}

function setupModoEscuro() {
    const toggle = document.getElementById('darkModeToggle');
    if (!toggle) return;
    toggle.addEventListener('click', function () {
        const ativo = document.body.classList.toggle('dark-mode');
        localStorage.setItem('darkMode', ativo);
        const icon = this.querySelector('.ic use');
        if (icon) icon.setAttribute('href', ativo ? '#i-lamp' : '#i-lamp-off');
    });
}


// -------------------------------
// SIDEBAR (mobile/colapso)
// -------------------------------
function fecharSidebarMobile() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebarOverlay');
    const toggle = document.getElementById('sidebarToggle');
    if (!sidebar) return;
    sidebar.classList.remove('mobile-open');
    if (overlay) overlay.classList.remove('show');
    if (toggle) toggle.setAttribute('aria-expanded', 'false');
}

function toggleSidebar(e) {
    e.stopPropagation();
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebarOverlay');
    const toggle = document.getElementById('sidebarToggle');
    if (!sidebar) return;
    if (window.innerWidth < 768) {
        sidebar.classList.toggle('mobile-open');
        if (overlay) overlay.classList.toggle('show');
        if (toggle) toggle.setAttribute('aria-expanded', sidebar.classList.contains('mobile-open'));
    } else {
        sidebar.classList.toggle('collapsed');
    }
}

function setupSidebar() {
    const toggle = document.getElementById('sidebarToggle');
    const overlay = document.getElementById('sidebarOverlay');
    if (toggle) toggle.addEventListener('click', toggleSidebar);
    if (overlay) overlay.addEventListener('click', fecharSidebarMobile);
    window.addEventListener('resize', function () {
        const sidebar = document.getElementById('sidebar');
        if (window.innerWidth >= 768 && sidebar) {
            sidebar.classList.remove('mobile-open');
            const overlay = document.getElementById('sidebarOverlay');
            if (overlay) overlay.classList.remove('show');
            const t = document.getElementById('sidebarToggle');
            if (t) t.setAttribute('aria-expanded', 'false');
        }
    });
}


function setupTopbarSombra() {
    const topbar = document.querySelector('.topbar');
    if (!topbar) return;
    const aplicar = () => topbar.classList.toggle('scrolled', window.scrollY > 6);
    window.addEventListener('scroll', aplicar, { passive: true });
    aplicar();
}


// -------------------------------
// SESSÃO — encerrar
// -------------------------------
async function encerrarSessao() {
    Sessao.limpar();
    window.location.href = '/logout';
}


// -------------------------------
// BOOT
// -------------------------------
document.addEventListener('DOMContentLoaded', async function () {
    setupSidebar();
    setupModoEscuro();
    setupTopbarSombra();
    aplicarModoEscuro();

    const pagina = window.location.pathname;
    const publica = pagina === '/' || pagina === '/login' || pagina === '/cadastro' ||
        pagina === '/index' || pagina === '/home';

    try {
        const resposta = await fetch('/api/usuario');
        if (resposta.status === 401) {
            localStorage.removeItem('biblioteca_usuario');
            if (!publica) {
                window.location.href = '/login';
            }
            return;
        }
        const resultado = await resposta.json();
        if (resultado.sucesso && resultado.usuario) {
            localStorage.setItem('biblioteca_usuario', JSON.stringify(resultado.usuario));
            renderizarSidebar(resultado.usuario);
            renderizarBadgeNotificacoes();
        }
    } catch (erro) {
        if (!publica) {
            window.location.href = '/login';
        }
    }
});
