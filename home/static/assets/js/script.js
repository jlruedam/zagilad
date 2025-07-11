const respuestaEnvioPrueba = document.getElementById('respuestaEnvioPruebas');
const admisionesPruebaEnviadas = document.getElementById('admisionesPruebaEnviadas');

let hoy = new Date()

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
    $('#tablaEmpresa').DataTable({
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
    

    $('#tablaMedicos').DataTable({
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
    

    $('#tablaUsuarioZeus').DataTable({
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

    $('#tablaTiposServicios').DataTable({
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
    $('#tablaViaIngreso').DataTable({
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
    $('#tablaCausaExterna').DataTable({
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
    $('#tablaUnidadFuncional').DataTable({
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
    $('#tablaCodigosSedes').DataTable({
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
    $('#tablaPuntosAtencion').DataTable({
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
    $('#tablaTiposDiagnosticos').DataTable({
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
    $('#tablaFinalidades').DataTable({
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
    $('#tablaCentrosCostos').DataTable({
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
    $('#tablaEstratos').DataTable({
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
    $('#tablaContratos').DataTable({
        data:respuesta,
        columns: encabezados
    }); 
}




