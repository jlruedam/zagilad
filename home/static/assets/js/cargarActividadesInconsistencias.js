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
        columns:[
            {data:'id'},
            {data:'regional'}, 
            {data:'fecha_servicio'}, 
            {data:'nombre_actividad'},
            {data:'diagnostico_p'}, 
            {data:'tipo_documento'}, 
            {data:'documento_paciente'},
            {data:'nombre_paciente'}, 
            {data:'carga',
                "render": function(data, type, row) {
                    return '<a href="/verCarga/'+data+'/1">'+data+'</a>'
                 }
            },
            {data:'admision__numero_estudio'},
            {data:'inconsistencias'},
            {data:'medico__documento'},
        ],
        ordering:false,
        processing:true,
        serverSide:true,
        
        
    }); 

})

