TARIFS = {
    "MOTO": {"base": 200, "par_km": 100},
    "VOITURE": {"base": 500, "par_km": 200},
    "TRICYCLE": {"base": 300, "par_km": 150}
}

def calculer_prix(distance_approche: float, distance_trajet: float, type_vehicule: str) -> float:
    tarif = TARIFS.get(type_vehicule)
    if tarif is None:
        raise ValueError("Type de véhicule inconnu")
    distance_totale = distance_approche + distance_trajet
    prix = tarif["base"] + (distance_totale * tarif["par_km"])
    return round(prix, 0)