// ===============================
// GRÁFICOS — barras e donut em SVG (sem dependências externas)
// ===============================

const PALETA = ['#2E6B4F', '#C7A24B', '#8A3624', '#3F6270', '#6E2A1B', '#3B8261', '#8A6A17', '#20503A'];

function lerCor(cssVar, fallback) {
    const el = document.body;
    const valor = getComputedStyle(el).getPropertyValue(cssVar).trim();
    return valor || fallback;
}

function configCores() {
    return {
        bg: 'transparent',
        grid: lerCor('--line', '#D6D4C6'),
        texto: lerCor('--ink-faint', '#7B7C6E'),
        ink: lerCor('--ink', '#26251E'),
        primaria: lerCor('--verdant', '#2E6B4F'),
        danger: lerCor('--oxblood', '#8A3624'),
        card: lerCor('--card', '#FBFAF5'),
    };
}


// -------------------------------
// GRÁFICO DE BARRAS
// -------------------------------
function renderBarChart(containerId, dados, opcoes = {}) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const cor = configCores();
    const largura = opcoes.largura || container.clientWidth || 500;
    const altura = opcoes.altura || 220;
    const rotuloAltura = 22;
    const pad = { top: 16, right: 8, bottom: rotuloAltura + 14, left: 40 };
    const areaLargura = largura - pad.left - pad.right;
    const areaAltura = altura - pad.top - pad.bottom;

    const maximo = Math.max(...dados.map(d => d.valor), 1);

    const barWidth = Math.max(8, (areaLargura / dados.length) * 0.55);
    const gap = areaLargura / dados.length;

    let svg = `<svg viewBox="0 0 ${largura} ${altura}" width="100%" height="${altura}" role="img" aria-label="${escapeHtml(opcoes.titulo || 'Gráfico de barras')}" preserveAspectRatio="none">`;

    // Linhas de grade + rótulos de valor
    const linhas = 4;
    for (let i = 0; i <= linhas; i++) {
        const y = pad.top + (areaAltura / linhas) * i;
        const valor = maximo - (maximo / linhas) * i;
        svg += `<line x1="${pad.left}" y1="${y}" x2="${largura - pad.right}" y2="${y}" stroke="${cor.grid}" stroke-width="1"/>`;
        svg += `<text x="${pad.left - 6}" y="${y + 4}" text-anchor="end" font-size="10" fill="${cor.texto}" font-family="monospace">${Math.round(valor)}</text>`;
    }

    // Barras
    dados.forEach((d, i) => {
        const x = pad.left + gap * i + (gap - barWidth) / 2;
        const h = (d.valor / maximo) * areaAltura;
        const y = pad.top + areaAltura - h;
        const fill = d.cor || PALETA[i % PALETA.length];
        svg += `<rect x="${x}" y="${y}" width="${barWidth}" height="${h}" rx="2" fill="${fill}" opacity="0.92"/>`;
        if (d.valor > 0) {
            svg += `<text x="${x + barWidth / 2}" y="${y - 5}" text-anchor="middle" font-size="10.5" fill="${cor.ink}" font-weight="600">${d.valor}</text>`;
        }
        svg += `<text x="${x + barWidth / 2}" y="${pad.top + areaAltura + 16}" text-anchor="middle" font-size="10" fill="${cor.texto}" font-family="monospace">${escapeHtml(d.rotulo)}</text>`;
    });

    svg += '</svg>';

    container.innerHTML = svg;
}


// -------------------------------
// GRÁFICO DONUT
// -------------------------------
function renderDonutChart(containerId, dados, opcoes = {}) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const cor = configCores();
    const tamanho = opcoes.tamanho || 200;
    const raio = (tamanho / 2) - 18;
    const circ = 2 * Math.PI * raio;

    const total = dados.reduce((s, d) => s + d.valor, 0);
    const centro = tamanho / 2;

    let svg = `<svg viewBox="0 0 ${tamanho} ${tamanho}" width="${tamanho}" height="${tamanho}" role="img" aria-label="${escapeHtml(opcoes.titulo || 'Gráfico de pizza')}">`;

    let acumulado = 0;
    dados.forEach((d, i) => {
        const frac = total > 0 ? d.valor / total : 0;
        const offset = acumulado * circ;
        const len = frac * circ;
        const fill = d.cor || PALETA[i % PALETA.length];
        svg += `<circle cx="${centro}" cy="${centro}" r="${raio}" fill="none" stroke="${fill}" stroke-width="22"
                 stroke-dasharray="${len} ${circ - len}" stroke-dashoffset="${-offset}" transform="rotate(-90 ${centro} ${centro})"/>`;
        acumulado += frac;
    });

    if (total > 0) {
        svg += `<text x="${centro}" y="${centro - 2}" text-anchor="middle" font-size="22" font-weight="700" fill="${cor.ink}" font-family="monospace">${total}</text>`;
        svg += `<text x="${centro}" y="${centro + 16}" text-anchor="middle" font-size="9" fill="${cor.texto}" font-family="monospace" letter-spacing="1">TOTAL</text>`;
    } else {
        svg += `<text x="${centro}" y="${centro}" text-anchor="middle" font-size="12" fill="${cor.texto}">Sem dados</text>`;
    }

    svg += '</svg>';

    // Legenda
    let legenda = '<ul class="chart-legend">';
    dados.forEach((d, i) => {
        const fill = d.cor || PALETA[i % PALETA.length];
        legenda += `<li><span class="legend-dot" style="background:${fill}"></span>${escapeHtml(d.rotulo)} <strong>${d.valor}</strong></li>`;
    });
    legenda += '</ul>';

    container.innerHTML = `<div class="donut-wrap">${svg}${legenda}</div>`;
}
