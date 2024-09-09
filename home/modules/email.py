from django.core.mail import send_mail
from zagilad.settings import EMAIL_HOST_USER

CORREO_APP  = EMAIL_HOST_USER

def enviar_email(asunto, mensaje,destinatarios):
    print(destinatarios)
    return send_mail(asunto,mensaje, CORREO_APP, destinatarios, fail_silently=False, html_message=mensaje)
