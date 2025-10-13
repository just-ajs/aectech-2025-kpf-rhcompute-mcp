#!/usr/bin/env python3
"""
Simple MCP Server with FastMCP
Provides tools: simple math operations, weather lookup, and Rhino.Compute Grasshopper execution.
"""

import os
import sys
import requests
import json
import math
from typing import Literal, Dict, Any, List, Optional, Union
from fastmcp import FastMCP
from dotenv import load_dotenv
from helpers.context_gen_helpers import parse_result
from helpers.compute_helpers import run_rhino_compute, format_parameter, format_parameters
from helpers.location_helpers import location_to_coordinates
from helpers.rhino_helpers import read_3dm_file, get_layers, get_geometry_by_layer, format_layer_info, encode_geometry
from helpers.compute_rhino3dm_helpers import add_parameter, decode_gh_output, save_3dm_file
import compute_rhino3d.Grasshopper as gh
import rhino3dm


# Load environment variables
load_dotenv()

# Create FastMCP server instance
mcp = FastMCP("Alex First MCP Server")

@mcp.tool()
def get_weather(city: str, country: str = "US") -> str:
    """
    Get current weather information for a specified city and country.
    
    Args:
        city: Name of the city
        country: Country name or country code (default: US)
        
    Returns:
        String containing weather information
    """
    try:
        # Use OpenWeatherMap API (requires API key)
        api_key = os.getenv("OPENWEATHER_API_KEY")
        
        if not api_key:
            # If no API key, return mock data
            return f"Mock Weather Data for {city}, {country}: Temperature: 22°C, Conditions: Partly Cloudy, Humidity: 65%. (Note: Set OPENWEATHER_API_KEY environment variable for real data)"
        
        # Construct API URL
        base_url = "http://api.openweathermap.org/data/2.5/weather"
        params = {
            "q": f"{city},{country}",
            "appid": api_key,
            "units": "metric"
        }
        
        # Make API request
        response = requests.get(base_url, params=params, timeout=600)
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract weather information
            temp = data["main"]["temp"]
            description = data["weather"][0]["description"].title()
            humidity = data["main"]["humidity"]
            feels_like = data["main"]["feels_like"]
            
            return f"Weather in {city}, {country}: {temp}°C (feels like {feels_like}°C), {description}, Humidity: {humidity}%"
            
        elif response.status_code == 404:
            return f"Error: City '{city}' in '{country}' not found"
        else:
            return f"Error: Unable to fetch weather data (HTTP {response.status_code})"
            
    except requests.exceptions.Timeout:
        return "Error: Weather API request timed out"
    except requests.exceptions.RequestException as e:
        return f"Error: Network error when fetching weather data: {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
def run_grasshopper_definition(
    definition_path: str,
    parameters: List[Dict[str, Any]],
    compute_url: str = "http://localhost:6001"
) -> str:
    """
    Run a Grasshopper definition via Rhino.Compute.
    
    Args:
        definition_path: Path to the Grasshopper definition file (.gh)
        parameters: List of parameter objects with ParamName and InnerTree
        compute_url: Rhino.Compute server URL (default: http://localhost:6001)
        
    Returns:
        String containing the result from Rhino.Compute
    """
    try:
        result = run_rhino_compute(
            definition_path=definition_path,
            parameters=parameters,
            compute_url=compute_url)

        return f"Grasshopper definition executed successfully. Result: {json.dumps(result, indent=2)}"
    
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
def run_simple_grasshopper_math(
    param_a: int,
    param_b: int,
    compute_url: str = "http://localhost:6001"
) -> str:
    """
    Simplified tool to run a Grasshopper math definition with two numeric parameters.
    
    Args:
        param_a: First numeric parameter (parameter name 'a')
        param_b: Second numeric parameter (parameter name 'b')
        compute_url: Rhino.Compute server URL (default: http://localhost:6001)
        
    Returns:
        String containing the result from the math operation
    """
    try:

        a = add_parameter("a", param_a)
        b = add_parameter("b", param_b)

        gh_inputs = [a, b]

        definition_path = "c:/Users/jszychowska/Desktop/compute/add.gh"

        output = gh.EvaluateDefinition(definition_path, gh_inputs)

        # Determine if we should use Int32 or Double based on whether values are whole numbers
        # parameters = format_parameters({
        #     'a': param_a,
        #     'b': param_b
        # })

        print (output)
        

        result = decode_gh_output(output)

        print(result)

        # response = run_rhino_compute(
        #     definition_path=definition_path,
        #     parameters=parameters,
        #     compute_url=compute_url)
        
        # result = response
        return f"Grasshopper definition executed successfully. Result: {result[0]}"
        #return f"Grasshopper definition executed successfully. Result: {json.dumps(result, indent=2)}"
    
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
def run_context_generator(
    location: str,
    compute_url: str = "http://localhost:6001",
    box_size_meters: float = 100
) -> Dict[str, Any]:
    """
    Run the Context Generator for a given location.

    Args:
        location: Human-readable location name (e.g., "Borough Market, London")
        compute_url: Rhino.Compute server URL (default: http://localhost:6001)

    Returns:
        Dictionary containing the result from the context generation
    """
    try:
        print(f"DEBUG: Starting context generator for location: {location}")
        overpass_url = location_to_coordinates(location, box_size_meters)

        # Path to the Grasshopper definition
        definition_path = "c:/Users/jszychowska/Desktop/compute/Context_Generator_RH.gh"

        # Prepare parameters for the Grasshopper script
        parameters = [format_parameter("osmURL", overpass_url)]

        response = run_rhino_compute(
            definition_path=definition_path,
            parameters=parameters,
            compute_url=compute_url)
        
        result = response
        
        # Process response as long as it contains values, regardless of status code
        if "values" in result:
            try:
                byte_array = parse_result(result)
                
                # Save to user's Downloads folder as context_model.3dm
                downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
                file_path = os.path.join(downloads_path, "context_model.3dm")
                
                # Write the decoded bytes directly to file
                with open(file_path, "wb") as f:
                    f.write(byte_array)
                
                print(f"Saved Rhino file to: {file_path}")
                
                return {
                    "success": True,
                    "download_path": downloads_path,
                    "location": location
                }
                    
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Error processing response data: {str(e)}"
                }
        else:
            # No values in response
            return {
                "success": False,
                "error": "No values found in Rhino.Compute response"
            }

    except Exception as e:
        return {
            "success": False,
            "error": f"Error: {str(e)}"
        }


@mcp.tool()
def location_to_coordinates_tool(location: str, box_size_meters: float = 100) -> str:
    """
    Convert a human-readable location to an Overpass API URL with a bounding box.
    
    Args:
        location: Human-readable location name (e.g., "Borough Market, London")
        box_size_meters: Size of the bounding box in meters (default: 100)
        
    Returns:
        Overpass API URL with a bounding box
    """

    return location_to_coordinates(location, box_size_meters)


@mcp.tool()
def read_rhino_layers(path: str) -> str:
    """
    Read and list all layers from a Rhino 3dm file, including geometry information.
    
    Args:
        path: Path to the Rhino 3dm file
        
    Returns:
        String containing information about layers and their geometry in the Rhino file
    """
    try:
        model = read_3dm_file(path)
        if model is None:
            return f"Error: Could not read file at '{path}'. Make sure it is a valid Rhino 3dm file."
        
        layer_info = get_layers(model)
        geometry_info = get_geometry_by_layer(model)
        print(geometry_info)

        objects = model.Objects
        print(f'Objects: {objects}')
        
        # for object in objects:
        #     print(f'geometry: {object.Geometry}')
        #     encoded = encode_geometry(object.Geometry)
        #     print(f'encoded geometry: {encoded}')
        
        # geo = encode_geometry(objects[0].Geometry)
        geo = objects[0].Geometry
        print(geo)

        geo_coded = geo.Encode()
        geo_coded_string = json.dumps(geo_coded)
        # print(f'encoded geometry: {geo_coded_string}')

        geo_input = add_parameter("surface", geo_coded_string)

        # print(f'geo input: {geo_input}')
        gh_inputs = [geo_input]

        
        definition_path = "C:/Users/jszychowska/Desktop/compute/extrude_srf.gh"

        output = gh.EvaluateDefinition(definition_path, gh_inputs)

        js = json.dumps(output, indent=2)
        print(js)

        geo_compute = decode_gh_output(output, tree_path='{0}')

        print(f'geo from compute: {geo_compute}')
        filename = 'test.3dm'
        save_3dm_file(geo_compute, filename)

        # output_shape = decode_gh_output(output)
        # filename = 'result.3dm'
        # print('Writing {} lines to {}'.format(len(output_shape), filename))

        # save_3dm_file(output_shape, filename)


        return format_layer_info(layer_info, geometry_info, os.path.basename(path))
        
    except Exception as e:
        return f"Error reading layers: {str(e)}"


if __name__ == "__main__":
    # FastMCP automatically detects transport mode
    # - When run normally: uses HTTP
    # - When run with stdio: uses stdio
    # - When run with SSE: uses Server-Sent Events
    
    if "--stdio" in sys.argv:
        # Force stdio mode for Claude Desktop
        mcp.run(transport="stdio")
    else:
        # Default to HTTP for MCP Inspector and manual testing
        mcp.run(
            transport="http",
            host="0.0.0.0",  # Bind to all interfaces for external access
            port=8000,       # HTTP port
            log_level="INFO" # Set logging level
        )