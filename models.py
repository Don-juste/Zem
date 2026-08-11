from sqlalchemy import Column,Integer,Float,String,ForeignKey,Enum
from enums import TypeVehicule,StatutCourse,StatutZem
from sqlalchemy import DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base
class Client(Base):
    __tablename__="clients"
    id=Column(Integer,primary_key=True,index=True)
    token=Column(String,unique=True,index=True)
    course=relationship("Course",back_populates="client")

class Zem(Base):
    __tablename__="zems"
    id=Column(Integer,primary_key=True,index=True)
    nom=Column(String)
    prenom=Column(String)
    email=Column(String,unique=True,index=True)
    mot_de_passe=Column(String)
    type_vehicule=Column(Enum(TypeVehicule))
    statut=Column(Enum(StatutZem),default=StatutZem.HORS_LIGNE)
    role=Column(String,default="Zem")
    otp_code=Column(String,nullable=True)
    otp_expiration=Column(DateTime,nullable=True)
    longitude=Column(Float,nullable=True)
    latitude=Column(Float,nullable=True)
    cours=relationship("Course",back_populates="zem")

class Course(Base):
    __tablename__="courses"
    id=Column(Integer,primary_key=True,index=True)
    type_vehicule=Column(Enum(TypeVehicule))
    destination=Column(String)    
    statut=Column(Enum(StatutCourse))
    prix=Column(Float)
    date_heure=Column(DateTime,default=func.now())
    client_id=Column(Integer,ForeignKey("clients.id"))
    zem_id=Column(Integer,ForeignKey("zems.id"))
    zem=relationship("Zem",back_populates="cours")
    client=relationship("Client",back_populates="course")

class Administrateur(Base):
    __tablename__= "admin"
    id=Column(Integer,primary_key=True,index=True)
    nom=Column(String)
    prenom=Column(String)
    email=Column(String,unique=True,index=True)
    mot_de_passe=Column(String)
    role=Column(String,default="admin")
    otp_code=Column(String,nullable=True)
    otp_expiration=Column(DateTime,nullable=True)
        
        
    
        