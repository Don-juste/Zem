from configuration import fm
from fastapi_mail import MessageSchema

async def envoyer_message(email:str,mot_de_passe:str):
    message=MessageSchema(
        subject="Votre compte a été créé, vos informations:",
        recipients=[email],
        body=f"Votre code de connexion :email: {email} et mot de passe: {mot_de_passe} ",
        subtype="plain"
    )
    await fm.send_message(message)