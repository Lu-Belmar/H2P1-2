// core/static/core/js/tabla_kpis.js

const IGNORAR_VALORES_CMF = new Set(['', '-', 'N/A', 'NO APLICA', 'SIN DATO', 'NONE', 'NO', 'S/I', 'SIN INFORMACION', 'SIN INFORMACIÓN']);

document.addEventListener('DOMContentLoaded', () => {
    aplicarFiltrosConsolidado();
});

function _extraerCampoFilaCmf(fila, nombresAtributo) {
    for (const attr of nombresAtributo) {
        if (fila.dataset[attr]) return fila.dataset[attr].trim();
    }
    const btnEditar = fila.querySelector('button[onclick*="abrirModalEditar"]');
    if (btnEditar) {
        for (const attr of nombresAtributo) {
            if (btnEditar.dataset[attr]) return btnEditar.dataset[attr].trim();
        }
    }
    return '';
}

function actualizarTopLiquidadorYReclamante() {
    const filasVisibles = Array.from(document.querySelectorAll('#tablaConsolidado tbody tr'))
        .filter(tr => tr.style.display !== 'none');

    const conteoLiquidador = {};
    const conteoReclamante = {};

    filasVisibles.forEach(fila => {
        const liq = _extraerCampoFilaCmf(fila, ['liquidador', 'liqtaller', 'liquidadortaller', 'taller']);
        if (liq && !IGNORAR_VALORES_CMF.has(liq.toUpperCase())) {
            conteoLiquidador[liq] = (conteoLiquidador[liq] || 0) + 1;
        }

        const rec = _extraerCampoFilaCmf(fila, ['reclamante', 'asegurado', 'nombrereclamante', 'corredor']);
        if (rec && !IGNORAR_VALORES_CMF.has(rec.toUpperCase())) {
            conteoReclamante[rec] = (conteoReclamante[rec] || 0) + 1;
        }
    });

    const topLiq = Object.entries(conteoLiquidador).sort((a, b) => b[1] - a[1])[0];
    const topRec = Object.entries(conteoReclamante).sort((a, b) => b[1] - a[1])[0];

    const elLiqNom = document.getElementById('kpiTopLiquidadorNombre');
    const elLiqCant = document.getElementById('kpiTopLiquidadorCant');
    if (elLiqNom && elLiqCant) {
        elLiqNom.textContent = topLiq ? topLiq[0] : 'Sin registros';
        elLiqNom.title = topLiq ? topLiq[0] : '';
        elLiqCant.textContent = `${topLiq ? topLiq[1] : 0} menc.`;
    }

    const elRecNom = document.getElementById('kpiTopReclamanteNombre');
    const elRecCant = document.getElementById('kpiTopReclamanteCant');
    if (elRecNom && elRecCant) {
        elRecNom.textContent = topRec ? topRec[0] : 'Sin registros';
        elRecNom.title = topRec ? topRec[0] : '';
        elRecCant.textContent = `${topRec ? topRec[1] : 0} recl.`;
    }
}

function aplicarFiltrosConsolidado() {
    const anioElegido = document.getElementById('filtroAnio').value;
    const mesElegido = document.getElementById('filtroMes').value;
    const anomaliaElegida = document.getElementById('filtroAnomalia').value;
    const busqueda = document.getElementById('buscadorConsolidado').value.toLowerCase().trim();

    const filas = document.querySelectorAll('#tablaConsolidado tbody tr');
    let visibles = 0, anomaliasVisibles = 0;

    filas.forEach(fila => {
        const okAnio = (anioElegido === 'TODOS') || (fila.dataset.anio === anioElegido);
        const okMes = (mesElegido === 'TODOS') || (fila.dataset.mes === mesElegido);
        const okAnom = (anomaliaElegida === 'TODOS') || (fila.dataset.anomalia === anomaliaElegida);
        const okTexto = (!busqueda) || fila.textContent.toLowerCase().includes(busqueda);

        if (okAnio && okMes && okAnom && okTexto) {
            fila.style.display = '';
            visibles++;
            if (fila.dataset.anomalia === 'SI') anomaliasVisibles++;
        } else {
            fila.style.display = 'none';
        }
    });

    document.getElementById('kpiTotalOficios').textContent = visibles;
    document.getElementById('kpiSubTotal').textContent = `${visibles} registros visibles`;
    document.getElementById('kpiTotalAnomalias').textContent = anomaliasVisibles;

    actualizarTopLiquidadorYReclamante();
}

function limpiarFiltrosConsolidado() {
    document.getElementById('filtroAnio').value = 'TODOS';
    document.getElementById('filtroMes').value = 'TODOS';
    document.getElementById('filtroAnomalia').value = 'TODOS';
    document.getElementById('buscadorConsolidado').value = '';
    aplicarFiltrosConsolidado();
}