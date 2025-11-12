"""
Simple MCP Server with FastMCP
Provides tools to connect with Rhino.Compute
"""

import os
import requests
import json
from fastmcp import FastMCP, Context
from pydantic import BaseModel, Field
import rhino3dm
import compute_rhino3d.Grasshopper as gh
import compute_rhino3d.Util

from helpers.helpers import add_parameter, decode_gh_output, save_3dm_file, create_file_path, resolve_path
# Create FastMCP server instance
mcp = FastMCP("Simple MCP with Rhino.Compute")

RHINO_COMPUTE_URL = "http://localhost:6500/"
compute_rhino3d.Util.url = RHINO_COMPUTE_URL

# compute_rhino3d.Util.apiKey = "..."
# compute_rhino3d.Util.AuthToken = "..."

###############################################################
## T O O L S
###############################################################

@mcp.tool
def get_rhinocompute_version_details() -> dict:
    """
    Retrieves version information from the connected Rhino.Compute server.

    Use this tool when you need to verify that Rhino.Compute is running,
    check compatibility, or confirm the Rhino/Compute build before running
    Grasshopper definitions.

    Args:
        None

    Returns:
        dict: {
            "status": "success",
            "version_info": {...}
        }
        or {"error": "..."}
    """
    url = f"{RHINO_COMPUTE_URL}version"

    try:
        response = requests.get(url, timeout=5)
        response_data = {
            "status": "success",
            "version_info": response.json()
        }
        return response_data

    except Exception as e:
        response_data = {"error": f"Failed to contact Rhino.Compute: {str(e)}"}
        return response_data


@mcp.tool
def get_installed_rhino_plugins() -> dict:
    """
    Returns a list of Rhino plugins installed on the Rhino.Compute server.

    Use this tool when checking server capabilities, diagnosing missing plugins,
    or validating that a Grasshopper or Rhino workflow will run correctly.

    Args:
        None

    Returns:
        dict: {
            "status": "success",
            "plugins": [...]
        }
        or {"error": "..."}
    """
    url = f"{RHINO_COMPUTE_URL}plugins/rhino/installed"

    try:
        response = requests.get(url, timeout=5)
        response_data = {
            "status": "success",
            "plugins": response.json()
        }
        return response_data

    except Exception as e:
        response_data = {"error": f"Failed to contact Rhino.Compute: {str(e)}"}
        return response_data

### EXERCISE 1 ###
# Add a new tool that checks which Grasshopper plugins are installed

##################

@mcp.tool
def read_grasshopper_inputs_outputs(pointer: str) -> dict:
    """
    Reads the inputs and outputs of a Grasshopper definition using Rhino.Compute's /io endpoint.

    Use this tool when you want to understand what parameters a .gh/.ghx file expects
    before running it, or when building dynamic user interfaces for tool execution.

    Args:
        pointer (str): Absolute or relative path to a .gh or .ghx Grasshopper file.

    Returns:
        dict: {
            "status": "success",
            "path": pointer,
            "description": "...",
            "inputs": [...],
            "outputs": [...],
            "icon": ...
        }
        or {"error": "..."}
    """
    pointer = resolve_path(pointer)
    if not os.path.exists(pointer):
        return {"error": f"Grasshopper file not found: '{pointer}'"}

    payload = {"algo": None, "pointer": pointer}

    try:
        response = requests.post(f"{RHINO_COMPUTE_URL}io", json=payload, timeout=10)
        data = response.json()

        response_data = {
            "status": "success",
            "path": pointer,
            "description": data.get("Description", "Grasshopper definition"),
            "inputs": data.get("Inputs", []),
            "outputs": data.get("Outputs", []),
            "icon": data.get("Icon")
        }
        return response_data

    except Exception as e:
        response_data = {"error": f"Failed to contact Rhino.Compute: {str(e)}"}
        return response_data

@mcp.tool
def run_grasshopper_tool(pointer: str, inputs: dict) -> dict:
    """
    Runs a generic Grasshopper definition via Rhino.Compute using compute_rhino3dm.

    Args:
        pointer: Absolute path to the .gh or .ghx definition file.
        inputs: Dictionary of input names and their values.

    """
    
    pointer = resolve_path(pointer)
    if not os.path.exists(pointer):
        return {"error": f"Grasshopper file not found: '{pointer}'"}

    try:
        # Prepare the inputs for Grasshopper
        gh_inputs = []
        for name, value in inputs.items():
            # Convert each input to the format Grasshopper expects
            param = add_parameter(name, value)
            gh_inputs.append(param)

        # Evaluate
        output = gh.EvaluateDefinition(pointer, gh_inputs)

        # Decode
        decoded = decode_gh_output(output)

        # Save result
        output_path = create_file_path(pointer)
        save_3dm_file(decoded, output_path)

        response_data = {
            "status": "success",
            "pointer": pointer,
            "output_file": output_path
        }
        return response_data

    except Exception as e:
        response_data = {"error": f"Failed to run Grasshopper definition: {str(e)}"}
        return response_data

### EXERCISE 2 ###
# Add an MCP tool that runs a Grasshopper definition
# and as an input takes the geometry from provided Rhino file.

##################

@mcp.tool
def run_wave_pattern_from_surface(path: str) -> dict:
    """
    Generates a wave pattern on a surface stored inside a Rhino .3dm file
    by evaluating the Grasshopper definition 'WavePatternFromSurface.gh'
    through Rhino.Compute.

    Use this tool when you want to take an existing surface from a Rhino file
    and automatically apply a parametric wave pattern created in Grasshopper.

    Args:
        path (str): Path to a Rhino .3dm file. The first object in the file
                    will be used as the input surface for the Grasshopper
                    definition.

    Returns:
        dict: {
            "status": "success",
            "pointer": path_to_grasshopper_file,
            "output_file": saved_3dm_path
        }
        or {"error": "..."}
    """
    try:
        # Validate input file
        path = resolve_path(path)
        if not os.path.exists(path):
            return {"error": f"Rhino file not found: '{path}'"}

        # Resolve GH definition path
        gh_path = os.path.abspath(
            os.path.join("assets", "WavePatternFromSurface.gh")
        )
        if not os.path.exists(gh_path):
            return {"error": f"Grasshopper file not found at '{gh_path}'"}

        # Load Rhino model
        model = rhino3dm.File3dm.Read(path)
        if model is None or not model.Objects:
            return {"error": f"Could not read geometry from '{path}'"}
        
        print(f"Running Grasshopper definition '{gh_path}' with surface from '{path}'")
            
        # Extract first geometry
        geometry = model.Objects[0].Geometry

        # Encode geometry and convert to JSON
        encoded_geo = json.dumps(geometry.Encode())

        # Used add_parameter method to create GH input called "surface"


        # Add this parameter to the list of GH inputs called gh_inputs


        # Run Grasshopper definition through Rhino.Compute using gh_path and gh_inputs
        # and save the result to variable called output


        # Decode Compute output into variable called decoded


        # Create a file path to save the result .3dm file


        # Save the decoded result into the output_file using save_3dm_file method


        # Add to the response data the pointer to GH file and output file path
        response_data = {
            "status": "success"
        }
        return response_data

    except Exception as e:
        response_data = {"error": f"Failed to run wave pattern tool: {str(e)}"}
        return response_data



##############################################################
## R U N N I N G    T H E    S E R V E R
##############################################################

if __name__ == "__main__":
    # Run the MCP server with HTTP transport (Streamable HTTP)
    mcp.run(
        transport="http",
        host="0.0.0.0",  # Bind to all interfaces for external access (any IP), 127.0.0.1 allows only local access
        port=8001,       # HTTP port
        log_level="INFO", # Set logging level
    )