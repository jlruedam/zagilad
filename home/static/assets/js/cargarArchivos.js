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
    
    respuesta = peticion_archivos(data, ruta, "POST", archivo);

    console.log(respuesta)

    tablaActividadesSubir.clear().draw();
    tablaActividadesSubir.rows.add(respuesta).draw();
    $('.iconoCargador').removeClass("loader");   
});


$('#btnEnviarCargaActividades').on('click', () => {
    console.log("CARGADOR ??");
    alert("Espere");
    $('.loader').show();
    let ruta = "/procesarCargueActividades/";
    let areaPrograma = $('#areaPrograma').val();
    
    data = {
        "areaPrograma":areaPrograma,
        "datos":respuesta
    }
   
    data = JSON.stringify(data);

    respuesta = peticion_archivos(data, ruta,"POST");

    for(inconsistencia of respuesta){
        console.log(inconsistencia);
    }

    tablaActividadesSubir.clear().draw();
    tablaActividadesSubir.rows.add(respuesta).draw();
    $('.loader').hide();  
    

});






