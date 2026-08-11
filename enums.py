from enum import Enum
class TypeVehicule(str,Enum):
    MOTO = "MOTO"
    VOITURE = "VOITURE"
    TRICYCLE = "TRICYCLE"

class StatutZem(str,Enum):
    DISPONIBLE = "DISPONIBLE"
    OCCUPE = "OCCUPE"
    HORS_LIGNE = "HORS_LIGNE"    

class StatutCourse(str, Enum):
    EN_ATTENTE = "EN_ATTENTE"
    EN_COURSE = "EN_COURSE"
    ANNULE = "ANNULE"
    TERMINE = "TERMINE"    