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
        const liq = _extraerCampoFilaCmf(fila, ['liquidador']);
        if (liq && !IGNORAR_VALORES_CMF.has(liq.toUpperCase())) {
            conteoLiquidador[liq] = (conteoLiquidador[liq] || 0) + 1;
        }

        const rec = _extraerCampoFilaCmf(fila, ['reclamante', 'asegurado']);
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

const CONFIG_FILTROS_MULTI_CMF = {
    anio: {
        selector: '.check-cmf-anio',
        chkTodosId: 'chk_cmf_anio_todos',
        btnId: 'btnDropCmfAnio',
        textoTodos: 'Año (Todos)',
        textoNinguno: 'Sin año'
    },
    mes: {
        selector: '.check-cmf-mes',
        chkTodosId: 'chk_cmf_mes_todos',
        btnId: 'btnDropCmfMes',
        textoTodos: 'Mes (Todos)',
        textoNinguno: 'Sin mes'
    },
    motivo: {
        selector: '.check-cmf-motivo',
        chkTodosId: 'chk_cmf_motivo_todos',
        btnId: 'btnDropCmfMotivo',
        textoTodos: 'Motivo (Todos)',
        textoNinguno: 'Sin motivo'
    },
    estado: {
        selector: '.check-cmf-estado',
        chkTodosId: 'chk_cmf_estado_todos',
        btnId: 'btnDropCmfEstado',
        textoTodos: 'Estado (Todos)',
        textoNinguno: 'Sin estado'
    },
    ramo: {
        selector: '.check-cmf-ramo',
        chkTodosId: 'chk_cmf_ramo_todos',
        btnId: 'btnDropCmfRamo',
        textoTodos: 'Ramo (Todos)',
        textoNinguno: 'Sin ramo'
    }
};

function toggleTodosChecksFiltroCmf(tipo, marcado) {
    const cfg = CONFIG_FILTROS_MULTI_CMF[tipo];
    if (!cfg) return;
    document.querySelectorAll(cfg.selector).forEach(chk => {
        chk.checked = marcado;
    });
    actualizarDropdownFiltroCmf(tipo);
}

function actualizarDropdownFiltroCmf(tipo, omitirAplicar = false) {
    const cfg = CONFIG_FILTROS_MULTI_CMF[tipo];
    if (!cfg) return;

    const todos = document.querySelectorAll(cfg.selector);
    const marcados = Array.from(todos).filter(c => c.checked).map(c => c.value);

    const chkTodos = document.getElementById(cfg.chkTodosId);
    if (chkTodos) {
        chkTodos.checked = (todos.length > 0 && marcados.length === todos.length);
    }

    const btn = document.getElementById(cfg.btnId);
    if (btn) {
        if (marcados.length === todos.length) {
            btn.textContent = cfg.textoTodos;
        } else if (marcados.length === 0) {
            btn.textContent = cfg.textoNinguno;
        } else if (marcados.length === 1) {
            btn.textContent = marcados[0];
        } else {
            btn.textContent = `${marcados.length} seleccionados`;
        }
    }

    if (!omitirAplicar) {
        aplicarFiltrosConsolidado();
    }
}

function _cumpleMultiCheck(valorFila, checksNodeList) {
    const totalChecks = checksNodeList.length;
    if (totalChecks === 0) return true;
    const seleccionados = Array.from(checksNodeList).filter(c => c.checked).map(c => c.value);
    if (seleccionados.length === totalChecks) return true; // Si están todos marcados, incluye también vacíos/otros
    return seleccionados.includes(valorFila);
}

function aplicarFiltrosConsolidado() {
    const tabla = document.getElementById('tablaConsolidado');
    if (!tabla) return;

    const checksAnio = document.querySelectorAll('.check-cmf-anio');
    const checksMes = document.querySelectorAll('.check-cmf-mes');
    const checksMotivo = document.querySelectorAll('.check-cmf-motivo');
    const checksEstado = document.querySelectorAll('.check-cmf-estado');
    const checksRamo = document.querySelectorAll('.check-cmf-ramo');

    const anomaliaElegida = document.getElementById('filtroAnomalia').value;
    const busqueda = document.getElementById('buscadorConsolidado').value.toLowerCase().trim();

    const filas = tabla.querySelectorAll('tbody tr');
    let visibles = 0, anomaliasVisibles = 0;

    filas.forEach(fila => {
        const okAnio = _cumpleMultiCheck(fila.dataset.anio || '', checksAnio);
        const okMes = _cumpleMultiCheck(fila.dataset.mes || '', checksMes);
        const okMotivo = _cumpleMultiCheck(fila.dataset.motivo || '', checksMotivo);
        const okEstado = _cumpleMultiCheck(fila.dataset.estado || '', checksEstado);
        const okRamo = _cumpleMultiCheck(fila.dataset.ramo || '', checksRamo);
        const okAnom = (anomaliaElegida === 'TODOS') || (fila.dataset.anomalia === anomaliaElegida);
        const okTexto = (!busqueda) || fila.textContent.toLowerCase().includes(busqueda);

        if (okAnio && okMes && okMotivo && okEstado && okRamo && okAnom && okTexto) {
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
    Object.keys(CONFIG_FILTROS_MULTI_CMF).forEach(tipo => {
        const cfg = CONFIG_FILTROS_MULTI_CMF[tipo];
        document.querySelectorAll(cfg.selector).forEach(chk => chk.checked = true);
        actualizarDropdownFiltroCmf(tipo, true);
    });
    document.getElementById('filtroAnomalia').value = 'TODOS';
    document.getElementById('buscadorConsolidado').value = '';
    aplicarFiltrosConsolidado();
}