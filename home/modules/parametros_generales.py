from ..models import ParametrosAreaPrograma,AreaPrograma, Regional
from zeus_mirror.models import UnidadFuncional, CentroCosto, PuntoAtencion
from zeus_mirror.views import listar_unidades_funcionales, listar_centros_costos
from zeus_mirror.views import listar_puntos_atencion, listar_contratos
from zeus_mirror.views import listar_seriales_sedes, listar_tipos_servicios

# PARÁMETROS GENERALES
CODIGO_MEDICO = 1
NOMBRE_USUARIO = "LUIS FERNANDO RODRIGUEZ"
NUMERO_USUARIO = 1
IDENTIFICACION_USUARIO = "1047394846"
TIPO_DIAGNOSTICO = 1
CODIGO_ENTIDAD = {
    "Contributivo": "EPS048",
    "Subsidiado":"ESS207"
}


parametros_arranque = {

    "REGIONALES":[
        "BOLIVAR NORTE",
        "BOLIVAR CENTRO",
        "BOLIVAR SUR",
        "ATLANTICO",
        "MAGDALENA",
        "SUCRE",
        "CORDOBA",
    ],

    "AREA":{
        "GR":"GESTION RIESGO",
        "SJ":"SER JOVEN"
    },   
    
    "PARAMETROS_AREAS":[
        {
            "area":"GR",
            "regional":"ATLANTICO",
            "unidad":"13",#CODIGO GRS-ATLANTICO
            "punto_atencion":"010",#CODIGO IPS FUNDACION SERSOCIAL GRS ATLANTICO
            "centro_costo":"0014",#CODIGO GRS-ATLANTICO
            "sede":"1"
        },
        {
            "area":"GR",
            "regional":"BOLIVAR CENTRO",
            "unidad":"14",
            "punto_atencion":"011",
            "centro_costo":"0015",
            "sede":"1"
        },
        {
            "area":"GR",
            "regional":"BOLIVAR NORTE",
            "unidad":"15",
            "punto_atencion":"012",
            "centro_costo":"0016",
            "sede":"1"
        },
        {
            "area":"GR",
            "regional":"MAGDALENA",
            "unidad":"18",
            "punto_atencion":"015",
            "centro_costo":"0017",
            "sede":"1"
        },
        {
            "area":"GR",
            "regional":"BOLIVAR SUR",
            "unidad":"16",
            "punto_atencion":"013",
            "centro_costo":"0019",
            "sede":"1"
        },
        {
            "area":"GR",
            "regional":"SUCRE",
            "unidad":"19",
            "punto_atencion":"016",
            "centro_costo":"0018",
            "sede":"1"
        },
        {
            "area":"GR",
            "regional":"CORDOBA",
            "unidad":"17",
            "punto_atencion":"014",
            "centro_costo":"0020",
            "sede":"1"
        },
        {
            "area":"SJ",
            "regional":"BOLIVAR NORTE",
            "unidad":"01",
            "punto_atencion":"001",
            "centro_costo":"0002",
            "sede":"1"
        },
        { 
            "area":"SJ",
            "regional":"BOLIVAR CENTRO",
            "unidad":"0102",
            "punto_atencion":"001",
            "centro_costo":"0005",
            "sede":"1"
        },
        { 
            "area":"SJ",
            "regional":"BOLIVAR SUR",
            "unidad":"0103",
            "punto_atencion":"001",
            "centro_costo":"0006",
            "sede":"1"
        },
        { 
            "area":"SJ",
            "regional":"MAGDALENA",
            "unidad":"02",
            "punto_atencion":"002",
            "centro_costo":"0003",
            "sede":"1"
        },
        { 
            "area":"SJ",
            "regional":"CORDOBA",
            "unidad":"03",
            "punto_atencion":"003",
            "centro_costo":"0004",
            "sede":"1"
        },
        { 
            "area":"SJ",
            "regional":"ATLANTICO",
            "unidad":"09",
            "punto_atencion":"005",
            "centro_costo":"0008",
            "sede":"1"
        },
        { 
            "area":"SJ",
            "regional":"SUCRE",
            "unidad":"10",
            "punto_atencion":"006",
            "centro_costo":"0009",
            "sede":"1"
        },
        
        

    ],
    
    "CONTRATOS_MARCOS":[
        {
            "numero":"21952",
            "contrato_subsidiado":"151",
            "contrato_contributivo":"150",
            "observacion":"Contrato gestión de riesgo"
        },

    ]
}

async def cargar_configuracion_default():

    await listar_unidades_funcionales(0)
    await listar_centros_costos(0)
    await listar_puntos_atencion(0)
    await listar_contratos(0)
    await listar_seriales_sedes(0)
    await listar_tipos_servicios(0)

    regionales = Regional.objects.count()
    if not regionales:
        for regional in parametros_arranque["REGIONALES"]:
            print(regional)
            regional_nueva = Regional(
               regional = regional
            )
            regional_nueva.save()

        
    areas = AreaPrograma.objects.count()
    if not areas:
        for identificador,nombre in (parametros_arranque["AREA"]).items():
            print(identificador,nombre)
            area_nueva = AreaPrograma(
                identificador = identificador,
                nombre = nombre
            )
            area_nueva.save()

    if areas or regionales:
        return False
    else:
        return True
    
def parametros_area_default():

    parametros_areas = ParametrosAreaPrograma.objects.exists()
    if not parametros_areas:
        for parametros in parametros_arranque["PARAMETROS_AREAS"]:
            print(parametros)

            nuevos_parametros = ParametrosAreaPrograma(
                area_programa = AreaPrograma.objects.get(identificador = parametros['area']),
                regional = Regional.objects.get(regional = parametros['regional']),
                unidad_funcional = UnidadFuncional.objects.get(codigo = parametros['unidad']),
                punto_atencion = PuntoAtencion.objects.get(codigo = parametros['punto_atencion']),
                centro_costo = CentroCosto.objects.get(codigo = parametros['centro_costo']),
            )

            nuevos_parametros.save()
        
        return True
    else:
        return False
    
        