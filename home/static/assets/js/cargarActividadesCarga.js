$(document).ready(async function () {
    let num_carga = $('#tablaActividadesCargadas').attr('carga');
    console.log(num_carga);
    $('#tablaActividadesCargadas').DataTable({
        ajax: {
            url:"/listarActividadesCarga/"+num_carga,
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
            {data:'admision__numero_estudio'},
            {data:'inconsistencias'},
            {
                data:'id',
                "render": function(data, type, row) {
                    return '<span class = "mybtn-emoji"><a href="/admisionarActividadIndividual/'+data+'/1" title="Admisionar">🆙</a></span><span class = "mybtn-emoji"><a href="/eliminarActividadIndividual/'+data+'/1" title="Eliminar">🗑️</a></span>'
                 }
            },
            
        ],
        processing:true,
        serverSide:true,
    }); 

})
