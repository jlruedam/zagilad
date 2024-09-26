$(document).ready(async function () {
    
    $('#tablaActividadesInconsistencias').DataTable({
        ajax: {
            url:"/listarActividadesInconsistencias/",
            dataSrc:'datos'
        },
        processing:true,
        serverSide:true,
        pageLength:10,
        ordering:false,
        
    }); 

})

