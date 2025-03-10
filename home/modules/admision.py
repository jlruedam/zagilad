from datetime import datetime, date, timedelta

hoy = date.today() - timedelta(days=10)

admision_prueba =  [{
        "autoid": 34678, #VARIABLE
        "Cod_entidad": "ESS207",#PARÁMETRO ESPECÍFICO - LA EPS, lo da el afiliado
        "tipo_estudio": "A",#QUEDMADO
        "nro_autoriza": "",#QUEDMADO
        "Cod_clasi": "01",#QUEDMADO
        "Fecha_ing":hoy.isoformat(),#CALCULADO
        "Hora_ing": "08:00",#QUEDMADO
        "Cod_medico": 1,#PARAMETRO
        "Nro_factura": 0,#CALCULADO
        "Estado": "A",#QUEDMADO
        "Obs": "Admisión de prueba JLRM",#VARIABLE
        "Cod_usuario": "1047394846",#PARÁMETRO GENERAL
        "Nom_usuario": "LUIS FERNANDO RODRIGUEZ",#PARÁMETRO GENERAL
        "Contrato": 150,#PARÁMETRO ESPECÍFICO 
        "Status_regis": 0,#QUEDMADO
        # "Estado_res": 0,
        "Usuario_estado_res": "1047394846",#PARÁMETRO
        "Codigo_servicio": "63",#VARIABLE // **Es realmente unidad funcional
        "Via_ingreso": 2,#QUEMADO
        "Causa_ext": "13",#QUEMADO
        "Terapia": 0,#QUEMADO
        "Nit_asegura": "0",#QUEMADO
        "Rs_asegura": "0",#QUEMADO
        "Consec_soat": "",#QUEMADO
        "No_poliza": 0,#QUEMADO
        "Ufuncional": 63,#VARIABLE
        "Embarazo": "",#VARIABLE
        "Id_sede": 1,#VARIABLE
        "PuntoAtencion": 16,#VARIABLE
        "PolizaSalud": "",#QUEMADO
        "serviciosObjDTOS": [
            {
                "autoid": 34678,#VARIABLE
                "fuente_tips": 87,#VARIABLE //Viene siendo el codigo del servicio
                "num_servicio": 1,#VARIABLE
                "cod_servicio": "990211", #"990204",#VARIABLE
                "fecha_servicio": hoy.isoformat(),#CALCULADO
                "descripcion": "EDUCACION INDIVIDUAL EN SALUD, POR ENFERMERIA",#VARIABLE
                "cantidad": 1, #PARÁMETRO
                "vlr_servicio": 0,#PARÁMETRO
                "total": 0,#PARAMETRO
                "personal_ate": "1",#QUEMADO
                "cod_medico": "1",#QUEMADO
                "tipo_diag": 1,#VARIABLE
                "cod_diap": "",#VARIABLE
                "cod_diagn1": "",#VARIABLE
                "cod_diagn2": "",#VARIABLE
                "cod_diagn3": "",#VARIABLE
                "finalidad": 10,#QUEMADO
                "ambito_proc": 1,#QUEMADO
                "ccosto": "0016",#PARÁMETRO
                "tipo_estudio": "A",#QUEMADO
                "ufuncional": 63,#VARIABLE
                "usuario": 1,#PARÁMETRO
                "tipoItem": "Procedimiento"#PARÁMETRO
            }
        ]
    }
]

# def crear_admision(autoid, regimen, codigo_entidad, num_usuario, 
#                    usuario_id, usuario_nombre, tipo_diag, actividad):
    

def crear_admision(autoid, regimen, codigo_entidad, tipo_diag, actividad):

    # Validar tipo de actividad
    if not actividad.tipo_actividad:
        raise Exception("Tipo actividad no está definida para esta actividad")
    
    # Validar médico
    if not actividad.medico:
        raise Exception("No se tiene médico asignado")
    
    # # Validar médico
    # if not actividad.usuario_zeus:
    #     raise Exception("Usuario no encontrado")
    
    # Validar médico
    if not actividad.parametros_programa:
        raise Exception("Párametros del programa no están configurados")
    

    contrato_subsidiado = actividad.tipo_actividad.contrato.contrato_subsidiado 
    contrato_contributivo = actividad.tipo_actividad.contrato.contrato_contributivo
    
    contrato = {
        "Subsidiado": contrato_subsidiado.codigo if contrato_subsidiado else "",
        "Contributivo": contrato_contributivo.codigo if contrato_contributivo else ""
    }

    admision_formato =  [{
        "autoid": autoid, #VARIABLE
        "Cod_entidad": codigo_entidad,#PARÁMETRO - CONTRATO
        "tipo_estudio": "A",#QUEDMADO
        "nro_autoriza": "",#QUEDMADO
        "Cod_clasi": "01",#QUEDMADO
        "Fecha_ing":(actividad.fecha_servicio).isoformat(),#CALCULADO
        "Hora_ing": "08:00",#QUEDMADO
        "Cod_medico": actividad.medico.codigo,#PARAMETRO
        "Nro_factura": 0,#QUEDMADO
        "Estado": "A",#QUEDMADO
        "Obs": actividad.nombre_actividad,#VARIABLE
        # "Cod_usuario": actividad.medico.documento,#PARÁMETRO
        # "Nom_usuario": actividad.medico.nombre,#PARÁMETRO
        "Cod_usuario": actividad.cedula_usuario,#PARÁMETRO
        "Nom_usuario": actividad.nombre_usuario,#PARÁMETRO
        "Contrato": contrato[regimen],#endpoint no funciona #PARÁMETRO
        "Status_regis": 0,#QUEDMADO
        # "Estado_res": 0,
        # "Usuario_estado_res": actividad.medico.documento,#PARÁMETRO
        "Usuario_estado_res": actividad.cedula_usuario,#PARÁMETRO,#PARÁMETRO
        "Codigo_servicio":str(actividad.parametros_programa.unidad_funcional.id_zeus), #VARIABLE // **Es realente unidad funcional
        "Via_ingreso": 2,#QUEMADO
        "Causa_ext": "13",#QUEMADO
        "Terapia": 0,#QUEMADO
        "Nit_asegura": "0",#QUEMADO
        "Rs_asegura": "0",#QUEMADO
        "Consec_soat": "",#QUEMADO
        "No_poliza": 0,#QUEMADO
        "Ufuncional":actividad.parametros_programa.unidad_funcional.codigo,#VARIABLE
        "Embarazo": "",#QUEMADO
        "Id_sede": actividad.parametros_porgrama.sede.id_zeus,#VARIABLE
        "PuntoAtencion": actividad.parametros_programa.punto_atencion.id_zeus,#VARIABLE
        "PolizaSalud": "",#QUEMADO
        "serviciosObjDTOS": [
            {
                "autoid": autoid,#VARIABLE
                "fuente_tips": actividad.tipo_actividad.tipo_servicio.id_zeus,#VARIABLE //Viene siendo el codigo del servicio
                "num_servicio": actividad.id,#VARIABLE
                "cod_servicio": actividad.tipo_actividad.cups,#VARIABLE
                "fecha_servicio": (actividad.fecha_servicio).isoformat(),#CALCULADO
                "descripcion": actividad.tipo_actividad.nombre,#VARIABLE
                "cantidad": 1, #PARÁMETRO
                "vlr_servicio": 0,#PARÁMETRO
                "total": 0,#PARAMETRO
                "personal_ate": actividad.medico.codigo,#QUEMADO
                "cod_medico":actividad.medico.codigo,#QUEMADO
                "tipo_diag": tipo_diag,#VARIABLE
                "cod_diap": "" if actividad.diagnostico_p == 'nan' or actividad.diagnostico_p == '0' else actividad.diagnostico_p.strip(),#VARIABLE
                "cod_diagn1":"" if actividad.diagnostico_1 == 'nan' or actividad.diagnostico_1 == '0' else actividad.diagnostico_1.strip(),#VARIABLE
                "cod_diagn2": "" if actividad.diagnostico_2 == 'nan' or actividad.diagnostico_2 == '0' else actividad.diagnostico_2.strip(),#VARIABLE
                "cod_diagn3": "" if actividad.diagnostico_3 == 'nan' or actividad.diagnostico_3 == '0' else actividad.diagnostico_3.strip(),#VARIABLE
                "finalidad": 10,#QUEMADO
                "ambito_proc": 1,#QUEMADO
                "ccosto": actividad.parametros_programa.centro_costo.codigo,#PARÁMETRO
                "tipo_estudio": "A",#QUEMADO
                "ufuncional": actividad.parametros_programa.unidad_funcional.id_zeus,#VARIABLE
                "usuario": actividad.id_usuario,#PARÁMETRO
                "tipoItem": "Procedimiento"#PARÁMETRO
            }
        ]
       }
    ]

    return admision_formato