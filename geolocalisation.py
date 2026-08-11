from math import radians, sin, cos, sqrt, atan2

def calculer_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    RAYON_TERRE_KM = 6371

    lat1_rad = radians(lat1)
    lon1_rad = radians(lon1)
    lat2_rad = radians(lat2)
    lon2_rad = radians(lon2)

    delta_lat = lat2_rad - lat1_rad
    delta_lon = lon2_rad - lon1_rad

    a = sin(delta_lat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = RAYON_TERRE_KM * c
    return distance