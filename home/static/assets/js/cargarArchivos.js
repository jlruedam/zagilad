// const URL_BASE = "http://10.244.21.17:8022";


$('#archivoMasivoActividades').on('change', () => {
    $('#archivoCargado').html = $('#archivoMasivoActividades').get(0).files[0].name;
    console.log("Si carga el archivo");
});


$('#btnCargarActividadesArchivo').on('click', async () => {
    let archivo = $('#archivoMasivoActividades').get(0).files[0];

    let ruta = "/cargarActividades/";

    json = {};

    console.log(json);

    data = JSON.stringify(json);
    
    respuesta = await peticion_archivos(data, ruta, "POST", archivo);

    console.log(respuesta)

    tablaActividadesSubir.clear().draw();
    tablaActividadesSubir.rows.add(respuesta).draw();   
});


$('#btnEnviarCargaActividades').on('click', async () => {
    let ruta = "/procesarCargueActividades/";
    let areaPrograma = $('#areaPrograma').val();

    data = {
        "areaPrograma":areaPrograma,
        "datos":respuesta
    }
   
    data = JSON.stringify(data);

    respuesta = await peticion_archivos(data, ruta,"POST");

    tablaActividadesSubir.clear().draw();
    tablaActividadesSubir.rows.add(respuesta).draw();

});





