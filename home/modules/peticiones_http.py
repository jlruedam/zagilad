import requests
import json
from zagilad.settings import URL_API_ZEUS, URL_API_ZEUS_PRUEBA, USUARIO_API_ZEUS, PASSWORD_API_ZEUS
from home.models import TokenApiZeus



USERNAME = USUARIO_API_ZEUS
PASSWORD = PASSWORD_API_ZEUS
VIGENCIA_TOKEN = 1

# Peticiones HTTP

def obtener_token():
    token = False
    # Configurar Vigencia del Token
    TokenApiZeus.vigencia = VIGENCIA_TOKEN

    # Validar el vencimiento de los token
    tokens_vigentes = TokenApiZeus.objects.filter(vigente = True)
    if tokens_vigentes:
        for t in tokens_vigentes:
            t.validar_vencimiento()
        
        # Guardar el último token vigente
        token = TokenApiZeus.objects.filter(vigente = True).last()
        print("TOKEN AUN VIGENTE", token) 

        if token:
            return token.token
        
    ruta_endpoint = "/api/AppApiUsers/Authenticate"
    cabeceras = {
        'cache-control': 'no-cache', 
        'Access-Control-Allow-Origin': '*.sersocial.org',
        'Content-Type': 'application/json'
    }
    auth_data = {
        "UserName":USERNAME,
        "Password":PASSWORD
    }
    print(auth_data)
    respuesta = requests.post(URL_API_ZEUS + ruta_endpoint, headers=cabeceras, data = json.dumps(auth_data) ) 
    if respuesta.status_code == 200:
        respuesta = respuesta.json()
        token_bd = TokenApiZeus(
            token = respuesta['BearerToken']
        )
        token_bd.save()
        token = token_bd.token
        print("NUEVO TOKEN: ", token)

    return token


def crear_admision_prueba(admision, token):
    print("CONECTADO A:", URL_API_ZEUS_PRUEBA)
    respuesta = []
    ruta_endpoint = "/api/Admision/GrabarAdmision"
    cabeceras = {
        'cache-control': 'no-cache', 
        'Access-Control-Allow-Origin': '*.sersocial.org',
        'Content-Type': 'application/json',
        'Authorization':token,
    }

    respuesta = requests.post(URL_API_ZEUS + ruta_endpoint, headers=cabeceras, data = json.dumps(admision) ) 
    print(respuesta)
    if respuesta.status_code == 200:
        try:
            respuesta = respuesta.json()
        except Exception as e:
            print("Error al convertir a JSON", e)
            respuesta = False
    else:
        respuesta = False
       
    return respuesta

def crear_admision(admision, token):
    print("CONECTADO A:", URL_API_ZEUS)
    respuesta = []
    ruta_endpoint = "/api/Admision/GrabarAdmision"
    cabeceras = {
        'cache-control': 'no-cache', 
        'Access-Control-Allow-Origin': '*.sersocial.org',
        'Content-Type': 'application/json',
        'Authorization':token,
    }

    respuesta = requests.post(URL_API_ZEUS + ruta_endpoint, headers=cabeceras, data = json.dumps(admision) ) 
    print(respuesta)
    if respuesta.status_code == 200:
        respuesta = respuesta.json()
    else:
        respuesta = False
       
    return respuesta

def consultar_data(ruta, data = [], token = ""):
    print("CONECTADO A:", URL_API_ZEUS)
    respuesta = []
    ruta_endpoint = ruta
    cabeceras = {
        'cache-control': 'no-cache', 
        'Access-Control-Allow-Origin': '*.sersocial.org',
        'Content-Type': 'application/json',
    }
    if token:
        cabeceras['Authorization'] = token

    if data:
        respuesta = requests.get(URL_API_ZEUS + ruta_endpoint, headers=cabeceras ,data=data) 
        print(respuesta.json())
    else:
        respuesta = requests.get(URL_API_ZEUS + ruta_endpoint, headers=cabeceras) 
        # print(respuesta.status_code)
        # print(respuesta.json())
        
    if respuesta.status_code == 200:
        respuesta = respuesta.json()

    return respuesta


