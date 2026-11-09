// core/static/core/js/legal/legal_modales_crud.js

function textoTieneHallazgo(texto) {
    return (texto || '').toLowerCase().includes('hallazgo');
}

function toggleHallazgoInput() {
    const check = document.getElementById('leg_check_hallazgo');
    const obs = document.getElementById('leg_observacion');
    let valor = obs.value.trim();

    if (check.checked) {
        if (!textoTieneHallazgo(valor)) {
            obs.value = valor ? `${valor} / Hallazgo` : 'Hallazgo';
        }
    } else {
        obs.value = valor
            .replace(/\s*\/\s*hallazgos?/gi, '')
            .replace(/hallazgos?\s*\/\s*/gi, '')
            .replace(/^hallazgos?$/gi, '')
            .trim();
    }
}

function sincronizarCheckHallazgo() {
    const valor = document.getElementById('leg_observacion').value;
    document.getElementById('leg_check_hallazgo').checked = textoTieneHallazgo(valor);
}

function abrirModalCausaCrear() {
    document.getElementById('formCausaLegal').reset();
    document.getElementById('inputAccionLegal').value = 'crear_causa_legal';
    document.getElementById('inputFilaLegal').value = '';
    document.getElementById('tituloModalCausaLegal').textContent = '➕ Crear Nueva Causa Legal';
    document.getElementById('leg_check_hallazgo').checked = false;
    new bootstrap.Modal(document.getElementById('modalCausaLegal')).show();
}

function abrirModalCausaEditar(btn) {
    const d = btn.dataset;
    document.getElementById('inputAccionLegal').value = 'editar_causa_legal';
    document.getElementById('inputFilaLegal').value = d.fila;
    document.getElementById('tituloModalCausaLegal').textContent = `✏️ Editar Causa ${d.id} (Fila #${d.fila})`;

    document.getElementById('leg_siniestro').value = d.siniestro || '';
    document.getElementById('leg_competencia').value = d.competencia || 'Civil';
    document.getElementById('leg_estudio').value = d.estudio || '';
    document.getElementById('leg_rotulado').value = d.rotulado || '';
    document.getElementById('leg_asegurado').value = d.asegurado || '';
    document.getElementById('leg_fcreacion').value = d.fcreacion || '';
    document.getElementById('leg_fpjud').value = d.fpjud || '';
    document.getElementById('leg_fasig').value = d.fasig || '';
    document.getElementById('leg_ftermino').value = d.ftermino || '';
    document.getElementById('leg_moneda').value = d.moneda || '';
    document.getElementById('leg_provision').value = d.provision || 0;
    document.getElementById('leg_calificacion').value = d.calificacion || '';
    document.getElementById('leg_motivo').value = d.motivo || '';
    document.getElementById('leg_parte').value = d.parte || '';
    document.getElementById('leg_estado').value = d.estado || 'En Proceso';

    const selectSentencia = document.getElementById('leg_sentencia');
    const valSent = (d.sentencia === '-' || !d.sentencia) ? '' : d.sentencia.trim();
    if (valSent && !Array.from(selectSentencia.options).some(opt => opt.value === valSent)) {
        selectSentencia.add(new Option(valSent, valSent));
    }
    selectSentencia.value = valSent;

    document.getElementById('leg_etapa').value = d.etapa || '';
    document.getElementById('leg_tribunal').value = d.tribunal || '';
    document.getElementById('leg_rit').value = d.rit || '';
    document.getElementById('leg_ruc').value = d.ruc || '';
    document.getElementById('leg_analista').value = d.analista || '';
    document.getElementById('leg_observacion').value = d.observacion || '';

    sincronizarCheckHallazgo();
    new bootstrap.Modal(document.getElementById('modalCausaLegal')).show();
}