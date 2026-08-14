import firebase_admin
from firebase_admin import credentials, messaging

cred = credentials.Certificate("firebase-key.json")
firebase_admin.initialize_app(cred)

def envoyer_notification(fcm_token: str, titre: str, corps: str):
    if fcm_token is None:
        return
    
    message = messaging.Message(
        notification=messaging.Notification(
            title=titre,
            body=corps
        ),
        token=fcm_token
    )
    
    try:
        messaging.send(message)
    except Exception as e:
        print(f"Erreur envoi notification FCM : {e}")