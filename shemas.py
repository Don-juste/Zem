from pydantic import BaseModel,Field,field_validator
from enums import TypeVehicule,StatutCourse,StatutZem
from datetime import datetime
from typing import Optional
import re
#Administrateur
class AdminCreate(BaseModel):
    nom:str=Field(min_length=3,max_length=50)
    prenom:str=Field(min_length=3,max_length=50)
    email:str
    mot_de_passe:str=Field(min_length=8)
    
    @field_validator("nom")
    def valider_nom(cls,nom):
        if not re.search(r"^[A-Z][A-Z]+$",nom):
            raise ValueError("Nom invalide")
        return nom
    @field_validator("prenom")
    def valider_prenom(cls,prenom):
        if not re.search(r"^[A-Z][a-z]+$",prenom):
            raise ValueError("Prenom invalide")
        return prenom
    @field_validator("mot_de_passe")
    def valider_mot_de_passe(cls,mot_de_passe):
        if not re.search(r"^(?=.*[A-Z])(?=.*\d)(?=.*[@#!]).{8,}$",mot_de_passe):
            raise ValueError("Mot de passe inavlide")
        return mot_de_passe
    @field_validator("email")
    def valider_email(cls,email):
        if not re.search(r"^[a-z][a-z]+\d*@\d*[a-z]+\.[a-z]{2,}$",email):
            raise ValueError("Email invalide")
        return email
class AdminLogin(BaseModel):
    email:str
    mot_de_passe:str

class AdminResponse(BaseModel):
    id:int
    nom:str
    prenom:str
    email:str
    class Config:
        from_attributes=True
        
class AdminCreateZem(BaseModel):
    nom:str=Field(min_length=3,max_length=50)
    prenom:str=Field(min_length=3,max_length=50)
    email:str
    mot_de_passe:str=Field(min_length=8)
    type_vehicule:TypeVehicule
    
 
    @field_validator("nom")
    def valider_nom(cls,nom):
        if not re.search(r"^[A-Z][A-Z]+$",nom):
            raise ValueError("Nom invalide")
        return nom
    @field_validator("prenom")
    def valider_prenom(cls,prenom):
        if not re.search(r"^[A-Z][a-z]+$",prenom):
            raise ValueError("Prenom invalide")
        return prenom
    @field_validator("mot_de_passe")
    def valider_mot_de_passe(cls,mot_de_passe):
        if not re.search(r"^(?=.*[A-Z])(?=.*\d)(?=.*[@#!]).{8,}$",mot_de_passe):
            raise ValueError("Mot de passe inavlide")
        return mot_de_passe   
    @field_validator("email")
    def valider_email(cls,email):
        if not re.search(r"^[a-z][a-z]+\d*@\d*[a-z]+\.[a-z]{2,}$",email):
            raise ValueError("Email invalide")
        return email   
#Zem    
class ZemLogin(BaseModel):
    email:str
    mot_de_passe:str

class ZemUpdate(BaseModel):
    longitude:float
    latitude:float
    
class ZemResponse(BaseModel):
    id:int
    nom:str
    prenom:str
    email:str
    type_vehicule:TypeVehicule
    statut:StatutZem
    class config:
        from_attributes=True

#Course
class CreateCourse(BaseModel):
    type_vehicule: TypeVehicule
    destination: str
    latitude: float
    longitude: float
    destination_latitude: float
    destination_longitude: float
    
    
class CourseUpdate(BaseModel):
    statut:StatutCourse  
    zem_id:Optional[int]=None   

class CourseResponse(BaseModel):
    id:int
    type_vehicule:TypeVehicule
    destination:str
    statut:StatutCourse
    date_heure:datetime
    client_id:int
    zem_id:Optional[int]=None
    class Config:
        from_attributes=True
    

    
 
class ResponseClient(BaseModel):
    id:int
    token:str   
    class Config:
        from_attributes=True   

class OTPshema(BaseModel):
    code:str
    email:str

class RefreshToken(BaseModel):
    refresh_token:str

class ForgotPassword(BaseModel):
    email:str

class FCMToken(BaseModel):
    fcm_token:str    

class ResetPassword(BaseModel):
    email:str
    code:str
    mot_de_passe:str   
    @field_validator("mot_de_passe")
    def valider_mot_de_passe(cls,mot_de_passe):
        if not re.search(r"^(?=.*[A-Z])(?=.*\d)(?=.*[@#!]).{8,}$",mot_de_passe):
            raise  ValueError("Mot de passe inavlide")
        return mot_de_passe                   

    
    
        
            

                    