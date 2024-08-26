let hoy = new Date()

const enviarAdminsionPrueba = async () => {
    let respuesta = "";
    let cantidad =  $('#cantidadAdmisiones').val();
    ruta = "/grabarAdmisionPrueba/";

    data = {
        "cantidad":cantidad,
    }
    try{
        respuesta = await peticion_http(data, ruta, "GET");
        // respuesta = respuesta.Datos[0].infoTrasaction;
        console.log(respuesta);
    }catch(error){
        console.log(error);
        respuesta = `error: ${error.status} - ${error.statusText} - ${error.responseText}`;
        
    }
    // $('#respuestaAdmision').toggleClass("no_show");
    // $('#respuestaAdmision').html(String(respuesta.resultados.DatosGuardados + "/" + respuesta.resultados.DatosEnError));
    $('#admisionesEnviadas').html(respuesta.resultados.length);
}

const grabarAdmisiones = async () => {
    let respuesta = "";
   
    ruta = "/grabarAdmisiones/";

    data = {}
    try{
        respuesta = await peticion_http(data, ruta, "GET");
        // respuesta = respuesta.Datos[0].infoTrasaction;
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

    data = {
        "id": docPaciente,
        "tipo": "cc"
    }

    // ruta = `${ruta}?id=${docPaciente}&tipo=cc`; 
    let respuesta =  await peticion_http(data, ruta);
    console.log(respuesta);

    let datosColaborador = respuesta["Datos"];

    $("#datosPaciente").empty();
    for(campo of Object.keys(datosColaborador[0])){
        $("#datosPaciente").append(`<li>${campo}: ${datosColaborador[0][campo] }</li>`);
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


