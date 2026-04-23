const respuestaEnvioPrueba = document.getElementById('respuestaEnvioPruebas');
const admisionesPruebaEnviadas = document.getElementById('admisionesPruebaEnviadas');

let hoy = new Date()

/**
 * Inicializa (o re-inicializa) un DataTable de forma segura.
 * Evita el warning "Cannot reinitialise DataTable" cuando las consultas
 * Zeus se ejecutan más de una vez sobre la misma tabla: destruye la
 * instancia previa y limpia el DOM (necesario porque las columnas se
 * derivan dinámicamente de cada respuesta y pueden variar).
 */
function ensureDataTable(selector, options) {
    if ($.fn.DataTable.isDataTable(selector)) {
        $(selector).DataTable().clear().destroy();
        $(selector).empty();
    }
    return $(selector).DataTable(options);
}

const enviarAdmisionPrueba = async () => {
    let respuesta = "";
    let cantidad =  $('#cantidadAdmisiones').val();
    let fechaInicial =  $('#fechaInicialCargadas').val();
    ruta = "/grabarAdmisionPrueba/";

    data = {
        "cantidad":cantidad,
    }
    try{
        respuesta = await peticion_http(data, ruta, "GET");
        respuesta = respuesta.estado;
        
    }catch(error){
        respuesta = `error: ${error.status} - ${error.statusText} - ${error.responseText}`;
        
    }
    respuestaEnvioPrueba.innerHTML = respuesta;
    console.log(respuesta);
}

const consultarAdmisionesPrueba = async () => {
    let respuesta = "";
    let fechaInicial =  $('#fechaInicialCargadas').val();
    ruta = "/consultarAdmisionesPrueba/";

    data = {
        "fechaInicial":fechaInicial,
    }
    try{
        respuesta = await peticion_http(data, ruta, "GET");
        respuesta = respuesta.cantidad;
    }catch(error){
        respuesta = `error: ${error.status} - ${error.statusText} - ${error.responseText}`;
        
    }
    admisionesPruebaEnviadas.innerHTML = respuesta;
    console.log(respuesta);

}

const grabarAdmisiones = async () => {
    let respuesta = "";
   
    ruta = "/grabarAdmisiones/";

    data = {}
    try{
        respuesta = await peticion_http(data, ruta, "GET");
        console.log(respuesta);
    }catch(error){
        console.log(error);
        respuesta = `error: ${error.status} - ${error.statusText} - ${error.responseText}`;
        
    }
}

const codigos_empresa = async () => {
    let ruta = "/consultarCodigosEmpresa/";
    let data = {}
    let encabezados = [];    
    let respuesta =  await peticion_http(data, ruta, "GET");
    console.log(respuesta);
            
    for( campo of Object.keys(respuesta[0])){
        encabezados.push({data:campo});
    } 

    $('#tablaEmpresa').toggleClass("show");
    ensureDataTable('#tablaEmpresa', {
        data:respuesta,
        columns: encabezados
    }); 
}

const consultarPaciente = async () => {
    let ruta = "/consultarDatosPaciente/";
    let docPaciente = $('#documentoPaciente').val();
    let tipoDocumento = $('#tipoDocumento').val();

    data = {
        "id": docPaciente,
        "tipo": tipoDocumento
    }

    // ruta = `${ruta}?id=${docPaciente}&tipo=cc`; 
    let respuesta = await peticion_http(data, ruta);
    console.log(respuesta);

    let datosColaborador = respuesta["Datos"];

    if(datosColaborador.length == 0){
        $("#datosPaciente").empty();
        alert("Datos vacíos");
    
    }else{
        $("#datosPaciente").empty();
        for(campo of Object.keys(datosColaborador[0])){
            $("#datosPaciente").append(`<li>${campo}: ${datosColaborador[0][campo] }</li>`);
        }
    }

}

const consultarMedicos = async () => {
    let ruta = "/consultarMedicos/";
    let data = {};
    let encabezados = [];
    let respuesta =  await peticion_http(data, ruta);
    console.log(respuesta);
            
    for( campo of Object.keys(respuesta[0])){
        console.log(campo);
        encabezados.push({data:campo});
    } 
    

    ensureDataTable('#tablaMedicos', {
        data:respuesta,
        columns: encabezados
    }); 
}

const consultarUsuariosZeus = async () => {
    console.log("AQUÍ ENTRA");
    let ruta = "/consultarUsuariosZeus/";
    let data = {};
    let encabezados = [];
    let respuesta =  await peticion_http(data, ruta);
    console.log(respuesta);
            
    for( campo of Object.keys(respuesta[0])){
        console.log(campo);
        encabezados.push({data:campo});
    } 
    

    ensureDataTable('#tablaUsuarioZeus', {
        data:respuesta,
        columns: encabezados
    }); 
}

const listarTiposServicios = async () => {
    let ruta = "/listarTiposServicios/";
    let data = {};
    let encabezados = [];
    let respuesta =  await peticion_http(data, ruta);
    console.log(respuesta);
            
    for( campo of Object.keys(respuesta[0])){
        console.log(campo);
        encabezados.push({data:campo});
    } 

    ensureDataTable('#tablaTiposServicios', {
        data:respuesta,
        columns: encabezados
    }); 
}

const listarViaIngreso = async () => {
    let ruta = "/listarViasIngreso/";
    let datos = {};
    let encabezados = [];
    let respuesta =  await peticion_http(datos, ruta);
    let primeroObjeto = respuesta.Data[0]

    for( campo of Object.keys(primeroObjeto)){
        console.log(campo);
        encabezados.push({data:campo});
    } 
    console.log(encabezados);
    ensureDataTable('#tablaViaIngreso', {
        data:respuesta.Data,
        columns: encabezados
    }); 
}

const listarCausaExterna = async () => {
    let ruta = "/listarCasusasExternas/";
    let datos = {};
    let encabezados = [];
    let respuesta =  await peticion_http(datos, ruta);
    let primeroObjeto = respuesta.Data[0]

    for( campo of Object.keys(primeroObjeto)){
        console.log(campo);
        encabezados.push({data:campo});
    } 
    console.log(encabezados);
    ensureDataTable('#tablaCausaExterna', {
        data:respuesta.Data,
        columns: encabezados
    }); 
}

const listarUnidadesFuncionales = async () => {
    let ruta = "/listarUnidadesFuncionales/";
    let datos = {};
    let encabezados = [];
    let respuesta =  await peticion_http(datos, ruta, "GET");
    console.log(respuesta)
    let primeroObjeto = respuesta[0]

    for( campo of Object.keys(primeroObjeto)){
        console.log(campo);
        encabezados.push({data:campo});
    } 
    console.log(encabezados);
    ensureDataTable('#tablaUnidadFuncional', {
        data:respuesta,
        columns: encabezados
    }); 
}

const listarCodigosSedes = async () => {
    let ruta = "/listarSerialesSedes";
    let datos = {};
    let encabezados = [];
    let respuesta =  await peticion_http(datos, ruta, "GET");
    console.log(respuesta)
    let primeroObjeto = respuesta[0]

    for( campo of Object.keys(primeroObjeto)){
        console.log(campo);
        encabezados.push({data:campo});
    } 
    console.log(encabezados);
    ensureDataTable('#tablaCodigosSedes', {
        data:respuesta,
        columns: encabezados
    }); 
}

const listarPuntosAtencion = async () => {
    let ruta = "/listarPuntosAtencion/";
    let datos = {};
    let encabezados = [];
    let respuesta =  await peticion_http(datos, ruta);
    console.log(respuesta)
    let primeroObjeto = respuesta[0]

    for( campo of Object.keys(primeroObjeto)){
        console.log(campo);
        encabezados.push({data:campo});
    } 
    console.log(encabezados);
    ensureDataTable('#tablaPuntosAtencion', {
        data:respuesta,
        columns: encabezados
    }); 
}

const listarTiposDiagnosticos = async () => {
    let ruta = "/listarTiposDiagnosticos/";
    let datos = {};
    let encabezados = [];
    let respuesta =  await peticion_http(datos, ruta);
    console.log(respuesta)
    let primeroObjeto = respuesta.Data[0]

    for( campo of Object.keys(primeroObjeto)){
        console.log(campo);
        encabezados.push({data:campo});
    } 
    console.log(encabezados);
    ensureDataTable('#tablaTiposDiagnosticos', {
        data:respuesta.Data,
        columns: encabezados
    }); 
}

const listarFinalidades = async () => {
    let ruta = "/listarFinalidades/";
    let datos = {};
    let encabezados = [];
    let respuesta =  await peticion_http(datos, ruta);
    console.log(respuesta)
    let primeroObjeto = respuesta.Data[0]

    for( campo of Object.keys(primeroObjeto)){
        console.log(campo);
        encabezados.push({data:campo});
    } 
    console.log(encabezados);
    ensureDataTable('#tablaFinalidades', {
        data:respuesta.Data,
        columns: encabezados
    }); 
}

const listarCentrosCosto = async () => {
    let ruta = "/listarCentrosCostos/";
    let datos = {};
    let encabezados = [];
    let respuesta =  await peticion_http(datos, ruta);
    console.log(respuesta)
    let primeroObjeto = respuesta[0]

    for( campo of Object.keys(primeroObjeto)){
        console.log(campo);
        encabezados.push({data:campo});
    } 
    console.log(encabezados);
    ensureDataTable('#tablaCentrosCostos', {
        data:respuesta,
        columns: encabezados
    }); 
}

const listarEstratos = async () => {
    let ruta = "/listarEstratos/";
    let datos = {};
    let encabezados = [];
    let respuesta =  await peticion_http(datos, ruta);
    console.log(respuesta)
    let primeroObjeto = respuesta[0]

    for( campo of Object.keys(primeroObjeto)){
        console.log(campo);
        encabezados.push({data:campo});
    } 
    console.log(encabezados);
    ensureDataTable('#tablaEstratos', {
        data:respuesta,
        columns: encabezados
    }); 
}

const listarContratos = async () => {
    let ruta = "/listarContratos/";
    let datos = {};
    let encabezados = [];
    let respuesta =  await peticion_http(datos, ruta);
    console.log(respuesta)
    let primeroObjeto = respuesta[0]

    for( campo of Object.keys(primeroObjeto)){
        console.log(campo);
        encabezados.push({data:campo});
    } 
    console.log(encabezados);
    ensureDataTable('#tablaContratos', {
        data:respuesta,
        columns: encabezados
    }); 
}




