document.addEventListener('DOMContentLoaded', function () {
        carregarRegras();
});

function carregarRegras() {
    API.get('/api/relatorios/regras-emprestimo')
        .then(data => {
            const tbody = document.getElementById('sobreRegrasBody');
            const categorias = data.categorias || [];
            if (categorias.length === 0) {
                tbody.innerHTML = '<tr><td colspan="3" class="empty-table">Nenhuma regra cadastrada.</td></tr>';
                return;
            }
            tbody.innerHTML = categorias.map(r => `
                <tr>
                    <td><strong>${escapeHtml(r.categoria)}</strong></td>
                    <td>${r.limite_livros} livros</td>
                    <td>${r.prazo_dias} dias</td>
                </tr>
            `).join('');
        })
        .catch(() => {
            const tbody = document.getElementById('sobreRegrasBody');
            if (tbody) tbody.innerHTML = '<tr><td colspan="3" class="empty-table">Não foi possível carregar as regras.</td></tr>';
        });
}
