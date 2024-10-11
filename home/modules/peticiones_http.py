import requests
import json
from zagilad.settings import USUARIO_API_ZEUS, PASSWORD_API_ZEUS
ZEUS_API = {
    "prueba":"http://10.244.21.17:8022",
    "produccion":"http://131.0.170.93:8030"
}

# URL_API_ZEUS = ZEUS_API['produccion']
URL_API_ZEUS = ZEUS_API['prueba']

USERNAME = USUARIO_API_ZEUS
PASSWORD = PASSWORD_API_ZEUS

# Peticiones HTTP

def obtener_token():
    token = ''
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
        token = respuesta['BearerToken']

    return token

def crear_admision(admision, token):
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
       
    return respuesta

def consultar_data(ruta, data = [], token = ""):
    print(URL_API_ZEUS)
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


