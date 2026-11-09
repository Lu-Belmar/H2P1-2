// core/static/core/js/legal/legal_estudios_bitacora.js

function abrirDetalleEstudio(nombreEstudio) {
    const info = estudiosStatsData.find(e => e.nombre === nombreEstudio);
    if (!info) return;

    document.getElementById('tituloModalEstudio').textContent = `🏛️ ${info.nombre}`;
    document.getElementById('detEstTotal').textContent = `${info.total} (${info.civil} Civ / ${info.penal} Pen)`;
    document.getElementById('detEstWinrate').textContent = `${info.winrate}% (${info.ganadas}W - ${info.perdidas}L)`;
    document.getElementById('detEstClp').textContent = info.provision_clp_fmt;
    document.getElementById('detEstUf').textContent = info.provision_uf_fmt;
    document.getElementById('detEstDias').textContent = `${info.promedio_dias} días`;

    const tbody = document.getElementById('tbodyDetalleEstudio');
    tbody.innerHTML = info.causas.map(c => `
        <tr>
            <td class="fw-bold">${c.id_causa}</td>
            <td>${c.siniestro}</td>
            <td><span class="badge ${c.bloque_legal === 'PENAL' ? 'bg-dark' : 'bg-info text-dark'}">${c.competencia}</span></td>
            <td>${c.rotulado || '-'}</td>
            <td>${c.tribunal || '-'}</td>
            <td>${c.estado}</td>
            <td>
                ${c.sentencia !== '-' ? `<span class="badge ${c.resultado_win === 'A_FAVOR' ? 'bg-success' : 'bg-danger'}">${c.sentencia}</span>` : '-'}
            </td>
            <td class="text-end fw-bold">${c.provision_fmt}</td>
            <td class="text-center">${c.dias_gestion !== null ? c.dias_gestion : '-'}</td>
            <td class="text-center">${c.hallazgo === 'SI' ? '🔍 Sí' : '-'}</td>
        </tr>
    `).join('');

    new bootstrap.Modal(document.getElementById('modalDetalleEstudio')).show();
}

function filtrarTablaReportesEstudios() {
    const input = document.getElementById('buscadorReportesEstudios');
    if (!input) return;
    const q = input.value.toLowerCase().trim();
    document.querySelectorAll('#tablaReportesEstudios tbody tr').forEach(tr => {
        tr.style.display = (!q || tr.textContent.toLowerCase().includes(q)) ? '' : 'none';
    });
}

function mostrarPanelMesesIndicadores() {
    const campos = ['rep_anteriores', 'oct_2026', 'dic_2026', 'feb_2027', 'abr_2027', 'jun_2027', 'ago_2027', 'oct_2027', 'dic_2027'];
    campos.forEach(key => actualizarIndicadorObs(key));
}

function actualizarIndicadorObs(key) {
    const ta = document.querySelector(`[name="${key}"]`);
    const badge = document.querySelector(`.indicador-obs[data-key="${key}"]`);
    if (ta && badge) {
        if (ta.value.trim().length > 0) {
            badge.textContent = 'Escrito';
            badge.className = 'badge bg-success float-end indicador-obs';
        } else {
            badge.textContent = 'Vacío';
            badge.className = 'badge bg-secondary float-end indicador-obs';
        }
    }
}

function mostrarPanelMes(keyPanel, btnElement) {
    document.querySelectorAll('.panel-editor-mes').forEach(el => {
        el.style.display = 'none';
    });

    const panelActivo = document.querySelector(`.panel-editor-mes[data-panel="${keyPanel}"]`);
    if (panelActivo) {
        panelActivo.style.display = 'flex';
    }

    const titulo = document.getElementById('tituloPanelActivo');
    if (titulo && btnElement) {
        titulo.textContent = btnElement.textContent.replace('Escrito', '').replace('Vacío', '').trim();
    }

    document.querySelectorAll('#listaIndiceMeses button').forEach(b => b.classList.remove('active'));
    if (btnElement) btnElement.classList.add('active');
}

function abrirSelectorNuevoMes() {
    const panel = document.getElementById('panelNuevoMes');
    if (panel) panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
}

function activarPanelMesSeleccionado() {
    const select = document.getElementById('selectNuevoMes');
    if (!select) return;
    const keySeleccionada = select.value;

    let btnEncontrado = null;
    document.querySelectorAll('#listaIndiceMeses button').forEach(b => {
        if ((b.getAttribute('onclick') || '').includes(keySeleccionada)) {
            btnEncontrado = b;
        }
    });

    if (btnEncontrado) {
        mostrarPanelMes(keySeleccionada, btnEncontrado);
        document.getElementById('panelNuevoMes').style.display = 'none';
        const ta = document.querySelector(`[name="${keySeleccionada}"]`);
        if (ta) ta.focus();
    }
}

function abrirModalReporteBimestral(btn) {
    const d = btn.dataset;
    document.getElementById('rep_fila_input').value = d.filarep || '';
    document.getElementById('tituloModalReporteBimestral').textContent =
        `📝 Reportes Bimestrales · Causa ${d.id || ''} (${d.estudio || 'Sin estudio'})`;

    const mapaValores = {
        'rep_anteriores': d.anteriores || '',
        'oct_2026': d.oct2026 || '',
        'dic_2026': d.dic2026 || '',
        'feb_2027': d.feb2027 || '',
        'abr_2027': d.abr2027 || '',
        'jun_2027': d.jun2027 || '',
        'ago_2027': d.ago2027 || '',
        'oct_2027': d.oct2027 || '',
        'dic_2027': d.dic2027 || ''
    };

    Object.entries(mapaValores).forEach(([k, val]) => {
        const el = document.querySelector(`[name="${k}"]`);
        if (el) el.value = val;
    });

    mostrarPanelMesesIndicadores();

    const primerConTexto = Object.keys(mapaValores).find(k => mapaValores[k].trim().length > 0) || 'rep_anteriores';
    let btnInicial = document.querySelector('#listaIndiceMeses button');
    document.querySelectorAll('#listaIndiceMeses button').forEach(b => {
        if ((b.getAttribute('onclick') || '').includes(primerConTexto)) {
            btnInicial = b;
        }
    });
    mostrarPanelMes(primerConTexto, btnInicial);

    new bootstrap.Modal(document.getElementById('modalReporteBimestral')).show();
}