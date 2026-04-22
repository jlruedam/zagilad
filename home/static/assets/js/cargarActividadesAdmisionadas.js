$(document).ready(async function () {
    
    $('#tablaActividadesAdmisionadas').DataTable({
        ajax: {
            url:"/listarActividadesAdmisionadas/",
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
            {data:'carga'},
            {data:'medico__documento'},
            {data:'admision__numero_estudio'},
            {
                data: 'id',
                className: 'col-acciones',
                render: function (data) {
                    return '<a class="btn-accion btn-accion--ver" href="/verActividad/' + data + '/" title="Ver detalle" aria-label="Ver detalle">🔍</a>';
                }
            },
            // {data:'inconsistencias'},
        ],
        ordering:false,
        processing:true,
        serverSide:true,
        
        
    }); 

})

