const tablaActividadesSubir = $('#tablaActividadesSubir').DataTable({
    responsive: {
        details: {
            display: $.fn.dataTable.Responsive.display.childRow,
            renderer: $.fn.dataTable.Responsive.renderer.listHiddenNodes(),
            type: 'inline'   // clic en cualquier parte de la fila despliega el acordeón
        }
    },
    columnDefs: [
        // Columnas siempre visibles: N° identificación, Fecha, Nombre actividad, Estado
        { responsivePriority: 1, targets: [1, 7, 8, 12] },
        // Columnas de prioridad media: Tipo doc, Primer apellido, Primer nombre, Regional
        { responsivePriority: 2, targets: [0, 2, 4, 6] },
        // Columnas que se ocultan primero: Segundo apellido, Segundo nombre, Ciex, Médico, Finalidad
        { responsivePriority: 10001, targets: [3, 5, 9, 10, 11] }
    ]
});

const tablaCargas = $('#tablaCargas').DataTable({
    order: [[ 0, 'desc' ]],
    responsive: {
        details: {
            display: $.fn.dataTable.Responsive.display.childRow,
            renderer: $.fn.dataTable.Responsive.renderer.listHiddenNodes(),
            type: 'inline'   // clic en cualquier parte de la fila despliega el acordeón
        }
    },
    columnDefs: [
        // Siempre visibles: ID, Estado, Exportar, Ver
        { responsivePriority: 1, targets: [0, 2, 12, 13] },
        // Alta prioridad: Usuario, Avance, Total, Admisionadas
        { responsivePriority: 2, targets: [1, 3, 4, 7] },
        // Media: Inconsistencias, Para admisionar
        { responsivePriority: 3, targets: [5, 6] },
        // Se ocultan primero: Tiempo, Observación, Created, Updated
        { responsivePriority: 10001, targets: [8, 9, 10, 11] }
    ]
});
// const tablaActividadesCargadas =  $('#tablaActividadesCargadas').DataTable({
//     paging: false,
//     info:false,
//     searching: false
// });

const tablaTiposActividad = $('#tablaTiposActividad').DataTable({
    responsive: {
        details: {
            display: $.fn.dataTable.Responsive.display.childRow,
            renderer: $.fn.dataTable.Responsive.renderer.listHiddenNodes(),
            type: 'inline'
        }
    },
    columnDefs: [
        // Siempre visibles: Id, Nombre, Área
        { responsivePriority: 1, targets: [0, 2, 12] },
        // Alta: Grupo, CUPS, Contrato, Tipo servicio
        { responsivePriority: 2, targets: [1, 3, 10, 11] },
        // Se ocultan primero: Responsable, Diagnóstico, Finalidad, Fuente, Observación, Entrega
        { responsivePriority: 10001, targets: [4, 5, 6, 7, 8, 9] }
    ]
});

const tablaParametrosPrograma = $('#tablaParametrosPrograma').DataTable({
    responsive: {
        details: {
            display: $.fn.dataTable.Responsive.display.childRow,
            renderer: $.fn.dataTable.Responsive.renderer.listHiddenNodes(),
            type: 'inline'
        }
    },
    columnDefs: [
        // Siempre visibles: Id, Área, Regional, Editar
        { responsivePriority: 1, targets: [0, 1, 2, 7] },
        // Alta: Unidad funcional, Punto atención
        { responsivePriority: 2, targets: [3, 4] },
        // Se ocultan primero: Centro costo, Sede
        { responsivePriority: 10001, targets: [5, 6] },
        // Editar no es ordenable
        { orderable: false, targets: [7] }
    ]
});
const tablaActividades = $('#tablaActividades').DataTable(); 
const tablaActividadesAdmisionar = $('#tablaActividadesAdmisionar').DataTable(); 
// const tablaActividadesInconsistencias =  $('#tablaActividadesInconsistencias').DataTable();
