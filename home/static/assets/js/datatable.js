const tablaActividadesSubir = $('#tablaActividadesSubir').DataTable({});

const tablaCargas =  $('#tablaCargas').DataTable({
    order: [[ 1, "desc" ]]
});
const tablaActividadesCargadas =  $('#tablaActividadesCargadas').DataTable({
    paging: false,
    info:false,
    searching: false
});
const tablaActividades = $('#tablaActividades').DataTable(); 
const tablaActividadesAdmisionar = $('#tablaActividadesAdmisionar').DataTable(); 
const tablaActividadesAdmisionadas =  $('#tablaActividadesAdmisionadas').DataTable();
const tablaActividadesInconsistencias =  $('#tablaActividadesInconsistencias').DataTable();
