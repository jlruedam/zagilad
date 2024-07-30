// let base64 = require('base-64');
var TOKEN = "";
const URL_BASE = "http://10.244.21.17:8022";
const corsAnywhere = 'https://cors-anywhere.herokuapp.com/';
const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value; // Se utiliza para poder enviar petición tipo POST a Django

let hoy = new Date()

let username = "administrador";
let password = "123456";
// let admision_prueba = [
//     {
//         "autoid": 34678, 
//         "Cod_entidad": "EPS048",
//         "tipo_estudio": "A",
//         "nro_autoriza": "",
//         "Cod_clasi": "01",
//         "Fecha_ing": "2024-07-17",
//         "Hora_ing": "08:00",
//         "Cod_medico": 1,
//         "Nro_factura": 123456,
//         "Estado": "A",
//         "Obs": "",
//         "Cod_usuario": "1047394846",
//         "Nom_usuario": "LUIS FERNANDO RODRIGUEZ",
//         "Contrato": 134,
//         "Status_regis": 0,
//         "Estado_res": 0,
//         "Usuario_estado_res": "1047394846",
//         "Codigo_servicio": 1,
//         "Via_ingreso": 2,
//         "Causa_ext": "13",
//         "Terapia": 2,
//         "Nit_asegura": "0",
//         "Rs_asegura": "0",
//         "Consec_soat": "",
//         "No_poliza": 0,
//         "Ufuncional": 1,
//         "Embarazo": "",
//         "Id_sede": 1,
//         "PuntoAtencion": 1,
//         "PolizaSalud": "",
//         "serviciosObjDTOS": [
//             {
//                 "autoid": 202665,
//                 "fuente_tips": 1,
//                 "num_servicio": 1,
//                 "cod_servicio": "911016",
//                 "fecha_servicio": "2024-07-17",
//                 "descripcion": "ECOGRAFIA DOPPLER DE VASOS ARTERIALES DE MIEMBROS SUPERIORES A COLOR",
//                 "cantidad": 2,
//                 "vlr_servicio": 2000,
//                 "total": 4000,
//                 "personal_ate": "1",
//                 "cod_medico": "1",
//                 "tipo_diag": 0,
//                 "cod_diap": "",
//                 "cod_diagn1": "",
//                 "cod_diagn2": "",
//                 "cod_diagn3": "",
//                 "finalidad": 1,
//                 "ambito_proc": 1,
//                 "ccosto": "19",
//                 "tipo_estudio": "A",
//                 "ufuncional": 1,
//                 "usuario": 1,
//                 "tipoItem": "Procedimiento"
//             }
//         ]
//     }
// ]
// let admision_prueba = [{
//         "autoid": 34678, //PARÁMETRO
//         "Cod_entidad": "0099",//PARÁMETRO
//         "tipo_estudio": "A",//QUEDMADO
//         "nro_autoriza": "",//QUEDMADO
//         "Cod_clasi": "01",//QUEDMADO
//         "Fecha_ing":formatDate(hoy),//CALCULADO
//         "Hora_ing": "08:00",//QUEDMADO
//         "Cod_medico": 1,//PARAMETRO
//         "Nro_factura": 33333,//CALCULADO
//         "Estado": "A",//QUEDMADO
//         "Obs": "Admisión de prueba JLRM",//VARIABLE
//         "Cod_usuario": "1047394846",//PARÁMETRO
//         "Nom_usuario": "LUIS FERNANDO RODRIGUEZ",//PARÁMETRO
//         "Contrato": 135,//endpoint no funciona //PARÁMETRO
//         "Status_regis": 0,//QUEDMADO
//         // "Estado_res": 0,
//         "Usuario_estado_res": "1047394846",//PARÁMETRO
//         "Codigo_servicio": 5,//VARIABLE
//         "Via_ingreso": 2,//QUEMADO
//         "Causa_ext": "13",//QUEMADO
//         "Terapia": 2,//PARÁMETRO
//         "Nit_asegura": "0",//QUEMADO
//         "Rs_asegura": "0",//QUEMADO
//         "Consec_soat": "",//QUEMADO
//         "No_poliza": 0,//QUEMADO
//         "Ufuncional": 11,//VARIABLE
//         "Embarazo": "",//VARIABLE
//         "Id_sede": 1,//VARIABLE
//         "PuntoAtencion": 8,//VARIABLE
//         "PolizaSalud": "",//QUEMADO
//         "serviciosObjDTOS": [
//             {
//                 "autoid": 34678,//VARIABLE
//                 "fuente_tips": 70,//VARIABLE
//                 "num_servicio": 70,//VARIABLE
//                 "cod_servicio": "911016",//VARIABLE
//                 "fecha_servicio": formatDate(hoy),//CALCULADO
//                 "descripcion": "ECOGRAFIA DOPPLER DE VASOS ARTERIALES DE MIEMBROS SUPERIORES A COLOR",//VARIABLE
//                 "cantidad": 1, //PARÁMETRO
//                 "vlr_servicio": 2000,//PARÁMETRO
//                 "total": 2000,//PARAMETRO
//                 "personal_ate": "1",//QUEMADO
//                 "cod_medico": "1",//QUEMADO
//                 "tipo_diag": 0,//VARIABLE
//                 "cod_diap": "",//VARIABLE
//                 "cod_diagn1": "",//VARIABLE
//                 "cod_diagn2": "",//VARIABLE
//                 "cod_diagn3": "",//VARIABLE
//                 "finalidad": 1,//QUEMADO
//                 "ambito_proc": 1,//QUEMADO
//                 "ccosto": "19",//PARÁMETRO
//                 "tipo_estudio": "A",//QUEMADO
//                 "ufuncional": 11,//VARIABLE
//                 "usuario": 1,//PARÁMETRO
//                 "tipoItem": "Procedimiento"//PARÁMETRO
//             }
//         ]
//     }
// ]

// const obtenerToken = async ()  => {

//     var respuesta;
//     let credenciales = {
//         "UserName":username,
//         "Password":password
//     }
//     console.log(credenciales);
//     let ruta = URL_BASE + "/api/AppApiUsers/Authenticate";
//     $.ajax({
//         async:false,
//         url:ruta,
//         method:"POST",
//         contentType: 'application/json',
//         enctype:'multipart/form-data',
//         data: JSON.stringify(credenciales),
//         // processData: false,
//         // cache: false,

//         success: function(response){ 
//             console.log(response.BearerToken);
//             respuesta = String(response.BearerToken);
//             TOKEN = String(response.BearerToken);
            
//         }, 
//         error: function(error){
//             console.log(error);
//             respuesta = error;
          
//         }
//     }); 
//     return respuesta;
// }

const  peticion_http = async (data, ruta, metodo = "GET", archivo = []) => {
    console.log(data, ruta, metodo, archivo);
    var respuesta;
    // let dataExportar = JSON.stringify({"data":data});
    // let token = await obtenerToken();
    $.ajax({
        async:false,
        url:ruta,
        type:metodo,
        data: data,
        headers: {
            'X-CSRFToken': csrftoken,
        },
        contentType: 'application/json',
        enctype:'multipart/form-data',
        // processData: false,
        // cache: false,

        success: function(response){ 
            console.log(response);
            respuesta =  response;
            
        }, 
        error: function(error){
            console.log(error);
            respuesta = error;
          
        }
    }); 


    return respuesta;
}

const enviarAdminsionPrueba = async () => {
    let respuesta = "";
    ruta = "/grabarAdmisionPrueba/"
    data = {}

    try{
        respuesta = await peticion_http(data, ruta, "GET");
        // respuesta = respuesta.Datos[0].infoTrasaction;
        console.log(respuesta);
    }catch(error){
        console.log(error);
        respuesta = `error: ${error.status} - ${error.statusText} - ${error.responseText}`;
    }
    // $('#respuestaAdmision').toggleClass("no_show");
    $('#respuestaAdmision').html(String(respuesta.Datos[0].infoTrasaction));
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



