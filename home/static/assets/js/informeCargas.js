const URL_RESUMEN_CARGAS = "/listarResumenCargas/";
const INTERVALO_ACTIVO   = 5000;   // 5 s — cuando hay cargas procesando o admisionando
const INTERVALO_INACTIVO = 30000;  // 30 s — cuando todas están en estado terminal

let pollingTimeout = null;

// ── Helpers de progreso ────────────────────────────────────────────────────────

function htmlBarraProgreso(pct, clase) {
    return `
        <div class="barra-progreso">
            <div class="barra-relleno ${clase}" style="width:${pct}%"></div>
        </div>
        <small class="texto-progreso">${pct}%</small>`;
}

function htmlProgresoCarga(carga) {
    if (carga.estado === "procesando") {
        const pct = carga.porcentaje_procesamiento ?? 0;
        const label = pct === 0 ? "Iniciando..." : `${pct}% procesado`;
        return `
            <div class="barra-progreso">
                <div class="barra-relleno barra-procesando" style="width:${pct}%"></div>
            </div>
            <small class="texto-progreso">${label}</small>`;
    }
    if (carga.estado === "admisionando") {
        const pct = carga.porcentaje_admisionado ?? 0;
        const label = pct === 0 ? "Iniciando..." : `${pct}% admisionado`;
        return `
            <div class="barra-progreso">
                <div class="barra-relleno barra-admisionando" style="width:${pct}%"></div>
            </div>
            <small class="texto-progreso">${label}</small>`;
    }
    return "—";
}

// ── Actualización de la tabla ──────────────────────────────────────────────────

function textoGestionCarga(carga) {
    if (carga.estado === "procesada") {
        return `<span class="iconosGestion"><a href="${carga.ver_url}">&#128065;&#65039;</a></span>`;
    }
    if (carga.estado === "cancelada") {
        return '<span class="iconosGestion">&#10060;</span>';
    }
    return '<span class="iconosGestion">&#128368;&#65039;</span>';
}

function actualizarCeldaCarga(fila, campo, valor) {
    const celda = fila.querySelector(`[data-carga-campo="${campo}"]`);
    if (celda) {
        celda.textContent = valor;
    }
}

function actualizarResumenCargas(cargas) {
    cargas.forEach((carga) => {
        const fila = document.querySelector(`[data-carga-id="${carga.id}"]`);
        if (!fila) return;

        actualizarCeldaCarga(fila, "usuario",                         carga.usuario);
        actualizarCeldaCarga(fila, "estado",                          carga.estado);
        actualizarCeldaCarga(fila, "cantidad_actividades",            carga.cantidad_actividades);
        actualizarCeldaCarga(fila, "cantidad_actividades_inconsistencias", carga.cantidad_actividades_inconsistencias);
        actualizarCeldaCarga(fila, "cantidad_actividades_ok",         carga.cantidad_actividades_ok);
        actualizarCeldaCarga(fila, "cantidad_actividades_admisionadas", carga.cantidad_actividades_admisionadas);
        actualizarCeldaCarga(fila, "tiempo_procesamiento",            carga.tiempo_procesamiento);
        actualizarCeldaCarga(fila, "updated_at",                      carga.updated_at);

        // Barra de progreso — usa innerHTML para actualizar el SVG/div interno
        const celdaProgreso = fila.querySelector('[data-carga-campo="progreso"]');
        if (celdaProgreso) {
            celdaProgreso.innerHTML = htmlProgresoCarga(carga);
        }

        const gestion = fila.querySelector('[data-carga-campo="gestion"]');
        if (gestion) {
            gestion.innerHTML = textoGestionCarga(carga);
        }
    });
}

// ── Polling con frecuencia adaptativa ─────────────────────────────────────────

function hayEstadoActivo(cargas) {
    return cargas.some(c => c.estado === "procesando" || c.estado === "admisionando");
}

async function cargarResumenCargas() {
    try {
        const respuesta = await fetch(URL_RESUMEN_CARGAS, {
            headers: { "Accept": "application/json" },
        });
        if (!respuesta.ok) return;

        const datos = await respuesta.json();
        const cargas = datos.cargas || [];
        actualizarResumenCargas(cargas);

        // Intervalo corto si hay procesos activos; largo si todo está en estado terminal
        const intervalo = hayEstadoActivo(cargas) ? INTERVALO_ACTIVO : INTERVALO_INACTIVO;
        pollingTimeout = setTimeout(cargarResumenCargas, intervalo);
    } catch (error) {
        console.error("No se pudo actualizar el resumen de cargas", error);
        pollingTimeout = setTimeout(cargarResumenCargas, INTERVALO_INACTIVO);
    }
}

document.addEventListener("DOMContentLoaded", () => {
    cargarResumenCargas();
});
