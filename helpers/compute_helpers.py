import requests
from typing import Dict, Any, List

def run_rhino_compute(
        definition_path: str,
        parameters: List[Dict[str, Any]],
        compute_url: str = "http://localhost:6001"
) -> Dict[str, Any]:    
    """
    Generic function to run a Grasshopper definition via Rhino.Compute.
    
    Args:
        definition_path: Path to the Grasshopper definition file (.gh)
        parameters: List of parameter objects with ParamName and InnerTree
        compute_url: Rhino.Compute server URL (default: http://localhost:6001)
        
    Returns:
        Dictionary containing the result from Rhino.Compute
    """
    # Construct the request payload
    payload = {
        "algo": None,
        "pointer": definition_path,
        "values": parameters
    }
    
    # Make POST request to Rhino.Compute
    url = f"{compute_url.rstrip('/')}/grasshopper"
    headers = {"Content-Type": "application/json"}

    print(f"DEBUG: Using definition path: {definition_path}")
    print(f"DEBUG: Using compute URL: {compute_url}")
    
    response = requests.post(
        url, 
        json=payload, 
        headers=headers,
        timeout=3000
    )
    print(f"DEBUG: Response status: {response.status_code}")
    
    # Try to parse the response as JSON even if status code is not 200
    try:
        json_response = response.json()
        
        # Special case for status code 500 with valid data - just process it
        if response.status_code == 500 and "values" in json_response:
            print(f"WARNING: Got status 500 but response contains data. Processing anyway.")
            return json_response
        
        # For other error codes, raise exception
        if response.status_code != 200:
            raise ValueError(f"Rhino.Compute returned status {response.status_code}: {response.text}")
        
        # Return the parsed JSON for 200 responses
        return json_response
        
    except Exception as e:
        # Any parsing error
        raise ValueError(f"Failed to process response: {str(e)}")

def format_parameter(
    param_name: str, 
    value: Any
) -> Dict[str, Any]:
    """
    Format a single parameter for Grasshopper.
    
    Args:
        param_name: Name of the parameter in Grasshopper
        value: The parameter value
        
    Returns:
        Dictionary containing the formatted parameter
    """
    # Determine .NET type based on the Python type
    if isinstance(value, str):
        net_type = "System.String"
    elif isinstance(value, bool):
        net_type = "System.Boolean"
    elif isinstance(value, int):
        net_type = "System.Int32"
    elif isinstance(value, float):
        # Check if float is actually an integer value
        if value == int(value):
            net_type = "System.Int32"
            value = int(value)
        else:
            net_type = "System.Double"
    else:
        # Default to string representation for other types
        net_type = "System.String"
        value = str(value)
    
    # Return the formatted parameter
    return {
        "ParamName": param_name,
        "InnerTree": {
            "{0}": [
                {
                    "type": net_type,
                    "data": value
                }
            ]
        }
    }

def format_parameters(param_dict: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Format multiple parameters for Grasshopper from a dictionary.
    """
    return [format_parameter(name, value) for name, value in param_dict.items()]