document.addEventListener('DOMContentLoaded', async function () {
    const usuario = await verificarSessao();
    if (!usuario) return;

    const staff = usuario.perfil === 'Administrador' || usuario.perfil === 'Bibliotecário';

    if (staff) {
        carregarDashboard();
    } else {
        carregarDashboardLeitor(usuario);
    }
});

async function verificarSessao() {
    try {
        const resposta = await fetch('/api/usuario');
        if (resposta.status === 401) {
            window.location.href = '/login';
            return false;
        }
        const resultado = await resposta.json();
        if (resultado.sucesso && resultado.usuario) {
            return resultado.usuario;
        }
        window.location.href = '/login';
        return false;
    } catch (erro) {
        window.location.href = '/login';
        return false;
    }
}

async function carregarDashboardLeitor(usuario) {
    const areaStaff = document.getElementById('areaStaff');
    const areaLeitor = document.getElementById('areaLeitor');
    const actions = document.getElementById('pageHeadActions');
    const desc = document.getElementById('pageHeadDescricao');

    if (areaStaff) areaStaff.style.display = 'none';
    if (areaLeitor) areaLeitor.style.display = '';
    if (actions) actions.style.display = 'none';
    if (desc) desc.textContent = 'Acompanhe seus empréstimos, reservas e notificações';

    showLoading();
    try {
        const [emprestimos, reservas, notificacoes] = await Promise.all([
            API.get('/api/emprestimos/ativos'),
            API.get('/api/reservas'),
            API.get('/api/notificacoes/nao-lidas'),
        ]);

        const emprestimosArea = Array.isArray(emprestimos) ? emprestimos : [];
        const reservasArea = Array.isArray(reservas) ? reservas : [];
        const reservasAtivas = reservasArea.filter(r => r.status === 'Ativa');
        const atrasados = emprestimosArea.filter(e => (e.dias_atraso || 0) > 0);

        document.getElementById('leitorEmprestimosAtivos').textContent = emprestimosArea.length;
        document.getElementById('leitorReservas').textContent = reservasAtivas.length;
        document.getElementById('leitorAtrasados').textContent = atrasados.length;
        document.getElementById('leitorNotificacoes').textContent = notificacoes.nao_lidas || 0;

        const alerta = document.getElementById('alertaAtrasadosLeitor');
        if (atrasados.length > 0) {
            alerta.style.display = 'flex';
            document.getElementById('alertaAtrasadosLeitorText').innerHTML =
                `<strong>Atenção:</strong> você tem ${atrasados.length} livro(s) em atraso. Procure a biblioteca para devolvê-los.`;
        }

        const tbody = document.getElementById('leitorEmprestimosBody');
        tbody.innerHTML = '';
        if (emprestimosArea.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" class="empty-table">Nenhum empréstimo ativo no momento.</td></tr>';
        } else {
            emprestimosArea.forEach(e => {
                const atrasado = (e.dias_atraso || 0) > 0;
                const tr = document.createElement('tr');
                if (atrasado) tr.className = 'row-warning';
                tr.innerHTML = `
                    <td>${escapeHtml(e.livro_titulo)}</td>
                    <td>${formatDate(e.data_emprestimo)}</td>
                    <td>${formatDate(e.data_prevista_devolucao)}</td>
                    <td>${getStatusBadge(atrasado ? 'Atrasado' : e.status)}</td>
                `;
                tbody.appendChild(tr);
            });
        }

        const rbody = document.getElementById('leitorReservasBody');
        rbody.innerHTML = '';
        if (reservasArea.length === 0) {
            rbody.innerHTML = '<tr><td colspan="3" class="empty-table">Nenhuma reserva encontrada.</td></tr>';
        } else {
            reservasArea.slice(0, 8).forEach(r => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${escapeHtml(r.livro_titulo)}</td>
                    <td>${formatDate(r.data_reserva)}</td>
                    <td>${getStatusBadge(r.status)}</td>
                `;
                rbody.appendChild(tr);
            });
        }
    } catch (erro) {
        showToast('Erro ao carregar seus dados: ' + erro.message, 'error');
    } finally {
        hideLoading();
    }
}

async function carregarDashboard() {
    showLoading();

    try {
        const resposta = await fetch('/api/dashboard');

        if (resposta.status === 401) {
            window.location.href = '/login';
            return;
        }

        const resultado = await resposta.json();

        if (!resposta.ok || !resultado.sucesso) {
            throw new Error(resultado.erro || 'Erro ao carregar dashboard.');
        }

        const dados = resultado.dados;

        document.getElementById('totalLivros').textContent = dados.totalLivros;
        document.getElementById('totalUsuarios').textContent = dados.totalUsuarios;
        document.getElementById('emprestimosAtivos').textContent = dados.emprestimosAtivos;
        document.getElementById('livrosAtrasados').textContent = dados.livrosAtrasados;
        document.getElementById('reservasAtivas').textContent = dados.reservasAtivas;
        document.getElementById('devolucoesRealizadas').textContent = dados.devolucoesRealizadas;
        document.getElementById('livrosDisponiveis').textContent = dados.livrosDisponiveis;
        document.getElementById('livrosIndisponiveis').textContent = dados.livrosIndisponiveis;
        document.getElementById('usuariosSuspensos').textContent = dados.usuariosSuspensos;

        const alerta = document.getElementById('alertaAtrasados');
        if (dados.livrosAtrasados > 0) {
            alerta.style.display = 'flex';
            document.getElementById('alertaAtrasadosText').innerHTML =
                `<strong>Atenção:</strong> ${dados.livrosAtrasados} empréstimo(s) em atraso. ` +
                `${dados.usuariosSuspensos} usuário(s) suspenso(s) por penalidades.`;
        }

        renderBarChart('chartEmprestimosMes',
            (dados.emprestimosMes || []).map(m => ({ rotulo: m.mes, valor: m.total })),
            { titulo: 'Empréstimos por mês', altura: 230 });

        renderBarChart('chartLivrosTop',
            (dados.livrosMaisEmprestados || []).map(l => ({ rotulo: l.titulo, valor: l.total })),
            { titulo: 'Livros mais emprestados', altura: 230 });

        renderDonutChart('chartAcervo',
            (dados.acervoCategoria || []).map(c => ({ rotulo: c.categoria, valor: c.total })),
            { titulo: 'Acervo por categoria', tamanho: 180 });

        renderDonutChart('chartEmprestimosCategoria',
            (dados.emprestimosCategoria || []).map(c => ({ rotulo: c.categoria, valor: c.total })),
            { titulo: 'Empréstimos por categoria', tamanho: 180 });

        preencherUltimosEmprestimos(dados.ultimosEmprestimos || []);
        preencherAtrasados(dados.livrosAtrasadosLista || []);

    } catch (erro) {
        showToast('Erro ao carregar dashboard: ' + erro.message, 'error');
    } finally {
        hideLoading();
    }
}

function preencherUltimosEmprestimos(emprestimos) {
    const tbody = document.getElementById('emprestimosBody');
    if (!tbody) return;

    tbody.innerHTML = '';

    if (emprestimos.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="empty-table">Nenhum empréstimo registrado.</td></tr>';
        return;
    }

    emprestimos.forEach(e => {
        const hoje = new Date();
        const limite = parseDateOnly(e.data_prevista_devolucao);
        const atrasado = e.status === 'Emprestado' && hoje > limite;
        const status = atrasado ? 'Atrasado' : e.status;

        const tr = document.createElement('tr');
        tr.className = atrasado ? 'row-warning' : '';
        tr.innerHTML = `
            <td>${escapeHtml(e.usuario_nome)}</td>
            <td>${escapeHtml(e.livro_titulo)}</td>
            <td>${formatDate(e.data_emprestimo)}</td>
            <td>${formatDate(e.data_prevista_devolucao)}</td>
            <td>${getStatusBadge(status)}</td>
        `;
        tbody.appendChild(tr);
    });
}

function preencherAtrasados(atrasados) {
    const tbody = document.getElementById('atrasadosBody');
    if (!tbody) return;

    tbody.innerHTML = '';

    if (atrasados.length === 0) {
        tbody.innerHTML = '<tr><td colspan="3" class="empty-table">Nenhum livro em atraso.</td></tr>';
        return;
    }

    atrasados.forEach(e => {
        const tr = document.createElement('tr');
        tr.className = 'row-warning';
        tr.innerHTML = `
            <td><strong>${escapeHtml(e.livro_titulo)}</strong></td>
            <td>${escapeHtml(e.usuario_nome)}</td>
            <td><span class="status-badge status-danger">${e.dias_atraso} dia(s)</span></td>
        `;
        tbody.appendChild(tr);
    });
}
