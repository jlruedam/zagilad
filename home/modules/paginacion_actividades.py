
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Q
from datetime import datetime

def actividades_paginadas(dt, actividades):

    context = {}
    draw = int(dt.get("draw"))
    start = int(dt.get("start"))
    length = int(dt.get("length"))
    search = dt.get("search[value]")

    print("SEARCH:", search)
    print("START:", start)
    print("LENGTH:", length)

    if search:
        # Filtrar los campos que son texto
        filtros = Q(id__icontains=search)|Q(tipo_fuente__icontains=search)|Q(regional__icontains=search)
        filtros |= Q(nombre_actividad__icontains=search)|Q(diagnostico_p__icontains=search)|Q(documento_paciente__icontains=search)
        filtros |= Q(nombre_paciente__icontains=search)|Q(inconsistencias__icontains=search)
        filtros |= Q(tipo_documento=search)
        # Intentamos convertir el valor a una fecha 
        try:
            fecha = datetime.strptime(search, "%d/%m/%Y").date()
            filtros |= Q(fecha_servicio=fecha)
        except ValueError:
            pass

        
        actividades = actividades.filter(filtros)

    # Preparamos la salida
    total_registros = actividades.count()
    context["draw"] = draw
    context["recordsTotal"] = total_registros
    context["recordsFiltered"] = total_registros

    registros = actividades[start:(start + length)]
    paginator = Paginator(registros, length)

     # https://www.youtube.com/watch?v=UP9qBWI5G4E
    try:
        obj = paginator.page(draw).object_list
    except PageNotAnInteger:
        obj = paginator.page(draw).object_list
    except EmptyPage:
        obj = paginator.page(paginator.num_pages).object_list

    context["data"] = list((obj).values('id','regional', 'fecha_servicio', 
                                              'nombre_actividad','diagnostico_p', 'tipo_documento', 'documento_paciente',
                                              'nombre_paciente', 'carga','admision__numero_estudio','inconsistencias'))
    print("datos pagínados: ", context["data"])

    return context