$(document).ready(async function () {
    let num_carga = $('#tablaActividadesCargadas').attr('carga');
    console.log(num_carga);
    admisionada = false;
    var tabla = $('#tablaActividadesCargadas').DataTable({
        ajax: {
            url:"/listarActividadesCarga/"+num_carga,
            dataSrc:'data',
            type:'POST',
            headers: {
                'X-CSRFToken': csrftoken,
            },
            data: function(d){
                console.log(d.columns);
            }
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
            {
                data:'admision__numero_estudio',
                "render": function(data, type, row) {
                    admisionada = true;
                    if(data){
                        admisionada = true;
                        return '<div ><a href="">'+data+'</a></div>'
                    }
                    return '<div ><a href=""></a></div>'
                    
                 }
            },
            {data:'inconsistencias'},
            {data:'medico__documento'},
            {
                data:'id',
                "render": function(data, type, row) {
                    console.log(self.columns);
                    console.log(admisionada);
                    if(admisionada){
                        console.log(admisionada);
                        return '✅'
                    }
                    return '<div id="botonesGestionActividad"><span class = "mybtn-emoji"><a href="/admisionarActividadIndividual/'+data+'/1" title="Admisionar" id="botonesGestionActividad">🆙</a></span><span class = "mybtn-emoji"><a href="/eliminarActividadIndividual/'+data+'/1" title="Eliminar">🗑️</a></span></div>'
                 }
            },
            
        ],
        ordering:false,
        processing:true,
        serverSide:true,
    });
    
    $('#botonesGestionActividad').html

})
