$(document).ready(async function () {

    // ── DataTable de actividades ──────────────────────────────────────────────
    $('#tablaActividadesInconsistencias').DataTable({
        ajax: {
            url: "/listarActividadesInconsistencias/",
            dataSrc: 'data',
            type: 'POST',
            headers: { 'X-CSRFToken': csrftoken },
        },
        columns: [
            { data: 'id' },
            { data: 'regional' },
            { data: 'fecha_servicio' },
            { data: 'nombre_actividad' },
            { data: 'diagnostico_p' },
            { data: 'tipo_documento' },
            { data: 'documento_paciente' },
            { data: 'nombre_paciente' },
            {
                data: 'carga',
                render: function (data) {
                    return '<a href="/verCarga/' + data + '/1">' + data + '</a>';
                }
            },
            { data: 'admision__numero_estudio' },
            { data: 'inconsistencias' },
            { data: 'medico__documento' },
            {
                data: 'id',
                className: 'col-acciones',
                render: function (data) {
                    return '<a class="btn-accion btn-accion--ver" href="/verActividad/' + data + '/" title="Ver detalle" aria-label="Ver detalle">🔍</a>';
                }
            },
        ],
        ordering: false,
        processing: true,
        serverSide: true,
    });

    // ── Estadísticas ──────────────────────────────────────────────────────────
    cargarStats();
});

async function cargarStats() {
    try {
        const resp = await fetch("/statsActividadesInconsistencias/", {
            headers: { "Accept": "application/json" }
        });
        if (!resp.ok) return;
        const datos = await resp.json();
        renderStats("statsPorTipo",      datos.por_tipo,      "inconsistencias", true);
        renderStats("statsPorActividad", datos.por_actividad, "nombre_actividad", false);
    } catch (e) {
        document.getElementById("statsPorTipo").textContent = "No se pudieron cargar las estadísticas.";
        document.getElementById("statsPorActividad").textContent = "";
    }
}

function renderStats(contenedorId, datos, campoLabel, truncarLabel) {
    const contenedor = document.getElementById(contenedorId);
    if (!datos || datos.length === 0) {
        contenedor.innerHTML = '<span style="color:#bbb;font-size:13px">Sin datos</span>';
        return;
    }
    const maxVal = datos[0].cantidad;
    contenedor.innerHTML = datos.map(item => {
        const pct = maxVal > 0 ? Math.round(item.cantidad / maxVal * 100) : 0;
        let label = item[campoLabel] || "—";
        // Quitar prefijo de emoji/código para las inconsistencias
        if (truncarLabel && label.length > 60) {
            label = label.substring(0, 57) + "…";
        }
        return `
        <div class="stats-fila" title="${item[campoLabel] || ''}">
            <span class="stats-fila__label">${label}</span>
            <div class="stats-fila__barra-wrap">
                <div class="stats-fila__barra" style="width:${pct}%"></div>
            </div>
            <span class="stats-fila__cant">${item.cantidad}</span>
        </div>`;
    }).join('');
}
