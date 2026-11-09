// core/static/core/js/legal/legal_agenda.js

let audienciasGlobales = [];
let fechaActualCalendario = new Date(); // Inicia en el mes y año actual

const NOMBRES_MESES = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
];

document.addEventListener('DOMContentLoaded', () => {
    const audEl = document.getElementById('audiencias-json-data');
    if (audEl) {
        try {
            audienciasGlobales = JSON.parse(audEl.textContent);
        } catch (e) {
            audienciasGlobales = [];
        }
    }
    renderizarCalendarioAgenda();
});

function _escaparAtributo(texto) {
    return String(texto || '')
        .replace(/&/g, '&amp;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
}

function cambiarMesCalendario(delta) {
    fechaActualCalendario.setDate(1);
    fechaActualCalendario.setMonth(fechaActualCalendario.getMonth() + delta);
    renderizarCalendarioAgenda();
}

function renderizarCalendarioAgenda() {
    const grilla = document.getElementById('grillaCalendarioMensual');
    const label = document.getElementById('labelMesAnioCalendario');
    if (!grilla || !label) return;

    const anio = fechaActualCalendario.getFullYear();
    const mes = fechaActualCalendario.getMonth();

    label.textContent = `${NOMBRES_MESES[mes]} ${anio}`;

    // Fecha actual real para marcar el día de hoy en rojo
    const hoy = new Date();
    const hoyStr = `${hoy.getFullYear()}-${String(hoy.getMonth() + 1).padStart(2, '0')}-${String(hoy.getDate()).padStart(2, '0')}`;

    const primerDia = new Date(anio, mes, 1);
    let diaSemanaInicio = primerDia.getDay() - 1; // Lunes = 0
    if (diaSemanaInicio === -1) diaSemanaInicio = 6; // Domingo = 6

    const ultimoDiaMes = new Date(anio, mes + 1, 0).getDate();
    const ultimoDiaMesAnterior = new Date(anio, mes, 0).getDate();

    let html = '';
    let diaContador = 1;
    let diasSiguienteMes = 1;

    for (let i = 0; i < 42; i++) {
        let esMesActual = false;
        let numDia = '';
        let fechaStr = '';

        if (i < diaSemanaInicio) {
            numDia = ultimoDiaMesAnterior - (diaSemanaInicio - 1 - i);
        } else if (diaContador <= ultimoDiaMes) {
            esMesActual = true;
            numDia = diaContador;
            const mFmt = String(mes + 1).padStart(2, '0');
            const dFmt = String(diaContador).padStart(2, '0');
            fechaStr = `${anio}-${mFmt}-${dFmt}`;
            diaContador++;
        } else {
            numDia = diasSiguienteMes;
            diasSiguienteMes++;
        }

        const esHoy = esMesActual && (fechaStr === hoyStr);
        const claseCelda = [
            'celda-dia-calendario',
            !esMesActual ? 'fuera-de-mes' : '',
            esHoy ? 'dia-actual-rojo' : ''
        ].join(' ').trim();

        const audsDelDia = esMesActual
            ? audienciasGlobales.filter(a => a.fecha_audiencia_iso === fechaStr)
            : [];

        const pildorasHtml = audsDelDia.map(a => {
            const numCausa = a.id_causa || a.siniestro || a.ruc || 'S/N';
            const detalleHover = `Estudio: ${a.estudio || '-'}\nRUC: ${a.ruc || '-'} | RIT: ${a.rit || '-'}\nMotivo: ${a.motivo_audiencia || '-'}`;
            return `
                <div class="evento-causa-pill mb-1"
                     data-bs-toggle="popover"
                     data-bs-trigger="hover focus"
                     data-bs-placement="top"
                     data-bs-title="Causa ${_escaparAtributo(numCausa)}"
                     data-bs-content="${_escaparAtributo(detalleHover)}"
                     onclick="abrirOverviewCausaAgenda('${_escaparAtributo(numCausa)}', '${fechaStr}')">
                    ${_escaparAtributo(numCausa)}
                </div>
            `;
        }).join('');

        html += `
            <div class="${claseCelda}">
                <div class="d-flex justify-content-end mb-1">
                    <span class="fw-bold small numero-dia-cal ${esMesActual ? 'text-dark' : 'text-muted'}">${numDia}</span>
                </div>
                <div class="flex-grow-1 overflow-y-auto" style="max-height: 62px;">
                    ${pildorasHtml}
                </div>
            </div>
        `;
    }

    grilla.innerHTML = html;

    // Inicializar popovers de Bootstrap para el hover de cada causa
    grilla.querySelectorAll('[data-bs-toggle="popover"]').forEach(el => {
        new bootstrap.Popover(el);
    });
}

function abrirOverviewCausaAgenda(identificador, fechaIso) {
    // 1. Buscar la audiencia específica
    const aud = audienciasGlobales.find(a =>
        (a.id_causa === identificador || a.siniestro === identificador || a.ruc === identificador) &&
        (!fechaIso || a.fecha_audiencia_iso === fechaIso)
    ) || audienciasGlobales.find(a =>
        a.id_causa === identificador || a.siniestro === identificador
    ) || {};

    // 2. Buscar los datos completos de la causa en el consolidado principal
    const causa = (typeof datosLegalesAnalytics !== 'undefined' ? datosLegalesAnalytics : []).find(c =>
        c.id_causa === identificador ||
        c.siniestro === identificador ||
        (aud.id_causa && c.id_causa === aud.id_causa) ||
        (aud.siniestro && c.siniestro === String(aud.siniestro))
    );

    document.getElementById('ov_titulo_modal').textContent = `⚖️ Resumen de Causa · ${identificador}`;
    document.getElementById('ov_fecha_audiencia').textContent = aud.fecha_audiencia || fechaIso || '-';
    document.getElementById('ov_motivo_audiencia').textContent = aud.motivo_audiencia || 'Sin descripción de audiencia';

    if (causa) {
        document.getElementById('ov_id_siniestro').textContent = `${causa.id_causa} (Siniestro: ${causa.siniestro || '-'})`;
        document.getElementById('ov_competencia_estado').textContent = `${causa.competencia} · ${causa.estado}`;
        document.getElementById('ov_provision').textContent = causa.provision_fmt || '-';
        document.getElementById('ov_rotulado').textContent = causa.rotulado || '-';
        document.getElementById('ov_asegurado').textContent = causa.asegurado || '-';
        document.getElementById('ov_estudio').textContent = causa.estudio || aud.estudio || '-';
        document.getElementById('ov_tribunal_roles').textContent = `${causa.tribunal || '-'} (RIT: ${causa.rit || '-'} / RUC: ${causa.ruc || '-'})`;
        document.getElementById('ov_motivo_delito').textContent = causa.motivo_delito || '-';
        document.getElementById('ov_etapa_sentencia').textContent = `${causa.etapa_procesal || '-'} / Sentencia: ${causa.sentencia || '-'}`;
        document.getElementById('ov_observacion').textContent = causa.ultimo_reporte_estudio || causa.observacion || 'Sin observaciones registradas.';
    } else {
        document.getElementById('ov_id_siniestro').textContent = `${aud.id_causa || '-'} (Siniestro: ${aud.siniestro || '-'})`;
        document.getElementById('ov_competencia_estado').textContent = 'No vinculada en tabla principal';
        document.getElementById('ov_provision').textContent = '-';
        document.getElementById('ov_rotulado').textContent = '-';
        document.getElementById('ov_asegurado').textContent = '-';
        document.getElementById('ov_estudio').textContent = aud.estudio || '-';
        document.getElementById('ov_tribunal_roles').textContent = `RIT: ${aud.rit || '-'} / RUC: ${aud.ruc || '-'}`;
        document.getElementById('ov_motivo_delito').textContent = '-';
        document.getElementById('ov_etapa_sentencia').textContent = '-';
        document.getElementById('ov_observacion').textContent = aud.motivo_audiencia || '-';
    }

    new bootstrap.Modal(document.getElementById('modalOverviewCausaAgenda')).show();
}