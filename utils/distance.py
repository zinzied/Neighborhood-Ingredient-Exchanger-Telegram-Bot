import math

def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the distance between two points on Earth using the Haversine formula.
    
    Parameters:
    - lat1, lon1: Latitude and longitude of the first point (in degrees)
    - lat2, lon2: Latitude and longitude of the second point (in degrees)
    
    Returns:
    - Distance between the points in kilometers
    """
    # Convert latitude and longitude from degrees to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Radius of Earth in kilometers
    earth_radius = 6371.0
    
    # Haversine formula
    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distance = earth_radius * c
    
    return distance

def get_nearby_coordinates(lat, lon, distance_km):
    """
    Get a bounding box of coordinates at a specified distance from a point.
    
    Parameters:
    - lat, lon: Latitude and longitude of the center point (in degrees)
    - distance_km: Distance from the center in kilometers
    
    Returns:
    - Dictionary with min and max latitude and longitude
    """
    # Approximate degrees per kilometer
    km_per_degree_lat = 111.0  # At the equator
    km_per_degree_lon = 111.0 * math.cos(math.radians(lat))
    
    # Calculate the offsets
    lat_offset = distance_km / km_per_degree_lat
    lon_offset = distance_km / km_per_degree_lon
    
    return {
        'min_lat': lat - lat_offset,
        'max_lat': lat + lat_offset,
        'min_lon': lon - lon_offset,
        'max_lon': lon + lon_offset
    }