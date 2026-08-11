from datetime import datetime,timedelta
from fastapi import HTTPException
from jose import jwt,JWTError
from passlib.context import CryptContext
import random
from dotenv import load_dotenv
load_dotenv()
import os
SECRET_KEY=os.getenv("SECRET_KEY")
ALGORITHM=os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRATION=int(os.getenv("ACCESS_TOKEN_EXPIRATION"))
REFRESH_TOKEN_EXPIRATION=int(os.getenv("REFRESH_TOKEN_EXPIRATION"))

pwd_context=CryptContext(schemes=["bcrypt"])
def hashe_mot_de_passe(mot_de_passe:str):
    return pwd_context.hash(mot_de_passe)
def verifier_mot_de_passe_hashe(mot_de_passe:str,mot_de_passe_hashe:str):
    return pwd_context.verify(mot_de_passe,mot_de_passe_hashe)
def generer_otp():
    return str(random.randint(100000,999999))
def  verifier_otp(user,code:str):
    if user.otp_code!=code:
        raise HTTPException(status_code=401,detail="Code Incorrect")
    if datetime.utcnow() > user.otp_expiration:
        raise HTTPException(status_code=401,detail="Code expiré")
    return True
def creer_access_token(data:dict):
    datacopy=data.copy()
    expiration=datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRATION)
    datacopy.update({"exp":expiration,"type":"access"})
    token=jwt.encode(datacopy,SECRET_KEY,algorithm=ALGORITHM)
    return token

def creer_refresh_token(data:dict):
    datacopy=data.copy()
    expiration=datetime.utcnow() + timedelta(minutes=REFRESH_TOKEN_EXPIRATION)
    datacopy.update({"exp":expiration,"type":"refresh"})
    token=jwt.encode(datacopy,SECRET_KEY,algorithm=ALGORITHM)
    return token

def verifier_token(token:str):
    try:
        payload=jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])
        if payload.get("type")!="access":
            raise HTTPException(status_code=401,detail="Token invalide")
        email=payload.get("sub")
        role=payload.get("role")
        if email is None or role is None:
            raise HTTPException(status_code=401,detail="Token invalide")
        return {"email": email, "role": role}
    except JWTError:
        raise HTTPException(status_code=401,detail="Token invalide")

