let todosEmprestimos = [];
let paginaEmprestimo = 1;
const POR_PAGINA_EMPRESTIMO = 10;
let somenteAtivos = false;

const PRAZO_CATEGORIA = {};
const LIMITE_CATEGORIA = {};

document.addEventListener('DOMContentLoaded', function () {
        carregarRegras();
    carregarSelects();
    carregarEmprestimos();
    setupEmprestimoForm();
    setupSearchHistorico();

    const dataInput = document.getElementById('data_emprestimo');
    if (dataInput) dataInput.value = hojeISO();
});

function carregarRegras() {
    API.get('/api/relatorios/regras-emprestimo')
        .then(data => {
            const categorias = data.categorias || [];
            categorias.forEach(c => {
                PRAZO_CATEGORIA[c.categoria] = c.prazo_dias;
                LIMITE_CATEGORIA[c.categoria] = c.limite_livros;
            });
        })
        .catch(() => {});
}

function setupSearchHistorico() {
    const searchInput = document.getElementById('searchHistorico');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(() => { paginaEmprestimo = 1; renderizarEmprestimos(); }, 250));
    }

    const btn = document.getElementById('btnSomenteAtivos');
    if (btn) {
        btn.addEventListener('click', function () {
            somenteAtivos = !somenteAtivos;
            paginaEmprestimo = 1;
            btn.textContent = somenteAtivos ? 'Mostrar todos' : 'Somente ativos';
            btn.classList.toggle('btn-primary', somenteAtivos);
            btn.classList.toggle('btn-secondary', !somenteAtivos);
            renderizarEmprestimos();
        });
    }
}

function carregarSelects() {
    Promise.all([
        API.get('/api/usuarios'),
        API.get('/api/livros')
    ])
    .then(([usuarios, livros]) => {
        const selectUsuario = document.getElementById('usuario_id');
        const selectLivro = document.getElementById('livro_id');

        if (selectUsuario) {
            selectUsuario.innerHTML = '<option value="">Selecione um usuário...</option>';
            usuarios.forEach(u => {
                const opt = document.createElement('option');
                opt.value = u.id;
                opt.dataset.categoria = u.tipo_usuario;
                opt.dataset.ativos = u.emprestimos_ativos || 0;
                const suspenso = u.status === 'Suspenso' ? ' [SUSPENSO]' : '';
                opt.textContent = `${u.nome} (${u.tipo_usuario})${suspenso}`;
                if (u.status === 'Suspenso') opt.style.color = 'var(--oxblood)';
                selectUsuario.appendChild(opt);
            });
        }

        if (selectLivro) {
            const livrosDisponiveis = livros.filter(l => l.disponivel > 0);
            selectLivro.innerHTML = '<option value="">Selecione um livro...</option>';
            livrosDisponiveis.forEach(l => {
                const opt = document.createElement('option');
                opt.value = l.id;
                opt.textContent = `${l.titulo} - ${l.autor} (${l.disponivel} disp.)`;
                selectLivro.appendChild(opt);
            });
        }
    })
    .catch(err => showToast('Erro ao carregar dados: ' + err.message, 'error'));
}

function setupEmprestimoForm() {
    const form = document.getElementById('emprestimoForm');
    if (!form) return;

    const selectUsuario = document.getElementById('usuario_id');
    const dataEmprestimo = document.getElementById('data_emprestimo');
    const dataPrevista = document.getElementById('data_prevista_devolucao');
    const regrasBox = document.getElementById('regrasUsuarioBox');

    if (selectUsuario) {
        selectUsuario.addEventListener('change', function () {
            const opt = selectUsuario.selectedOptions[0];
            if (!opt || !opt.value) {
                regrasBox.style.display = 'none';
                return;
            }
            const categoria = opt.dataset.categoria || 'Discente Regular';
            const emUso = parseInt(opt.dataset.ativos) || 0;
            const limite = LIMITE_CATEGORIA[categoria] || 6;
            const prazo = PRAZO_CATEGORIA[categoria] || 7;

            const suspenso = opt.textContent.includes('[SUSPENSO]');
            if (suspenso) {
                regrasBox.className = 'suspensao-box';
                regrasBox.style.display = 'block';
                regrasBox.innerHTML = `<svg class="ic" aria-hidden="true"><use href="#i-alert"></use></svg>
                    <strong>Atenção:</strong> este usuário está <strong>suspenso</strong> e não pode realizar novos empréstimos.`;
            } else {
                regrasBox.className = 'regras-box';
                regrasBox.style.display = 'block';
                regrasBox.innerHTML = `
                    <p><strong>${categoria}</strong> — limite de <strong>${limite} livros</strong> · prazo de <strong>${prazo} dias</strong></p>
                    <p style="margin-top:6px">Empréstimos ativos: <strong>${emUso}/${limite}</strong></p>
                `;
            }

            if (dataEmprestimo.value) {
                const d = parseDateOnly(dataEmprestimo.value);
                const nova = new Date(d);
                nova.setDate(nova.getDate() + prazo);
                dataPrevista.value = nova.toISOString().split('T')[0];
            }
        });
    }

    if (dataEmprestimo) {
        dataEmprestimo.addEventListener('change', () => selectUsuario.dispatchEvent(new Event('change')));
    }

    form.addEventListener('submit', function (e) {
        e.preventDefault();

        const dados = {
            usuario_id: parseInt(selectUsuario.value),
            livro_id: parseInt(document.getElementById('livro_id').value),
            data_emprestimo: dataEmprestimo.value,
            data_prevista_devolucao: dataPrevista.value,
        };

        if (!dados.usuario_id || !dados.livro_id || !dados.data_emprestimo || !dados.data_prevista_devolucao) {
            showToast('Preencha todos os campos obrigatórios.', 'error');
            return;
        }

        showLoading();
        API.post('/api/emprestimos', dados)
            .then(data => {
                showToast(data.mensagem || 'Empréstimo registrado com sucesso!', 'success');
                form.reset();
                regrasBox.style.display = 'none';
                dataEmprestimo.value = hojeISO();
                carregarSelects();
                carregarEmprestimos();
            })
            .catch(err => showToast('Erro: ' + err.message, 'error'))
            .finally(() => hideLoading());
    });
}

function carregarEmprestimos() {
    const tbody = document.getElementById('emprestimosBody');
    if (!tbody) return;

    showLoading();
    skeletonTabela(8, 6, 'emprestimosBody');

    API.get('/api/emprestimos')
        .then(data => {
            todosEmprestimos = data;
            renderizarEmprestimos();
        })
        .catch(err => {
            tbody.innerHTML = `<tr><td colspan="8" class="empty-table">Erro ao carregar: ${escapeHtml(err.message)}</td></tr>`;
        })
        .finally(() => hideLoading());
}

function renderizarEmprestimos() {
    const tbody = document.getElementById('emprestimosBody');
    if (!tbody) return;

    const termo = (document.getElementById('searchHistorico').value || '').toLowerCase();

    let filtrados = todosEmprestimos.filter(e => {
        if (somenteAtivos && e.status !== 'Emprestado') return false;
        if (termo) {
            const texto = `${e.usuario_nome} ${e.livro_titulo}`.toLowerCase();
            if (!texto.includes(termo)) return false;
        }
        return true;
    });

    const totalPaginas = Math.max(1, Math.ceil(filtrados.length / POR_PAGINA_EMPRESTIMO));
    if (paginaEmprestimo > totalPaginas) paginaEmprestimo = totalPaginas;

    const pagina = paginar(filtrados, paginaEmprestimo, POR_PAGINA_EMPRESTIMO);
    tbody.innerHTML = '';

    if (pagina.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="empty-table">Nenhum empréstimo encontrado.</td></tr>';
        return;
    }

    pagina.forEach(e => {
        const hoje = new Date();
        const limite = parseDateOnly(e.data_prevista_devolucao);
        const atrasado = e.status === 'Emprestado' && hoje > limite;
        const status = atrasado ? 'Atrasado' : e.status;

        const podeRenovar = e.status === 'Emprestado' && !atrasado && e.renovacoes < 3;

        const tr = document.createElement('tr');
        tr.className = atrasado ? 'row-warning' : '';
        tr.innerHTML = `
            <td><strong>${escapeHtml(e.usuario_nome)}</strong></td>
            <td>${escapeHtml(e.livro_titulo)}</td>
            <td>${formatDate(e.data_emprestimo)}</td>
            <td>${formatDate(e.data_prevista_devolucao)}</td>
            <td>${e.data_devolucao ? formatDate(e.data_devolucao) : '-'}</td>
            <td><span class="status-badge ${e.renovacoes >= 3 ? 'status-danger' : 'status-info'}">${e.renovacoes}/3</span></td>
            <td>${getStatusBadge(status)}</td>
            <td>
                <div class="acoes-grupo">
                    ${e.status === 'Emprestado' ? `
                        ${podeRenovar ? `
                        <button class="btn btn-sm btn-secondary" onclick="renovarEmprestimo(${e.id})" title="Renovar" aria-label="Renovar empréstimo">
                            <svg class="ic" aria-hidden="true"><use href="#i-refresh"></use></svg> Renovar
                        </button>` : ''}
                        <a class="btn btn-sm btn-success" href="/devolucoes">
                            <svg class="ic" aria-hidden="true"><use href="#i-return"></use></svg> Devolver
                        </a>
                    ` : `<button class="btn btn-sm btn-secondary" onclick="verRenovacoes(${e.id})" title="Ver renovações" aria-label="Ver renovações">
                            <svg class="ic" aria-hidden="true"><use href="#i-history"></use></svg> Renovações
                        </button>`}
                </div>
            </td>
        `;
        tbody.appendChild(tr);
    });

    criarPaginacao('emprestimosPaginacao', paginaEmprestimo, totalPaginas, p => {
        paginaEmprestimo = p;
        renderizarEmprestimos();
    });
}

async function renovarEmprestimo(id) {
    const ok = await confirmar('Deseja renovar este empréstimo por mais um período? (máx. 3 renovações)', 'Renovar Empréstimo', '#i-refresh');
    if (!ok) return;

    showLoading();
    API.put(`/api/emprestimos/${id}`, { acao: 'renovar' })
        .then(data => {
            showToast(data.mensagem || 'Empréstimo renovado com sucesso!', 'success');
            carregarEmprestimos();
        })
        .catch(err => showToast('Erro: ' + err.message, 'error'))
        .finally(() => hideLoading());
}

function verRenovacoes(id) {
    showLoading();
    API.get(`/api/emprestimos/${id}/renovacoes`)
        .then(renovacoes => {
            const e = todosEmprestimos.find(x => x.id === id);
            let container = document.getElementById('renovacoesModal');
            if (!container) {
                container = document.createElement('div');
                container.id = 'renovacoesModal';
                container.className = 'modal';
                container.innerHTML = `
                    <div class="modal-content">
                        <div class="modal-header">
                            <h3><svg class="ic" aria-hidden="true"><use href="#i-refresh"></use></svg> Histórico de Renovações</h3>
                            <button class="modal-close" aria-label="Fechar"><svg class="ic" aria-hidden="true"><use href="#i-close"></use></svg></button>
                        </div>
                        <div class="modal-body" id="renovacoesBody"></div>
                    </div>
                `;
                document.body.appendChild(container);
                container.querySelector('.modal-close').addEventListener('click', () => fecharModal('renovacoesModal'));
                container.addEventListener('click', (ev) => { if (ev.target === container) fecharModal('renovacoesModal'); });
            }

            let html = `<p style="margin-bottom:12px;color:var(--ink-soft)">Empréstimo de <strong>${escapeHtml(e ? e.livro_titulo : '')}</strong></p>`;
            if (renovacoes.length === 0) {
                html += '<p class="empty-table">Nenhuma renovação registrada.</p>';
            } else {
                html += `<dl class="info-list">`;
                renovacoes.forEach(r => {
                    html += `
                        <div class="info-item" style="grid-column:1/-1;border-bottom:1px solid var(--line);padding-bottom:8px">
                            <dt>Renovação em</dt>
                            <dd>${formatDate(r.data_renovacao)} — nova previsão: <strong>${formatDate(r.nova_data_prevista)}</strong></dd>
                        </div>`;
                });
                html += '</dl>';
            }
            container.querySelector('#renovacoesBody').innerHTML = html;
            abrirModal('renovacoesModal');
        })
        .catch(err => showToast('Erro: ' + err.message, 'error'))
        .finally(() => hideLoading());
}
