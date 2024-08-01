
const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value; // Se utiliza para poder enviar petición tipo POST a Django


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


const  peticion_archivos = async (data, ruta, metodo = "GET", archivo = []) => {
   
    let formData = new FormData();
    let fileData = archivo;

    var data = JSON.stringify(data);

    formData.append("data");
    formData.append("adjunto",fileData);


    $.ajax({
        url: ruta,
        method:"POST",
        headers: {'X-CSRFToken': csrftoken},
        contentType: false,
        data: formData,
        enctype:'multipart/form-data',
        processData: false,
        cache: false,

        success:function(response){
            console.log(response);
            console.log("Petición exitosa");
            alert("Carga enviada");
            location.reload();
        }, 
        error: function(error){
            console.log("Hay un Pendejo error")
            console.log(error);
            alert("No se pudo realizar la carga.");
            //location.reload();
            
        }
        
    }); 


    return respuesta;
}