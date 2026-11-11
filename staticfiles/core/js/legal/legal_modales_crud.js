// core/static/core/js/legal/legal_modales_crud.js


function abrirModalCausaCrear() {
    document.getElementById('formCausaLegal').reset();
    document.getElementById('inputAccionLegal').value = 'crear_causa_legal';
    document.getElementById('inputFilaLegal').value = '';
    document.getElementById('tituloModalCausaLegal').textContent = '➕ Crear Nueva Causa Legal';
    document.getElementById('leg_check_hallazgo').checked = false;
    new bootstrap.Modal(document.getElementById('modalCausaLegal')).show();
}

// core/static/core/js/legal/legal_modales_crud.js
function abrirModalCausaEditar(btn) {
    const d = btn.dataset;
    document.getElementById('inputAccionLegal').value = 'editar_causa_legal';
    document.getElementById('inputFilaLegal').value = d.fila || '';
    document.getElementById('tituloModalCausaLegal').textContent = `✏️ Editar Causa ${d.id || ''} (Fila #${d.fila || ''})`;

    const asignarValor = (id, val) => {
        const el = document.getElementById(id);
        if (el) el.value = val || '';
    };

    asignarValor('leg_siniestro', d.siniestro);
    asignarValor('leg_competencia', d.competencia || 'Civil');
    asignarValor('leg_estudio', d.estudio);
    asignarValor('leg_rotulado', d.rotulado);
    asignarValor('leg_asegurado', d.asegurado);
    asignarValor('leg_fcreacion', d.fcreacion);
    asignarValor('leg_fpjud', d.fpjud);
    asignarValor('leg_fasig', d.fasig);
    asignarValor('leg_ftermino', d.ftermino);
    asignarValor('leg_moneda', d.moneda);
    asignarValor('leg_provision', d.provision || 0);
    asignarValor('leg_calificacion', d.calificacion);
    asignarValor('leg_motivo', d.motivo);
    asignarValor('leg_parte', d.parte);
    asignarValor('leg_estado', d.estado || 'En Proceso');

    const selectSentencia = document.getElementById('leg_sentencia');
    if (selectSentencia) {
        const valSent = (d.sentencia === '-' || !d.sentencia) ? '' : d.sentencia.trim();
        if (valSent && !Array.from(selectSentencia.options).some(opt => opt.value === valSent)) {
            selectSentencia.add(new Option(valSent, valSent));
        }
        selectSentencia.value = valSent;
    }

    asignarValor('leg_etapa', d.etapa);
    asignarValor('leg_tribunal', d.tribunal);
    asignarValor('leg_rit', d.rit);
    asignarValor('leg_ruc', d.ruc);
    asignarValor('leg_analista', d.analista);
    asignarValor('leg_observacion', d.observacion);

    if (typeof sincronizarCheckHallazgo === 'function') {
        sincronizarCheckHallazgo();
    }

    const modalEl = document.getElementById('modalCausaLegal');
    if (modalEl) {
        new bootstrap.Modal(modalEl).show();
    }
}