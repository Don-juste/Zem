from fastapi import FastAPI, HTTPException,Header,Request,File,UploadFile,Depends,WebSocket, WebSocketDisconnect
from jose import jwt,JWTError
from fastapi.security import OAuth2PasswordBearer,OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from slowapi import Limiter,_rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.middleware.cors import CORSMiddleware
import aiofiles
import uuid
import os
from datetime  import datetime, timedelta
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
load_dotenv()
from database import Base,engine,SessionLocal
import models
import shemas
import logging
from auth import hashe_mot_de_passe,verifier_mot_de_passe_hashe,generer_otp,verifier_otp,creer_access_token,creer_refresh_token,verifier_token
from mails1 import envoyer_otp
from geolocalisation import calculer_distance
from enums import TypeVehicule,StatutCourse,StatutZem
from mails2 import envoyer_message
from configuration import fm
from tarification import calculer_prix
connexions_actives = {}
logging.basicConfig(
    filename="app.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger=logging.getLogger(__name__)
SECRET_KEY=os.getenv("SECRET_KEY")
ADMIN_KEY=os.getenv("ADMIN_KEY")
OTP_EXPIRATION=int(os.getenv("OTP_EXPIRATION"))                
RATE_LIMIT=os.getenv("RATE_LIMIT")
ALGORITHM=os.getenv("ALGORITHM")
limiter=Limiter(key_func=get_remote_address)
app=FastAPI()
app.state.limiter=limiter
app.add_exception_handler(RateLimitExceeded,_rate_limit_exceeded_handler)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)
os.makedirs("uploads",exist_ok=True)
app.mount("/uploads",StaticFiles(directory="uploads"),name="uploads")
Base.metadata.create_all(bind=engine)
oauth2_sheme=OAuth2PasswordBearer(tokenUrl="connexion/zem")
oauth2_sheme_optionnel = OAuth2PasswordBearer(tokenUrl="connexion/zem", auto_error=False)

def get_db():
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()
MODELES={"admin":models.Administrateur,"zem":models.Zem}        
def get_current_user(token: str = Depends(oauth2_sheme), db: Session = Depends(get_db)):
    payload = verifier_token(token)
    modele = MODELES.get(payload["role"])
    if modele is None:
        raise HTTPException(status_code=401, detail="Token invalide")
    db_user = db.query(modele).filter(modele.email == payload["email"]).first()
    if db_user is None:
        raise HTTPException(status_code=401, detail="Token invalide")
    return db_user

def identifier_expediteur(
    x_client_token: str = Header(default=None),
    token: str = Depends(oauth2_sheme_optionnel),
    db: Session = Depends(get_db)
):
    if x_client_token:
        client = db.query(models.Client).filter(models.Client.token == x_client_token).first()
        if client is None:
            raise HTTPException(status_code=401, detail="Client invalide")
        return {"type": "client", "id": client.id}

    if token:
        payload = verifier_token(token)
        modele = MODELES.get(payload["role"])
        db_user = db.query(modele).filter(modele.email == payload["email"]).first()
        if db_user is None:
            raise HTTPException(status_code=401, detail="Token invalide")
        return {"type": "zem", "id": db_user.id}

    raise HTTPException(status_code=401, detail="Authentification requise")

def get_current_client(x_client_token: str = Header(...), db: Session = Depends(get_db)):
    client = db.query(models.Client).filter(models.Client.token == x_client_token).first()
    if client is None:
        raise HTTPException(status_code=401, detail="Client invalide")
    return client


@app.post("/Administrateur")
def creer_compte(user:shemas.AdminCreate,x_admin_key:str=Header(...),db:Session=Depends(get_db)):
    if ADMIN_KEY!=x_admin_key:
        logger.info(f"Accès réfusé :{user.email}")
        return {"Message":"Accès réfusé"}
    db_user=db.query(models.Administrateur).filter(models.Administrateur.email==user.email).first()
    if db_user:
        logger.warning(f"Email déjà utilisé")
        raise HTTPException(status_code=400,detail="Email déjà utilisé")
    mot_de_passe_hashe=hashe_mot_de_passe(user.mot_de_passe)
    nouvel_administrateur=models.Administrateur(
        nom=user.nom,
        prenom=user.prenom,
        email=user.email,
        mot_de_passe=mot_de_passe_hashe,
        role="admin"
    )        
    db.add(nouvel_administrateur)
    db.commit()
    db.refresh(nouvel_administrateur)
    return {"Message":"Compte créé avec succès "}
    
@app.post("/Zem")
async   def creer_compte_zem(user:shemas.AdminCreateZem,current_user=Depends(get_current_user),db:Session=Depends(get_db)):  
    if current_user.role != "zem":
        logger.warning(f"Accès invalide : {current_user.email}")
        raise HTTPException(status_code=403, detail="Role invalide")
    db_user=db.query(models.Zem).filter(models.Zem.email==user.email).first()
    if db_user:
        logger.warning(f"Email déjà utilisé :{user.email}")
        raise HTTPException(status_code=400,detail="Email déjà utilisé")
    mot_de_passe_hashe=hashe_mot_de_passe(user.mot_de_passe)
    nouvel_zem=models.Zem (
        nom=user.nom,
        prenom=user.prenom,
        email=user.email,
        mot_de_passe=mot_de_passe_hashe,
        type_vehicule=user.type_vehicule,
        role="zem"
        
    ) 
    db.add(nouvel_zem)
    db.commit()
    db.refresh(nouvel_zem)
    await envoyer_message(
        user.email,
        user.mot_de_passe
    )
    return {"Message":"Compte créé avec succès"}


@app.post("/connexion/{type_utilisateur}")
@limiter.limit(RATE_LIMIT)
def connexion(type_utilisateur: str, request: Request, user: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    modele = MODELES.get(type_utilisateur)
    if modele is None:
        raise HTTPException(status_code=404, detail="Type utilisateur invalide")
    db_user = db.query(modele).filter(modele.email == user.username).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="Email ou mot de passe incorrect")
    if not verifier_mot_de_passe_hashe(user.password, db_user.mot_de_passe):
        raise HTTPException(status_code=400, detail="Email ou mot de passe invalide")
    
    if type_utilisateur == "zem":
        db_user.statut = StatutZem.DISPONIBLE
        db.commit()
    
    access_token = creer_access_token({"sub": db_user.email, "role": db_user.role})
    refresh_token = creer_refresh_token({"sub": db_user.email, "role": db_user.role})
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@app.get("/zem/profil")
def mon_profil(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "zem":
        raise HTTPException(status_code=403, detail="Accès réservé aux zems")

    return {
        "nom": current_user.nom,
        "prenom": current_user.prenom,
        "email": current_user.email,
        "type_vehicule": current_user.type_vehicule,
        "statut": current_user.statut,
        "photo": current_user.photo
    }


@app.post("/zem/photo")
async def uploader_photo(
    photo: UploadFile = File(...),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "zem":
        raise HTTPException(status_code=403, detail="Accès réservé aux zems")

    extensions_autorisees = [".jpg", ".jpeg", ".png"]
    extension = os.path.splitext(photo.filename)[1].lower()
    if extension not in extensions_autorisees:
        raise HTTPException(status_code=400, detail="Format de fichier non autorisé")

    nom_fichier = f"{uuid.uuid4()}{extension}"
    chemin_fichier = f"uploads/{nom_fichier}"

    async with aiofiles.open(chemin_fichier, "wb") as fichier:
        contenu = await photo.read()
        await fichier.write(contenu)

    current_user.photo = chemin_fichier
    db.commit()

    return {"Message": "Photo mise à jour", "photo": current_user.photo}
    

@app.put("/modifier-user")
def modifier_mot_de_passe(user: shemas.ZemLogin, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    current_user.mot_de_passe = hashe_mot_de_passe(user.mot_de_passe)
    current_user.email=user.email
    db.commit()
    db.refresh(current_user)
    return {"Message": "Mot de passe modifié avec succès"}


@app.post("/mot-de-passe-oublie/{type_utilisateur}")
async def forget_password(type_utilisateur: str, user: shemas.ForgotPassword, db: Session = Depends(get_db)):
    modele = MODELES.get(type_utilisateur)
    if modele is None:
        raise HTTPException(status_code=404, detail="Type utilisateur invalide")
    db_user = db.query(modele).filter(modele.email == user.email).first()
    if db_user is None:
        raise HTTPException(status_code=400, detail="Email incorrect")
    code = generer_otp()
    db_user.otp_code = code
    db_user.otp_expiration = datetime.utcnow() + timedelta(minutes=OTP_EXPIRATION)
    db.commit()
    await envoyer_otp(db_user.email, code)
    return {"Message": "Code OTP envoyé"}
@app.post("/reset-mot-de-passe/{type_utilisateur}")
def reset_password(type_utilisateur: str, user: shemas.ResetPassword, db: Session = Depends(get_db)):
    modele = MODELES.get(type_utilisateur)
    if modele is None:
        raise HTTPException(status_code=404, detail="Type utilisateur invalide")
    db_user = db.query(modele).filter(modele.email == user.email).first()
    if db_user is None:
        raise HTTPException(status_code=400, detail="Email incorrect")
    verifier_otp(db_user, user.code)
    db_user.otp_code = None
    db_user.otp_expiration = None
    db_user.mot_de_passe = hashe_mot_de_passe(user.mot_de_passe)
    db.commit()
    return {"Message": "Mot de passe réinitialisé"}

@app.post("/Refresh")
def refesh_token_route(token: shemas.RefreshToken, db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token.refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Token invalide")

        email = payload.get("sub")
        role = payload.get("role")

        modele = MODELES.get(role)
        if modele is None:
            raise HTTPException(status_code=401, detail="Token invalide")

        db_user = db.query(modele).filter(modele.email == email).first()
        if db_user is None:
            raise HTTPException(status_code=401, detail="Token invalide")

        new_access_token = creer_access_token({"sub": email, "role": role})
        return {"access_token": new_access_token, "token_type": "bearer"}
    except JWTError:
        raise HTTPException(status_code=401, detail="Token invalide")  
    


@app.post("/client/nouveau")
def creer_client(db: Session = Depends(get_db)):
    nouveau_token = str(uuid.uuid4())
    nouveau_client = models.Client(token=nouveau_token)
    db.add(nouveau_client)
    db.commit()
    db.refresh(nouveau_client)
    return {"token": nouveau_client.token}    


@app.put("/zem/position")
def mettre_a_jour_position(position: shemas.ZemUpdate, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    current_user.latitude = position.latitude
    current_user.longitude = position.longitude
    db.commit()
    return {"Message": "Position mise à jour"}


@app.put("/zem/statut")
def modifier_statut(statut: StatutZem, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    current_user.statut = statut
    db.commit()
    return {"Message": "Statut mis à jour"}



@app.post("/lancer_commande")
def lancerCommande(user: shemas.CreateCourse, current_client=Depends(get_current_client), db: Session = Depends(get_db)):
    zem_disponible = db.query(models.Zem).filter(
        models.Zem.statut == StatutZem.DISPONIBLE,
        models.Zem.type_vehicule == user.type_vehicule
    ).all()
    
    if not zem_disponible:
        raise HTTPException(status_code=404, detail="Aucun zem n'est disponible")

    zem_le_plus_proche = None
    distance_minimale = None

    for zem in zem_disponible:
        distance = calculer_distance(user.latitude, user.longitude, zem.latitude, zem.longitude)
        if distance_minimale is None or distance < distance_minimale:
            distance_minimale = distance
            zem_le_plus_proche = zem

    distance_trajet = calculer_distance(
        user.latitude, user.longitude,
        user.destination_latitude, user.destination_longitude
    )

    prix = calculer_prix(distance_minimale, distance_trajet, user.type_vehicule)

    nouvelle_course = models.Course(
        type_vehicule=user.type_vehicule,
        destination=user.destination,
        statut=StatutCourse.EN_ATTENTE,
        prix=prix,
        client_id=current_client.id,
        zem_id=zem_le_plus_proche.id
    )

    db.add(nouvelle_course)
    zem_le_plus_proche.statut = StatutZem.OCCUPE
    db.commit()
    db.refresh(nouvelle_course)

    return {
        "Message": "Course créée",
        "Nom": zem_le_plus_proche.nom,
        "course_id": nouvelle_course.id,
        "prix": nouvelle_course.prix
    }
@app.put("/course/{course_id}/annuler")
def annuler_course(course_id: int, current_client=Depends(get_current_client), db: Session = Depends(get_db)):
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    
    if course is None:
        raise HTTPException(status_code=404, detail="Course introuvable")
    
    if course.client_id != current_client.id:
        raise HTTPException(status_code=403, detail="Vous n'êtes pas autorisé à annuler cette course")
    
    if course.statut == StatutCourse.TERMINE:
        raise HTTPException(status_code=400, detail="Cette course est déjà terminée")
    
    zem = db.query(models.Zem).filter(models.Zem.id == course.zem_id).first()
    if zem is not None:
        zem.statut = StatutZem.DISPONIBLE
    
    course.statut = StatutCourse.ANNULE
    db.commit()
    
    return {"Message": "Course annulée avec succès"}

@app.put("/course/{course_id}/confirmer")
def confirmer_course(course_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    course = db.query(models.Course).filter(models.Course.id == course_id).first()

    if course is None:
        raise HTTPException(status_code=404, detail="Course introuvable")

    if course.zem_id != current_user.id:
        raise HTTPException(status_code=403, detail="Vous n'êtes pas autorisé à confirmer cette course")

    if course.statut != StatutCourse.EN_ATTENTE:
        raise HTTPException(status_code=400, detail="Cette course n'est plus en attente")

    course.statut = StatutCourse.EN_COURSE
    db.commit()

    return {"Message": "Course confirmée, trajet en cours"}

@app.put("/course/{course_id}/terminer")
def terminer_course(course_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    course = db.query(models.Course).filter(models.Course.id == course_id).first()

    if course is None:
        raise HTTPException(status_code=404, detail="Course introuvable")

    if course.zem_id != current_user.id:
        raise HTTPException(status_code=403, detail="Vous n'êtes pas autorisé à terminer cette course")

    if course.statut != StatutCourse.EN_COURSE:
        raise HTTPException(status_code=400, detail="Cette course n'est pas en cours")

    course.statut = StatutCourse.TERMINE
    current_user.statut = StatutZem.DISPONIBLE
    db.commit()

    return {"Message": "Course terminée avec succès"}


@app.websocket("/ws/course/{course_id}")
async def chat_websocket(websocket: WebSocket, course_id: int, db: Session = Depends(get_db)):
    await websocket.accept()

    # Authentification (premier message)
    premier_message = await websocket.receive_json()
    x_client_token = premier_message.get("x_client_token")
    token = premier_message.get("token")

    expediteur = None
    if x_client_token:
        client = db.query(models.Client).filter(models.Client.token == x_client_token).first()
        if client:
            expediteur = {"type": "client", "id": client.id}
    elif token:
        try:
            payload = verifier_token(token)
            modele = MODELES.get(payload["role"])
            db_user = db.query(modele).filter(modele.email == payload["email"]).first()
            if db_user:
                expediteur = {"type": payload["role"], "id": db_user.id}
        except Exception:
            pass

    if expediteur is None:
        await websocket.close(code=1008)
        return

    # Autorisation
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if course is None:
        await websocket.close(code=1008)
        return

    if expediteur["type"] == "client" and expediteur["id"] != course.client_id:
        await websocket.close(code=1008)
        return
    if expediteur["type"] == "zem" and expediteur["id"] != course.zem_id:
        await websocket.close(code=1008)
        return

    # Enregistrement de la connexion
    if course_id not in connexions_actives:
        connexions_actives[course_id] = {}
    connexions_actives[course_id][expediteur["type"]] = websocket

    # Boucle de discussion
    try:
        while True:
            course_actuelle = db.query(models.Course).filter(models.Course.id == course_id).first()
            if course_actuelle.statut not in [StatutCourse.EN_ATTENTE, StatutCourse.EN_COURSE]:
                await websocket.close(code=1000)
                return

            data = await websocket.receive_json()
            contenu = data.get("contenu")
            if not contenu:
                continue

            destinataire_type = "zem" if expediteur["type"] == "client" else "client"
            destinataire_ws = connexions_actives.get(course_id, {}).get(destinataire_type)
            if destinataire_ws:
                await destinataire_ws.send_json({
                    "expediteur": expediteur["type"],
                    "contenu": contenu
                })

    except WebSocketDisconnect:
        if course_id in connexions_actives and expediteur["type"] in connexions_actives[course_id]:
            del connexions_actives[course_id][expediteur["type"]]
    
    
       
    
    
        
        
        

    
    
    
    
    
    
    
    

