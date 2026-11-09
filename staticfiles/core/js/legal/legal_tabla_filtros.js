// core/static/core/js/legal/legal_tabla_filtros.js

let chartLegalInstancia = null;
let datosLegalesAnalytics = [];
let estudiosStatsData = [];

document.addEventListener('DOMContentLoaded', () => {
    const legDataEl = document.getElementById('legales-analytics-data');
    const estDataEl = document.getElementById('estudios-stats-data');
    if (legDataEl) datosLegalesAnalytics = JSON.parse(legDataEl.textContent);
    if (estDataEl) estudiosStatsData = JSON.parse(estDataEl.textContent);

    document.querySelectorAll('.barra-winrate').forEach(barra => {
        barra.style.width = `${parseFloat(barra.dataset.winrate) || 0}%`;
    });
});

function aplicarFiltrosCausas() {
    const radioBloque = document.querySelector('input[name="radioBloqueLegal"]:checked');
    const bloqueElegido = radioBloque ? radioBloque.value : 'TODOS';
    const compElegida = document.getElementById('filtroLegalCompetencia').value;
    const estudioElegido = document.getElementById('filtroLegalEstudio').value;
    const estadoElegido = document.getElementById('filtroLegalEstado').value;
    const hallazgoElegido = document.getElementById('filtroLegalHallazgo').value;
    const busqueda = document.getElementById('buscadorCausasLegales').value.toLowerCase().trim();

    const filas = document.querySelectorAll('#tablaCausasLegales tbody tr');
    let visibles = 0, enProceso = 0, terminadas = 0, hallazgos = 0;
    let sumaClp = 0, sumaUf = 0;

    filas.forEach(fila => {
        const okBloque = (bloqueElegido === 'TODOS') || (fila.dataset.bloque === bloqueElegido);
        const okComp = (compElegida === 'TODOS') || (fila.dataset.competencia === compElegida);
        const okEstudio = (estudioElegido === 'TODOS') || (fila.dataset.estudio === estudioElegido);
        const okEstado = (estadoElegido === 'TODOS') || (fila.dataset.estado === estadoElegido);
        const okHallazgo = (hallazgoElegido === 'TODOS') || (fila.dataset.hallazgo === hallazgoElegido);
        const okTexto = (!busqueda) || fila.textContent.toLowerCase().includes(busqueda);

        if (okBloque && okComp && okEstudio && okEstado && okHallazgo && okTexto) {
            fila.style.display = '';
            visibles++;
            if ((fila.dataset.estado || '').toLowerCase() === 'en proceso') enProceso++;
            if ((fila.dataset.estado || '').toLowerCase() === 'terminada') terminadas++;
            if (fila.dataset.hallazgo === 'SI') hallazgos++;

            const monto = parseFloat(fila.dataset.provision) || 0;
            if (fila.dataset.moneda === 'CLP') sumaClp += monto;
            if (fila.dataset.moneda === 'UF') sumaUf += monto;
        } else {
            fila.style.display = 'none';
        }
    });

    document.getElementById('kpiLegalClp').textContent = '$' + Math.round(sumaClp).toLocaleString('es-CL');
    document.getElementById('kpiLegalUf').textContent = sumaUf.toLocaleString('es-CL', { minimumFractionDigits: 1, maximumFractionDigits: 1 }) + ' UF';
    document.getElementById('kpiLegalSubCausas').textContent = `${visibles} causas visibles`;
    document.getElementById('kpiLegalProceso').textContent = enProceso;
    document.getElementById('kpiLegalTerminadas').textContent = terminadas;
    document.getElementById('kpiLegalHallazgos').textContent = `🔍 ${hallazgos}`;
}

function limpiarFiltrosCausas() {
    document.getElementById('radBloqueTodos').checked = true;
    document.getElementById('filtroLegalCompetencia').value = 'TODOS';
    document.getElementById('filtroLegalEstudio').value = 'TODOS';
    document.getElementById('filtroLegalEstado').value = 'TODOS';
    document.getElementById('filtroLegalHallazgo').value = 'TODOS';
    document.getElementById('buscadorCausasLegales').value = '';
    aplicarFiltrosCausas();
}