// core/static/core/js/legal/legal_graficos.js

function renderizarGraficoLegal() {
    const canvas = document.getElementById('canvasGraficoLegal');
    if (!canvas || datosLegalesAnalytics.length === 0) return;

    const tipo = document.getElementById('leg_tipo_grafico').value;
    const metrica = document.getElementById('leg_metrica_grafico').value;
    const selectBloque = document.getElementById('leg_bloque_grafico');
    const hallazgo = document.getElementById('leg_hallazgo_grafico').value;

    let bloqueEfectivo = selectBloque.value;
    if (tipo === 'motivos_civiles') bloqueEfectivo = 'CIVIL';
    else if (tipo === 'delitos_penales') bloqueEfectivo = 'PENAL';

    const muestra = datosLegalesAnalytics.filter(d => {
        const okBloque = (bloqueEfectivo === 'TODOS') || (d.bloque_legal === bloqueEfectivo);
        const okHall = (hallazgo === 'TODOS') || (d.hallazgo === hallazgo);
        if (tipo === 'motivos_civiles' && d.tipo_motivo_delito !== 'MOTIVO') return false;
        if (tipo === 'delitos_penales' && d.tipo_motivo_delito !== 'DELITO') return false;
        return okBloque && okHall;
    });

    document.getElementById('leg_resumen_grafico').textContent = `${muestra.length} causas analizadas`;

    let labels = [], valores = [], indexAxis = 'x', chartType = 'bar', titulo = '';

    if (tipo === 'winrate_estudio') {
        const mapa = {};
        muestra.forEach(d => {
            if (!mapa[d.estudio]) mapa[d.estudio] = { w: 0, t: 0 };
            if (d.resultado_win === 'A_FAVOR') { mapa[d.estudio].w++; mapa[d.estudio].t++; }
            else if (d.resultado_win === 'EN_CONTRA') { mapa[d.estudio].t++; }
        });
        const pares = Object.entries(mapa).filter(x => x[1].t > 0)
            .map(([k, v]) => [k, +((v.w / v.t) * 100).toFixed(1)])
            .sort((a, b) => b[1] - a[1]);
        labels = pares.map(p => p[0]);
        valores = pares.map(p => p[1]);
        indexAxis = 'y';
        titulo = 'Winrate (%) por Estudio Jurídico';
    } else {
        let campo = 'estudio';
        if (tipo === 'competencia') {
            campo = 'competencia';
            titulo = 'Distribución por Competencia';
        } else if (tipo === 'motivos_civiles') {
            campo = 'motivo_delito';
            titulo = '🏛️ Top Motivos de Demanda (Causas Civiles)';
            indexAxis = 'y';
        } else if (tipo === 'delitos_penales') {
            campo = 'motivo_delito';
            titulo = '⚖️ Top Delitos Investigados (Causas Penales)';
            indexAxis = 'y';
        } else if (tipo === 'evolucion_anual') {
            campo = 'anio_creacion';
            titulo = 'Evolución de Causas por Año de Creación';
        } else {
            campo = 'estudio';
            titulo = 'Provisión y Volumen por Estudio Jurídico';
            indexAxis = 'y';
        }

        const acum = {};
        muestra.forEach(d => {
            const k = d[campo] || 'Sin especificar';
            if (!acum[k]) acum[k] = 0;
            if (metrica === 'cantidad') acum[k] += 1;
            else if (metrica === 'clp' && d.moneda === 'CLP') acum[k] += d.provision;
            else if (metrica === 'uf' && d.moneda === 'UF') acum[k] += d.provision;
        });

        const pares = Object.entries(acum).sort((a, b) =>
            tipo === 'evolucion_anual' ? a[0].localeCompare(b[0]) : b[1] - a[1]
        );
        labels = pares.map(p => p[0]);
        valores = pares.map(p => p[1]);
    }

    document.getElementById('leg_titulo_grafico').textContent = titulo;

    if (chartLegalInstancia) chartLegalInstancia.destroy();
    chartLegalInstancia = new Chart(canvas.getContext('2d'), {
        type: chartType,
        data: {
            labels: labels,
            datasets: [{
                label: tipo === 'winrate_estudio' ? 'Winrate (%)' : metrica.toUpperCase(),
                data: valores,
                backgroundColor: tipo === 'delitos_penales' ? 'rgba(30, 34, 41, 0.85)' : 'rgba(215, 0, 42, 0.82)',
                borderColor: tipo === 'delitos_penales' ? '#1E2229' : '#A20620',
                borderWidth: 1,
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: indexAxis
        }
    });
}