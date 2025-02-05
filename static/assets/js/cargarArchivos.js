// const URL_BASE = "http://10.244.21.17:8022";


$('#archivoMasivoActividades').on('change', () => {
    $('#archivoCargado').html = $('#archivoMasivoActividades').get(0).files[0].name;
    console.log("Si carga el archivo");
});

$('#btnCargarActividadesArchivo').on('click',() => {
    $('.iconoCargador').addClass("loader");
    let archivo = $('#archivoMasivoActividades').get(0).files[0];

    let ruta = "/cargarActividades/";

    json = {};

    console.log(json);

    data = JSON.stringify(json);
    
    respuesta = peticion_archivos(data, ruta, "POST", false, archivo);

    console.log(respuesta)

    tablaActividadesSubir.clear().draw();
    tablaActividadesSubir.rows.add(respuesta).draw();
    $('.iconoCargador').removeClass("loader");   
});

$('#btnEnviarCargaActividades').on('click', () => {

    let ruta = "/procesarCargueActividades/";
    
    data = {
        "observacion":$('#observacion_carga').val(),
        "datos":respuesta
    }
   
    data = JSON.stringify(data);

    respuesta = peticion_archivos(data, ruta,"POST");

    console.log(respuesta);

    tablaActividadesSubir.clear().draw();

    if(respuesta){
        alert(`✅Se ha creado la Carga # ${respuesta.num_carga}`);
    }else{
        alert(`🚫Error al procesar la carga`)
    }
    
});






