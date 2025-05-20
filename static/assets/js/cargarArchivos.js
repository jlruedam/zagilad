// const URL_BASE = "http://10.244.21.17:8022";


$('#archivoMasivoActividades').on('change', () => {
    $('#archivoCargado').html = $('#archivoMasivoActividades').get(0).files[0].name;
    console.log("Si carga el archivo");
});

$('#btnCargarActividadesArchivo').on('click',async () => {
    $('.iconoCargador').addClass("loader");
    let archivo = $('#archivoMasivoActividades').get(0).files[0];

    let ruta = "/cargarActividades/";

    json = {};
    console.log(json);
    data = JSON.stringify(json);
    
    respuesta = await peticion_archivos(data, ruta, "POST", false, archivo);
    console.log(respuesta);
    if(!respuesta.status){
        tablaActividadesSubir.clear().draw();
        tablaActividadesSubir.rows.add(respuesta).draw();
        
    }else{
        alert("Error: "+ respuesta.responseText);
    }
    $('.iconoCargador').removeClass("loader");   
    
});

$('#btnEnviarCargaActividades').on('click', async () => {

    let ruta = "/procesarCargueActividades/";
    
    data = {
        "observacion":$('#observacion_carga').val(),
        "datos":respuesta
    }
   
    data = JSON.stringify(data);

    respuesta = await peticion_archivos(data, ruta,"POST");

    console.log(respuesta);

    tablaActividadesSubir.clear().draw();

    if(!respuesta.status){
        alert(`✅Se ha creado la Carga # ${respuesta.num_carga}`);
    }else{
        alert(`🚫Error al procesar la carga`)
        console.log(respuesta)
    }
    
});






