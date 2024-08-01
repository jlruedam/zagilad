from datetime import datetime, date, timedelta


hoy = date.today() - timedelta(days=10)

admision_prueba =  [{
        "autoid": 34678, #VARIABLE
        "Cod_entidad": "ESS207",#PARÁMETRO - CONTRATO
        "tipo_estudio": "A",#QUEDMADO
        "nro_autoriza": "",#QUEDMADO
        "Cod_clasi": "01",#QUEDMADO
        "Fecha_ing":hoy.isoformat(),#CALCULADO
        "Hora_ing": "08:00",#QUEDMADO
        "Cod_medico": 1,#PARAMETRO
        "Nro_factura": 0,#CALCULADO
        "Estado": "A",#QUEDMADO
        "Obs": "Admisión de prueba JLRM",#VARIABLE
        "Cod_usuario": "1047394846",#PARÁMETRO
        "Nom_usuario": "LUIS FERNANDO RODRIGUEZ",#PARÁMETRO
        "Contrato": 150,#endpoint no funciona #PARÁMETRO
        "Status_regis": 0,#QUEDMADO
        # "Estado_res": 0,
        "Usuario_estado_res": "1047394846",#PARÁMETRO
        "Codigo_servicio": "63",#VARIABLE // **Es realente unidad funcional
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
                "cod_servicio": "990204",#VARIABLE
                "fecha_servicio": hoy.isoformat(),#CALCULADO
                "descripcion": "EDUCACION INDIVIDUAL EN SALUD, POR ENFERMERIA",#VARIABLE
                "cantidad": 1, #PARÁMETRO
                "vlr_servicio": 2000,#PARÁMETRO
                "total": 2000,#PARAMETRO
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