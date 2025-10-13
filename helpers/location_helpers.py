import requests
import math
from typing import Dict, List, Tuple, Optional, Any, Union


def parse_direct_coordinates(location: str) -> Tuple[bool, Optional[float], Optional[float]]:
    """
    Attempt to parse the location string as direct coordinates.
    
    Args:
        location: A string that might contain lat, lon coordinates
        
    Returns:
        A tuple of (is_coordinates, lat, lon) where is_coordinates is a boolean
        indicating if parsing was successful, and lat/lon are the parsed coordinates
        or None if parsing failed
    """
    if ',' not in location:
        return False, None, None
        
    try:
        # Strip any spaces and split by comma
        parts = [part.strip() for part in location.split(',')]
        
        if len(parts) == 2:
            # Try to convert both parts to floats
            possible_lat = float(parts[0])
            possible_lon = float(parts[1])
            
            # Check if values are in valid ranges for lat/lon
            if -90 <= possible_lat <= 90 and -180 <= possible_lon <= 180:
                print(f"DEBUG: Parsed direct coordinates: lat={possible_lat}, lon={possible_lon}")
                return True, possible_lat, possible_lon
    except ValueError:
        pass
        
    return False, None, None


def is_potential_intersection(location: str) -> bool:
    """
    Check if a location string might represent a street intersection.
    """
    intersection_keywords = [" and ", " & ", " at ", " intersection "]
    return any(keyword in location.lower() for keyword in intersection_keywords)


def geocode_location(location: str) -> List[Dict[str, Any]]:
    """
    Geocode a location string using Nominatim.
    
    Args:
        location: The location string to geocode
        
    Returns:
        A list of geocoding results, each as a dictionary
    """
    # Use Nominatim API for geocoding (OpenStreetMap's geocoding service)
    geocoding_url = "https://nominatim.openstreetmap.org/search"
    
    # Parameters for the geocoding request
    params = {
        "q": location,
        "format": "json",
        "limit": 5,  # Get more results to handle ambiguous cases
        "addressdetails": 1,  # Get address details for better filtering
        "extratags": 1  # Get extra tags that might help identify intersections
    }
    
    # Add user-agent header as required by Nominatim usage policy
    headers = {
        "User-Agent": "MCP-Tool/1.0"
    }
    
    # Make the geocoding request
    response = requests.get(geocoding_url, params=params, headers=headers, timeout=30)
    response.raise_for_status()  # Raise exception for HTTP errors
    
    return response.json()


def try_alternate_intersection_format(location: str) -> List[Dict[str, Any]]:
    """
    Try an alternate format for intersection queries if the initial query fails.
    
    Args:
        location: The location string to geocode
        
    Returns:
        A list of geocoding results
    """
    processed_location = location
    
    # Replace "and" with "&" or vice versa
    if " and " in processed_location.lower():
        processed_location = processed_location.lower().replace(" and ", " & ")
    elif " & " in processed_location.lower():
        processed_location = processed_location.lower().replace(" & ", " and ")
        
    print(f"DEBUG: Retrying with modified intersection query: {processed_location}")
    return geocode_location(processed_location)


def select_best_geocoding_result(data: List[Dict[str, Any]], is_intersection: bool) -> Dict[str, Any]:
    """
    Select the best result from a list of geocoding results.
    
    Args:
        data: List of geocoding results
        is_intersection: Whether to prioritize results that look like intersections
        
    Returns:
        The selected result as a dictionary
    """
    if not data:
        raise ValueError("No geocoding results to select from")
        
    selected_result = None
    
    # If it's a potential intersection, prioritize results with "highway" in the type
    if is_intersection:
        for item in data:
            if "type" in item and "highway" in item["type"].lower():
                selected_result = item
                break
                
            # Also check the class field
            if "class" in item and item["class"] == "highway":
                selected_result = item
                break
    
    # If no suitable intersection found, or not looking for intersection, use the highest-ranked result
    if not selected_result:
        selected_result = data[0]
        
    print(f"DEBUG: Selected location: {selected_result.get('display_name', 'Unknown')}")
    return selected_result


def calculate_bounding_box(lat: float, lon: float, box_size_meters: float) -> List[float]:
    """
    Calculate a bounding box around a point.
    
    Args:
        lat: Latitude of the center point
        lon: Longitude of the center point
        box_size_meters: Size of the bounding box in meters
    """
    # Convert box_size_meters to approximate degrees
    # This is a rough approximation - at the equator, 1 degree is about 111,320 meters
    # Longitude degrees vary with latitude, so we adjust for that
    lat_offset = box_size_meters / 111320  # Roughly meters to degrees for latitude
    lon_offset = box_size_meters / (111320 * abs(math.cos(math.radians(lat))))  # Adjust for latitude
    
    # Create the bounding box (min_lon, min_lat, max_lon, max_lat)
    return [
        lon - lon_offset,  # min_lon
        lat - lat_offset,  # min_lat
        lon + lon_offset,  # max_lon
        lat + lat_offset   # max_lat
    ]


def generate_overpass_url(bbox: List[float]) -> str:
    return f"https://overpass-api.de/api/map?bbox={bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}"


def location_to_coordinates(location: str, box_size_meters: float = 100) -> str:
    """
    Convert a human-readable location to an Overpass API URL with a bounding box.
    
    Supports various location formats including:
    - Addresses: "123 Main St, City, Country"
    - Points of interest: "Borough Market, London"
    - Intersections: "23rd Street and 8th Avenue, Manhattan, New York"
    - Coordinates: "40.732547796756386, -73.98050772789479"
    
    Args:
        location: Human-readable location name or coordinates
        box_size_meters: Size of the bounding box in meters (default: 100)
        
    Returns:
        Overpass API URL with a bounding box
    """
    try:
        # First, try to parse as direct coordinates
        is_coordinates, lat, lon = parse_direct_coordinates(location)
        
        if not is_coordinates:
            # Check if this might be an intersection
            intersection_check = is_potential_intersection(location)
            
            if intersection_check:
                print(f"DEBUG: Processing as potential intersection: {location}")
                
            # Try to geocode the location
            geocode_results = geocode_location(location)
            
            # If no results and it might be an intersection, try an alternative format
            if not geocode_results and intersection_check:
                geocode_results = try_alternate_intersection_format(location)
                
            # If still no results, return an error
            if not geocode_results:
                return f"Error: Location '{location}' not found"
                
            # Select the best result from the geocoding response
            selected_result = select_best_geocoding_result(geocode_results, intersection_check)
            
            # Extract lat/lon from the selected result
            lat = float(selected_result["lat"])
            lon = float(selected_result["lon"])
        
        # Calculate the bounding box
        bbox = calculate_bounding_box(lat, lon, box_size_meters)
        
        # Generate and return the Overpass API URL
        return generate_overpass_url(bbox)
        
    except requests.exceptions.Timeout:
        return "Error: Geocoding API request timed out"
    except requests.exceptions.RequestException as e:
        return f"Error: Network error when geocoding location: {str(e)}"
    except ValueError as e:
        return f"Error: Invalid location format: {str(e)}"
    except IndexError:
        return f"Error: Could not extract coordinates from location '{location}'"
    except Exception as e:
        return f"Error: {str(e)}"


# Async version of the function
async def location_to_coordinates_async(location: str, box_size_meters: float = 100) -> str:
    """
    Async version of location_to_coordinates.
    Convert a human-readable location to an Overpass API URL with a bounding box.
    
    Supports various location formats including:
    - Addresses: "123 Main St, City, Country"
    - Points of interest: "Borough Market, London"
    - Intersections: "23rd Street and 8th Avenue, Manhattan, New York"
    - Coordinates: "40.732547796756386, -73.98050772789479"
    
    Args:
        location: Human-readable location name or coordinates
        box_size_meters: Size of the bounding box in meters (default: 100)
        
    Returns:
        Overpass API URL with a bounding box
    """
    # For now, this just calls the synchronous version
    # In the future, this could be updated to use aiohttp or similar for async requests
    return location_to_coordinates(location, box_size_meters)
