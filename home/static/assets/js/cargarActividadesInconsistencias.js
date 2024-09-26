$(document).ready(async function () {
    
    $('#tablaActividadesInconsistencias').DataTable({
        ajax: {
            url:"/listarActividadesInconsistencias/",
            dataSrc:'data',
            type:'POST',
            headers: {
                'X-CSRFToken': csrftoken,
            },
        },
        processing:true,
        serverSide:true,
        
    }); 

})

