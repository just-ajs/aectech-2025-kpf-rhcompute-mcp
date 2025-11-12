import os
import datetime
import json
import compute_rhino3d.Grasshopper as gh
import rhino3dm
from typing import Any, List, Dict


def create_file_path(pointer: str) -> str:
    """Create a unique file path for saving output files."""

    # Make filename unique: extract base name and add timestamp
    base_name = os.path.splitext(os.path.basename(pointer))[0]
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    # Go one folder up from the current file's directory
    parent_dir = os.path.dirname(os.path.dirname(__file__))
    output_dir = os.path.join(parent_dir, "outputs")
    os.makedirs(output_dir, exist_ok=True)  # Ensure outputs directory exists
    filename = f"{base_name}_{timestamp}.3dm"
    output_path = os.path.join(output_dir, filename)
    return output_path

def add_parameter(input_name: str, input_value: Any) -> gh.DataTree:
    input_tree = gh.DataTree(input_name)
    input_tree.Append([0], [input_value])
    return input_tree

def decode_gh_output(output: dict, tree_path: str = '{0}') -> List[Any]:
    """Decode Grasshopper output at a given tree path into Rhino geometry, numbers, or text."""
    branch = output['values'][0]['InnerTree'][tree_path]
    results = []
    for item in branch:
        data = item['data']
        # Remove extra quotes if present (e.g., '"10"' -> '10')
        if isinstance(data, str) and data.startswith('"') and data.endswith('"'):
            data = data[1:-1]
        # Try geometry decode
        try:
            obj = rhino3dm.CommonObject.Decode(json.loads(data))
            print('decoded object:')
            print(obj)
            if obj is not None:
                results.append(obj)
                continue
        except Exception:
            pass
        # Try number decode
        try:
            if '.' in data:
                num = float(data)
            else:
                num = int(data)
            results.append(num)
            continue
        except Exception:
            pass
        # Fallback: return as string
        results.append(data)
    return results

def save_3dm_file(objects: List[rhino3dm.CommonObject], filename: str) -> None:

    """Save a list of Rhino geometry objects to a .3dm file, handling multiple types."""
    model = rhino3dm.File3dm()
    for obj in objects:
        # Try adding as curve
        try:
            if isinstance(obj, rhino3dm.Curve):
                model.Objects.AddCurve(obj)
                continue
        except Exception:
            pass
        # Try adding as point
        try:
            if isinstance(obj, rhino3dm.Point):
                model.Objects.AddPoint(obj)
                continue
        except Exception:
            pass
        # Try adding as surface
        try:
            if isinstance(obj, rhino3dm.Surface):
                model.Objects.AddSurface(obj)
                continue
        except Exception:
            pass
        # Try adding as mesh
        try:
            if isinstance(obj, rhino3dm.Mesh):
                model.Objects.AddMesh(obj)
                continue
        except Exception:
            pass
        # Try adding as bpre
        try:
            if isinstance(obj, rhino3dm.Brep):
                model.Objects.AddBrep(obj)
                continue
        except Exception:
            pass
        # Try subs
        try:
            if isinstance(obj, rhino3dm.SubD):
                model.Objects.Add(obj)
                continue
        except Exception:
            pass
        # Try adding as SubD
        try:
            if hasattr(rhino3dm, "SubD") and isinstance(obj, rhino3dm.SubD):
                model.Objects.AddSubD(obj)
                continue
        except Exception:
            pass
        # Add more geometry types as needed
    model.Write(filename)

def resolve_path(path: str) -> str:
    """Resolves a path to absolute if it's not already."""
    return path if os.path.isabs(path) else os.path.abspath(path)