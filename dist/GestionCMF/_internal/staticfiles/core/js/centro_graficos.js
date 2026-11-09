// core/static/core/js/3_centro_graficos.js

document.addEventListener('DOMContentLoaded', () => {
    inicializarCentroGraficos();
});

function inicializarCentroGraficos() {
    const analyticsEl = document.getElementById('analytics-data');
    if (analyticsEl) {
        datosAnalytics = JSON.parse(analyticsEl.textContent);
    }

    const tabGraficos = document.getElementById('graficos-tab');
    if (tabGraficos) {
        tabGraficos.addEventListener('shown.bs.tab', () => {
            renderizarGraficoAvanzado();
        });
    }
}

function contarAgrupado(lista, claveGrupo, modoMetrica) {
    const mapa = {};
    lista.forEach(item => {
        const k = item[claveGrupo] || 'Sin especificar';
        if (!mapa[k]) mapa[k] = new Set();
        if (modoMetrica === 'oficios' && item.oficio) {
            mapa[k].add(item.oficio);
        } else {
            mapa[k].add(Symbol());
        }
    });
    const resultado = {};
    Object.keys(mapa).forEach(k => resultado[k] = mapa[k].size);
    return resultado;
}

function actualizarFiltroRamosGrafico() {
    const todosChecks = document.querySelectorAll('.check-ramo-grafico');
    const seleccionados = Array.from(todosChecks)
        .filter(chk => chk.checked)
        .map(chk => chk.value === 'SIN_RAMO' ? 'Sin Ramo' : chk.value);

    const btn = document.getElementById('btnDropdownRamos');
    if (btn) {
        if (seleccionados.length === todosChecks.length) {
            btn.textContent = 'Todos seleccionados';
        } else if (seleccionados.length === 0) {
            btn.textContent = 'Ningún ramo';
        } else {
            btn.textContent = seleccionados.join(', ');
        }
    }
    renderizarGraficoAvanzado();
}

function renderizarGraficoAvanzado() {
    const canvasAvanzado = document.getElementById('graficoAvanzado');
    if (!canvasAvanzado || datosAnalytics.length === 0) return;

    const tipoReporte = document.getElementById('g_tipo_reporte').value;
    const selectMetrica = document.getElementById('g_metrica');
    const anioFiltro = document.getElementById('g_anio').value;
    const anomFiltro = document.getElementById('g_anomalia').value;
    const ramosSeleccionados = Array.from(document.querySelectorAll('.check-ramo-grafico:checked'))
        .map(chk => chk.value);

    let modoMetrica = 'filas';
    if (selectMetrica) {
        selectMetrica.disabled = (tipoReporte === 'promedio_dias');
        modoMetrica = selectMetrica.value;
    }

    const filtrados = datosAnalytics.filter(d => {
        const okAnio = (anioFiltro === 'TODOS') || (d.anio === anioFiltro);
        const okRamo = ramosSeleccionados.includes(d.ramo);
        const okAnom = (anomFiltro === 'TODOS') || (d.anomalia === anomFiltro);
        return okAnio && okRamo && okAnom;
    });

    const oficiosUnicos = new Set(filtrados.map(d => d.oficio).filter(Boolean)).size;
    document.getElementById('g_resumen_muestra').textContent =
        `${filtrados.length} registros | ${oficiosUnicos} oficios únicos`;

    let chartType = 'bar';
    let labels = [];
    let valores = [];
    let indexAxis = 'x';
    let colores = 'rgba(215, 0, 42, 0.8)';
    let titulo = '';

    if (tipoReporte === 'motivos') {
        const conteo = contarAgrupado(filtrados, 'motivo', modoMetrica);
        const top10 = Object.entries(conteo).sort((a, b) => b[1] - a[1]).slice(0, 10);
        labels = top10.map(x => x[0]);
        valores = top10.map(x => x[1]);
        indexAxis = 'y';
        titulo = 'Top 10 Motivos del Reclamo';
    } else if (tipoReporte === 'evolucion_mensual') {
        const conteo = contarAgrupado(filtrados, 'mes', modoMetrica);
        labels = MESES_CORTOS;
        valores = MESES_CORTOS.map(m => conteo[m] || 0);
        chartType = 'line';
        titulo = 'Evolución Mensual de Reclamos (Ene - Dic)';
    } else if (tipoReporte === 'evolucion_anual') {
        const conteo = contarAgrupado(filtrados, 'anio', modoMetrica);
        labels = Object.keys(conteo).filter(a => a !== '').sort();
        valores = labels.map(a => conteo[a]);
        titulo = 'Comparativa de Reclamos por Año CMF';
    } else if (tipoReporte === 'sla_demora') {
        const validosSla = filtrados.filter(d => d.rango_demora && d.rango_demora !== '-');
        const conteo = contarAgrupado(validosSla, 'rango_demora', modoMetrica);
        labels = ORDEN_SLA;
        valores = ORDEN_SLA.map(s => conteo[s] || 0);
        colores = ['#198754', '#20c997', '#ffc107', '#fd7e14', '#dc3545', '#842029'];
        titulo = 'Cumplimiento de Plazos (Rango de Demora)';
    } else if (tipoReporte === 'calidad_respuesta') {
        const conteo = contarAgrupado(filtrados, 'estado', modoMetrica);
        const valoresBrutos = Object.values(conteo);
        const totalMuestra = valoresBrutos.reduce((acc, v) => acc + v, 0);

        labels = Object.keys(conteo).map((estado, idx) => {
            const pct = totalMuestra > 0 ? ((valoresBrutos[idx] / totalMuestra) * 100).toFixed(1) : '0.0';
            return `${estado} (${pct}%)`;
        });
        valores = valoresBrutos;
        chartType = 'doughnut';
        colores = ['#198754', '#0d6efd', '#fd7e14', '#D7002A', '#6c757d'];
        titulo = 'Distribución por Estado / Calidad de Respuesta';
    } else if (tipoReporte === 'promedio_dias') {
        const sumaPorAnio = {};
        filtrados.forEach(d => {
            if (d.dias_cmf_fid !== null && d.anio) {
                if (!sumaPorAnio[d.anio]) sumaPorAnio[d.anio] = { suma: 0, n: 0 };
                sumaPorAnio[d.anio].suma += d.dias_cmf_fid;
                sumaPorAnio[d.anio].n += 1;
            }
        });
        labels = Object.keys(sumaPorAnio).sort();
        valores = labels.map(a => +(sumaPorAnio[a].suma / sumaPorAnio[a].n).toFixed(1));
        colores = 'rgba(30, 34, 41, 0.85)';
        titulo = 'Promedio de Días de Respuesta (CMF vs FID) por Año';
    }

    document.getElementById('g_titulo_dinamico').textContent = titulo;

    if (chartAvanzadoInstancia) {
        chartAvanzadoInstancia.destroy();
    }

    const ctx = canvasAvanzado.getContext('2d');
    const pluginsActivos = (chartType === 'doughnut' && typeof ChartDataLabels !== 'undefined')
        ? [ChartDataLabels] : [];

    chartAvanzadoInstancia = new Chart(ctx, {
        type: chartType,
        plugins: pluginsActivos,
        data: {
            labels: labels,
            datasets: [{
                label: tipoReporte === 'promedio_dias'
                    ? 'Promedio Días'
                    : (modoMetrica === 'oficios' ? 'Oficios Únicos' : 'Total Registros'),
                data: valores,
                backgroundColor: colores,
                borderColor: chartType === 'line' ? '#D7002A' : (chartType === 'doughnut' ? '#FFFFFF' : undefined),
                borderWidth: chartType === 'doughnut' ? 2 : 1,
                tension: 0.25,
                fill: chartType === 'line'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: indexAxis,
            plugins: {
                legend: { position: chartType === 'doughnut' ? 'right' : 'top' },
                datalabels: {
                    color: '#FFFFFF',
                    font: {
                        family: 'Montserrat, sans-serif',
                        weight: 'bold',
                        size: 13
                    },
                    display: function(context) {
                        const dataset = context.dataset.data;
                        const total = dataset.reduce((acc, val) => acc + val, 0);
                        const valor = dataset[context.dataIndex];
                        return total > 0 && ((valor / total) * 100) >= 3;
                    },
                    formatter: function(value, context) {
                        const total = context.chart.data.datasets[0].data.reduce((a, b) => a + b, 0);
                        const pct = total > 0 ? ((value / total) * 100).toFixed(1) : '0.0';
                        return `${pct}%`;
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const valor = context.raw || 0;
                            if (tipoReporte === 'promedio_dias') {
                                return ` Promedio: ${valor} días`;
                            }
                            const sumaTotal = context.dataset.data.reduce((a, b) => a + b, 0);
                            const pct = sumaTotal > 0 ? ((valor / sumaTotal) * 100).toFixed(1) : '0.0';
                            const unidad = modoMetrica === 'oficios' ? 'oficios' : 'registros';
                            return ` ${valor} ${unidad} (${pct}%)`;
                        }
                    }
                }
            }
        }
    });
}