from configuration import fm
from fastapi_mail import MessageSchema
async def envoyer_otp(email:str,code:str):
    message=MessageSchema(
        subject="Votre code de connexion",
        recipients=[email],
        body=f"Votre code de connexion : {code}\n Il espire dans 5 min",
        subtype="plain"
    )
    await fm.send_message(message)
    
        