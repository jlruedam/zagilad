from home.modules import email

URL_VER_CARGA = "http://zagilad.sersocial.org/verCarga/"

FUENTE_CORREO = 'ZAGILAD'

def notificar_carga_procesada(carga, receptores =[]):
    '''Colabordor realiza la solicitud, se notifica al colaborador que realiza la solicitud ya su jefe inmediato'''
    asunto = f'''{FUENTE_CORREO} - Carga #{carga.id}'''

    # Mensaje a enviar
    mensaje = f'''
        <div>
            <h4>
                Se informa que  la {carga} ha sido procesada. 
                Ingrese a la plataforma para realizar su respectiva gestión.
            </h4>
            <a href={URL_VER_CARGA + str(carga.id)}>Ver carga...</a>

            <table style="border:1px solid black; width:100% text-align:center">
                <thead>
                    <th style="border:1px solid black;">Número de carga</td>
                    <th style="border:1px solid black;">Estado</td>
                    <th style="border:1px solid black; color:green;">Tiempo procesamiento</td>
                    <th style="border:1px solid black; color:green;">Cantidad actividades</td>
                </thead>
                <tbody>
                    <tr>
                        <td>{carga.id}</td>
                        <td>{carga.estado}</td>
                        <td>{carga.tiempo_procesamiento}</td>
                        <td>{carga.cantidad_actividades}</td>
                    </tr>
                </tbody>
            </table>
        </div>
    '''
    
    email.enviar_email(asunto, mensaje, receptores)


    return True


def notificar_carga_admisionada(carga, receptores =[]):
    '''Colabordor realiza la solicitud, se notifica al colaborador que realiza la solicitud ya su jefe inmediato'''
    asunto = f'''{FUENTE_CORREO} - Carga #{carga.id}'''

    # Mensaje a enviar
    mensaje = f'''
        <div>
            <h4>
                Se informa que  las actividades de la {carga} han sido admisioandas. 
                Ingrese a la plataforma para realizar su respectiva gestión.
            </h4>
            <a href={URL_VER_CARGA + str(carga.id)}>Ver carga...</a>
        </div>
    '''
    
    email.enviar_email(asunto, mensaje, receptores)


    return True
