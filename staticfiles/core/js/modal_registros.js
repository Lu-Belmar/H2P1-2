// core/static/core/js/4_modal_registro.js
// f(echa)CMFString, d(ate)Cmf
function recalcularFormulasModal() {
    const fCmfStr = document.getElementById('f_fcmf').value;
    const fLimStr = document.getElementById('f_flimite').value;
    const fFidStr = document.getElementById('f_ffid').value;

    const dCmf = fCmfStr ? new Date(fCmfStr + 'T00:00:00') : null;
    const dLim = fLimStr ? new Date(fLimStr + 'T00:00:00') : null;
    const dFid = fFidStr ? new Date(fFidStr + 'T00:00:00') : null;

    document.getElementById('calc_cmf').textContent = dCmf
        ? `${MESES_CORTOS[dCmf.getMonth()]} / ${dCmf.getFullYear()}` : '-';

    document.getElementById('calc_fid').textContent = dFid
        ? `${MESES_CORTOS[dFid.getMonth()]} / ${dFid.getFullYear()}` : '- / -';

    if (dFid && dCmf) {
        const diffL = Math.round((dFid - dCmf) / (1000 * 60 * 60 * 24));
        document.getElementById('calc_l').textContent = `${diffL} días`;
    } else {
        document.getElementById('calc_l').textContent = '-';
    }

    if (dFid && dLim) {
        const diffM = Math.round((dFid - dLim) / (1000 * 60 * 60 * 24));
        document.getElementById('calc_m').textContent = `${diffM} días`;

        let rango = '-';
        if (diffM === 0) rango = 'Sin retraso';
        else if (diffM >= 1 && diffM <= 3) rango = 'De 1 a 3 días de retraso';
        else if (diffM >= 4 && diffM <= 7) rango = 'De 4 a 7 días de retraso';
        else if (diffM >= 8 && diffM <= 10) rango = 'De 7 a 10 días de retraso';
        else if (diffM > 10) rango = 'Más de 10 días de retraso';
        else if (diffM < 0) rango = 'Respuesta enviada antes de la fecha límite';

        document.getElementById('calc_n').textContent = rango;
    } else {
        document.getElementById('calc_m').textContent = '-';
        document.getElementById('calc_n').textContent = '-';
    }
}

function textoTieneAnomalia(texto) {
    const limpio = (texto || '').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
    return limpio.includes('anomal');
}

function toggleAnomaliaInput() {
    const check = document.getElementById('f_check_anomalia');
    const inputObs = document.getElementById('f_observaciones');
    let valor = inputObs.value.trim();

    if (check.checked) {
        if (!textoTieneAnomalia(valor)) {
            inputObs.value = valor ? `${valor} / Anomalía` : 'Anomalía';
        }
    } else {
        valor = valor
            .replace(/\s*\/\s*anomal[ií]as?/gi, '')
            .replace(/anomal[ií]as?\s*\/\s*/gi, '')
            .replace(/^anomal[ií]as?$/gi, '')
            .trim();
        inputObs.value = valor;
    }
}

function sincronizarCheckDesdeTexto() {
    const valor = document.getElementById('f_observaciones').value;
    document.getElementById('f_check_anomalia').checked = textoTieneAnomalia(valor);
}

function abrirModalCrear() {
    document.getElementById('formRegistro').reset();
    document.getElementById('inputAccion').value = 'crear_registro';
    document.getElementById('inputFilaExcel').value = '';
    document.getElementById('tituloModal').textContent = '➕ Crear Nuevo Registro en Tabla consolidado';
    document.getElementById('f_check_anomalia').checked = false;
    recalcularFormulasModal();
    new bootstrap.Modal(document.getElementById('modalRegistro')).show();
}

function abrirModalEditar(btn) {
    const d = btn.dataset;
    document.getElementById('inputAccion').value = 'editar_registro';
    document.getElementById('inputFilaExcel').value = d.fila;
    document.getElementById('tituloModal').textContent = `✏️ Modificar Registro (Fila #${d.fila} del Excel)`;

    document.getElementById('f_nombre').value = d.nombre || '';
    document.getElementById('f_oficio').value = d.oficio || '';
    document.getElementById('f_siniestro').value = d.siniestro || '';
    document.getElementById('f_fsiniestro').value = d.fsiniestro || '';
    document.getElementById('f_fcmf').value = d.fcmf || '';
    document.getElementById('f_flimite').value = d.flimite || '';
    document.getElementById('f_ffid').value = d.ffid || '';
    document.getElementById('f_motivo').value = d.motivo || '';
    document.getElementById('f_estado').value = d.estado || '';

    let ramoNormalizado = (d.ramo || 'VM').toUpperCase().trim();
    if (ramoNormalizado === 'RR.VV' || ramoNormalizado === 'RRVV' || ramoNormalizado === 'RR.VV.') {
        ramoNormalizado = 'RV';
    }
    document.getElementById('f_ramo').value = ramoNormalizado;

    document.getElementById('f_respuesta').value = d.respuesta || '';
    document.getElementById('f_dda').value = d.dda || '';
    document.getElementById('f_zendesk').value = d.zendesk || '';
    document.getElementById('f_observaciones').value = d.observaciones || '';
    document.getElementById('f_legal').value = d.legal || '';

    sincronizarCheckDesdeTexto();
    recalcularFormulasModal();
    new bootstrap.Modal(document.getElementById('modalRegistro')).show();
}