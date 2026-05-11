$(document).ready(async function () {
    let num_carga = $('#tablaActividadesCargadas').attr('carga');
    console.log(num_carga);
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
                    admisionada = false;
                    if(data){
                        admisionada = true;
                        return '<div ><a href="">'+data+'</a></div>'
                    }
                    return '<div ><a href=""></a></div>'
                    
                 }
            },
            {data:'inconsistencias'},
            {data:'medico__documento'},
            {data:'finalidad__valor'},
            {
                data:'id',
                className: 'col-acciones',
                "render": function(data) {
                    return '<a class="btn-accion btn-accion--ver" href="/verActividad/'+data+'/" title="Ver detalle" aria-label="Ver detalle">🔍</a>';
                }
            },
            {
                data:'id',
                className: 'col-acciones',
                "render": function(data, type, row) {
                    if(admisionada){
                        return '<span class="btn-accion btn-accion--done" title="Admisionada" aria-label="Admisionada">✓</span>';
                    }
                    return '<div class="btns-gestion">'
                        + '<a class="btn-accion btn-accion--admisionar" href="/admisionarActividadIndividual/'+data+'/1" title="Admisionar" aria-label="Admisionar">🆙</a>'
                        + '<a class="btn-accion btn-accion--eliminar" href="/eliminarActividadIndividual/'+data+'/1" title="Eliminar" aria-label="Eliminar">🗑️</a>'
                        + '</div>';
                 }
            },
            
            
        ],
        ordering:false,
        processing:true,
        serverSide:true,
    });
    
    $('#botonesGestionActividad').html

    // ── Filtrado por tipo de inconsistencia ──
    // Al hacer click en una fila del resumen, aplica el texto de esa
    // inconsistencia como búsqueda global de DataTables. El backend ya
    // soporta inconsistencias__icontains a través de search[value].
    var $banner = $('#filtroInconsistenciaActivo');
    var $bannerTexto = $banner.find('.filtro-texto');
    var $btnQuitar = $('#btnQuitarFiltroInconsistencia');
    var $resumenWrapper = $('.bloqueTablaResumenInconsistencias');

    function aplicarFiltro(texto) {
        tabla.search(texto).draw();
        $bannerTexto.text(texto);
        $banner.addClass('visible');
        $resumenWrapper.find('tr').removeClass('is-active');
        $resumenWrapper.find('tr[data-inconsistencia]').filter(function () {
            return $(this).attr('data-inconsistencia') === texto;
        }).addClass('is-active');
        // scroll suave al banner para que el usuario vea el efecto
        var top = $banner.offset().top - 80;
        $('html, body').animate({ scrollTop: top }, 200);
    }

    function quitarFiltro() {
        tabla.search('').draw();
        $banner.removeClass('visible');
        $bannerTexto.text('');
        $resumenWrapper.find('tr').removeClass('is-active');
    }

    $resumenWrapper.on('click', 'td.tipo-inconsistencia', function () {
        var texto = $(this).closest('tr').attr('data-inconsistencia') || '';
        if (!texto) return;
        aplicarFiltro(texto);
    });

    $btnQuitar.on('click', quitarFiltro);

})
