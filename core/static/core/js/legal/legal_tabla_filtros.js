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

function toggleBloqueLegal(chk) {
    const chkTodos = document.getElementById('chkBloqueTodos');
    const checksBloques = Array.from(document.querySelectorAll('.check-bloque-legal'));

    if (chk && chk.id === 'chkBloqueTodos') {
        checksBloques.forEach(c => c.checked = chkTodos.checked);
    } else if (chkTodos) {
        chkTodos.checked = checksBloques.every(c => c.checked);
    }
    aplicarFiltrosCausas();
}

const CONFIG_FILTROS_MULTI_LEGAL = {
    comp: {
        selector: '.check-legal-comp',
        chkTodosId: 'chk_leg_comp_todos',
        btnId: 'btnDropCompLegal',
        textoTodos: 'Competencia (Todas)',
        textoNinguno: 'Sin competencia'
    },
    estudio: {
        selector: '.check-legal-estudio',
        chkTodosId: 'chk_leg_estudio_todos',
        btnId: 'btnDropEstudioLegal',
        textoTodos: 'Estudio Jurídico (Todos)',
        textoNinguno: 'Sin estudio'
    },
    estado: {
        selector: '.check-legal-estado',
        chkTodosId: 'chk_leg_estado_todos',
        btnId: 'btnDropEstadoLegal',
        textoTodos: 'Estado (Todos)',
        textoNinguno: 'Sin estado'
    }
};

function toggleTodosChecksFiltroLegal(tipo, marcado) {
    const cfg = CONFIG_FILTROS_MULTI_LEGAL[tipo];
    if (!cfg) return;
    document.querySelectorAll(cfg.selector).forEach(chk => {
        chk.checked = marcado;
    });
    actualizarDropdownFiltroLegal(tipo);
}

function actualizarDropdownFiltroLegal(tipo, omitirAplicar = false) {
    const cfg = CONFIG_FILTROS_MULTI_LEGAL[tipo];
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
        aplicarFiltrosCausas();
    }
}

function aplicarFiltrosCausas() {
    const radioBloque = document.querySelector('input[name="radioBloqueLegal"]:checked');
    const bloqueElegido = radioBloque ? radioBloque.value : 'TODOS';

    const compsElegidas = Array.from(document.querySelectorAll('.check-legal-comp:checked')).map(c => c.value);
    const estudiosElegidos = Array.from(document.querySelectorAll('.check-legal-estudio:checked')).map(c => c.value);
    const estadosElegidos = Array.from(document.querySelectorAll('.check-legal-estado:checked')).map(c => c.value);

    const elHallazgo = document.getElementById('filtroLegalHallazgo');
    const hallazgoElegido = elHallazgo ? elHallazgo.value : 'TODOS';
    const busqueda = document.getElementById('buscadorCausasLegales').value.toLowerCase().trim();

    const filas = document.querySelectorAll('#tablaCausasLegales tbody tr');
    let visibles = 0, enProceso = 0, terminadas = 0, hallazgos = 0;
    let sumaClp = 0, sumaUf = 0;

    filas.forEach(fila => {
        const okBloque = (bloqueElegido === 'TODOS') || (fila.dataset.bloque === bloqueElegido);
        const okComp = compsElegidas.includes(fila.dataset.competencia);
        const okEstudio = estudiosElegidos.includes(fila.dataset.estudio);
        const okEstado = estadosElegidos.includes(fila.dataset.estado);
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
    const elKpiHallazgos = document.getElementById('kpiLegalHallazgos');
    if (elKpiHallazgos) elKpiHallazgos.textContent = `${hallazgos}`;
}

function limpiarFiltrosCausas() {
    document.getElementById('radBloqueTodos').checked = true;

    ['comp', 'estudio', 'estado'].forEach(tipo => {
        const cfg = CONFIG_FILTROS_MULTI_LEGAL[tipo];
        document.querySelectorAll(cfg.selector).forEach(chk => chk.checked = true);
        actualizarDropdownFiltroLegal(tipo, true);
    });

    const elHallazgo = document.getElementById('filtroLegalHallazgo');
    if (elHallazgo) elHallazgo.value = 'TODOS';
    document.getElementById('buscadorCausasLegales').value = '';
    aplicarFiltrosCausas();
}

// Añadir al final de core/static/core/js/legal/legal_tabla_filtros.js

const CONFIG_FILTROS_SISGEN = {
    motivo: {
        selector: '.check-sisgen-motivo',
        chkTodosId: 'chk_sis_motivo_todos',
        btnId: 'btnDropSisgenMotivo',
        textoTodos: 'Motivo - Delito (Todos)',
        textoNinguno: 'Sin motivo'
    },
    cia: {
        selector: '.check-sisgen-cia',
        chkTodosId: 'chk_sis_cia_todos',
        btnId: 'btnDropSisgenCia',
        textoTodos: 'Cía. SISGEN (Todas)',
        textoNinguno: 'Sin compañía'
    }
};

function toggleTodosChecksFiltroSisgen(tipo, marcado) {
    const cfg = CONFIG_FILTROS_SISGEN[tipo];
    if (!cfg) return;
    document.querySelectorAll(cfg.selector).forEach(chk => {
        chk.checked = marcado;
    });
    actualizarDropdownFiltroSisgen(tipo);
}

function actualizarDropdownFiltroSisgen(tipo, omitirAplicar = false) {
    const cfg = CONFIG_FILTROS_SISGEN[tipo];
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
        aplicarFiltrosSisgen();
    }
}

function _cumpleMultiCheckSisgen(valorFila, checksNodeList) {
    const total = checksNodeList.length;
    if (total === 0) return true;
    const marcados = Array.from(checksNodeList).filter(c => c.checked).map(c => c.value);
    if (marcados.length === total) return true; // Cuando están todos activos, incluye también filas sin Cía/Motivo
    return marcados.includes(valorFila);
}

function aplicarFiltrosSisgen() {
    const tabla = document.getElementById('tablaQuerellasSisgen');
    if (!tabla) return;

    const radioCruce = document.querySelector('input[name="radioCruceSisgen"]:checked');
    const cruceElegido = radioCruce ? radioCruce.value : 'TODOS';

    const checksMotivo = document.querySelectorAll('.check-sisgen-motivo');
    const checksCia = document.querySelectorAll('.check-sisgen-cia');
    const busqueda = (document.getElementById('buscadorQuerellasSisgen')?.value || '').toLowerCase().trim();

    const filas = tabla.querySelectorAll('tbody tr');
    let visibles = 0, conCruce = 0, sinCruce = 0;
    const conteoCias = {};

    filas.forEach(fila => {
        const okCruce = (cruceElegido === 'TODOS') || (fila.dataset.cruce === cruceElegido);
        const okMotivo = _cumpleMultiCheckSisgen(fila.dataset.motivo || '', checksMotivo);
        const okCia = _cumpleMultiCheckSisgen(fila.dataset.cia || '', checksCia);
        const okTexto = (!busqueda) || fila.textContent.toLowerCase().includes(busqueda);

        if (okCruce && okMotivo && okCia && okTexto) {
            fila.style.display = '';
            visibles++;
            if (fila.dataset.cruce === 'SI') conCruce++;
            else sinCruce++;

            const ciaVal = (fila.dataset.cia || '').trim();
            if (ciaVal) conteoCias[ciaVal] = (conteoCias[ciaVal] || 0) + 1;
        } else {
            fila.style.display = 'none';
        }
    });

    const topCiaEntry = Object.entries(conteoCias).sort((a, b) => b[1] - a[1])[0];

    document.getElementById('kpiSisgenTotal').textContent = visibles;
    document.getElementById('kpiSisgenSubTotal').textContent = `${visibles} registros visibles`;
    document.getElementById('kpiSisgenConCruce').textContent = conCruce;
    document.getElementById('kpiSisgenSinCruce').textContent = sinCruce;
    const elTopCia = document.getElementById('kpiSisgenTopCia');
    if (elTopCia) {
        elTopCia.textContent = topCiaEntry ? `${topCiaEntry[0]} (${topCiaEntry[1]})` : 'Sin registros';
    }
}

function limpiarFiltrosSisgen() {
    const radTodos = document.getElementById('radSisgenTodos');
    if (radTodos) radTodos.checked = true;

    ['motivo', 'cia'].forEach(tipo => {
        const cfg = CONFIG_FILTROS_SISGEN[tipo];
        document.querySelectorAll(cfg.selector).forEach(chk => chk.checked = true);
        actualizarDropdownFiltroSisgen(tipo, true);
    });

    const inputBusq = document.getElementById('buscadorQuerellasSisgen');
    if (inputBusq) inputBusq.value = '';
    aplicarFiltrosSisgen();
}

function abrirModalSisgenCrear() {
    document.getElementById('formQuerellaSisgen').reset();
    document.getElementById('inputAccionSisgen').value = 'crear_querella_sisgen';
    document.getElementById('inputFilaSisgen').value = '';
    document.getElementById('tituloModalSisgen').textContent = 'Nuevo Registro - QUERELLAS VS SISGEN';
    new bootstrap.Modal(document.getElementById('modalQuerellaSisgen')).show();
}

function abrirModalSisgenEditar(btn) {
    const d = btn.dataset;
    document.getElementById('inputAccionSisgen').value = 'editar_querella_sisgen';
    document.getElementById('inputFilaSisgen').value = d.fila;
    document.getElementById('tituloModalSisgen').textContent = `Editar Registro ${d.id || ''} (Fila #${d.fila})`;

    document.getElementById('sis_siniestro').value = d.siniestro || '';
    document.getElementById('sis_motivo').value = d.motivo || '';
    document.getElementById('sis_parte').value = d.parte || 'Querellante';
    document.getElementById('sis_rotulado').value = d.rotulado || '';
    document.getElementById('sis_asegurado').value = d.asegurado || '';
    document.getElementById('sis_rut').value = d.rut || '';
    document.getElementById('sis_ultimosin').value = d.ultimosin || '';
    document.getElementById('sis_fechasisgen').value = d.fechasisgen || '';
    document.getElementById('sis_cia').value = d.cia || '';
    document.getElementById('sis_observaciones').value = d.observaciones || '';

    new bootstrap.Modal(document.getElementById('modalQuerellaSisgen')).show();
}