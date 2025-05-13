
const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value; // Se utiliza para poder enviar petición tipo POST a Django
const panel_loader = document.querySelector("#panel_loader");


const peticion_http = async (data, ruta, metodo = "GET", archivo = []) => {
    panel_loader.style.display = 'block';

    try {
        const respuesta = await new Promise((resolve, reject) => {
            $.ajax({
                url: ruta,
                type: metodo,
                data: data,
                headers: {
                    'X-CSRFToken': csrftoken,
                },
                contentType: 'application/json',
                enctype: 'multipart/form-data',
                success: function(response) {
                    resolve(response);
                },
                error: function(error) {
                    reject(error);
                }
            });
        });

        return respuesta;
    } catch (error) {
        console.error(error);
        return error;
    } finally {
        panel_loader.style.display = 'none'; 
    }
};

const  peticion_archivos = async (data, ruta, metodo = "GET", sincrono = false, archivo = []) => {
    panel_loader.style.display = 'block';
    let formData = new FormData();
    let fileData = archivo;

    formData.append("data", data);
    if(fileData){
        formData.append("adjunto",fileData);
    }

    try {
        const respuesta = await new Promise((resolve, reject) =>{

            $.ajax({
                // async:sincrono,
                url: ruta,
                method:metodo,
                headers: {'X-CSRFToken': csrftoken},
                contentType: false,
                data: formData,
                enctype:'multipart/form-data',
                processData: false,
                cache: false,
                success: async function(response){
                    resolve(response);
                    alert("Carga enviada");
                }, 
                error: function(error){
                    reject(error);
                    respuesta = false;
                    alert("No se pudo realizar la carga.");
                    
                }
        
            });
        });
        
        return respuesta;
    }catch(error){
        console.error(error);
        return error;
    }finally{
        panel_loader.style.display = 'none'; 
    }
        
   
}