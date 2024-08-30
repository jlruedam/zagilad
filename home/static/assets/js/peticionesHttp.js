
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

const  peticion_archivos = (data, ruta, metodo = "GET", archivo = []) => {
   
    let formData = new FormData();
    let fileData = archivo;
    var res;

    formData.append("data", data);
    if(fileData){
        formData.append("adjunto",fileData);
    }
        
    $.ajax({
        async:false,
        url: ruta,
        method:metodo,
        headers: {'X-CSRFToken': csrftoken},
        contentType: false,
        data: formData,
        enctype:'multipart/form-data',
        processData: false,
        cache: false,

        success: async function(response){
            respuesta = response;
            console.log(respuesta);
            console.log("Petición exitosa");
            alert("Carga enviada");
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