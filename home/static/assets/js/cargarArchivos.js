// const URL_BASE = "http://10.244.21.17:8022";


$('#archivoMasivoActividades').on('change', () => {
    $('#archivoCargado').html = $('#archivoMasivoActividades').get(0).files[0].name;
    console.log("Si carga el archivo");
});


$('#btnEnviarCargaActividades').on('click', async () => {
    let archivo = $('#archivoMasivoActividades').get(0).files[0];
    let tipoActividad = $('#tipoActividad').val();
    let ruta = "/cargarActividades/";

    json = {
        'tipoActividad':tipoActividad
    }

    console.log(json);

    data = JSON.stringify(json);
    
    respuesta = await peticion_archivos(data, ruta, "POST", archivo);

    console.log(respuesta)
});


