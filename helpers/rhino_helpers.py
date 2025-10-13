import os
import rhino3dm
from typing import Dict, List, Tuple, Set, Any, Optional


def read_3dm_file(path: str) -> Optional[rhino3dm.File3dm]:
    """
    Read a Rhino 3dm file and return the model object.
    """
    if not os.path.exists(path):
        return None
    
    try:
        model = rhino3dm.File3dm.Read(path)
        return model
    except Exception:
        return None


def get_layers(model: rhino3dm.File3dm) -> List[Dict[str, Any]]:
    """
    Get information about all layers in a Rhino model.
    """
    if not model or not model.Layers:
        return []
    
    layers = model.Layers
    layer_info = []
    
    for layer in layers:
        color = layer.Color
        if isinstance(color, tuple) and len(color) >= 3:
            r, g, b = color[0], color[1], color[2]
            alpha = color[3] if len(color) > 3 else 255
            rgb = f"RGB({r},{g},{b}), Alpha: {alpha}"
        else:
            rgb = f"Color format unknown: {color}"
        
        parent_id = None
        if hasattr(layer, "ParentLayerId"):
            parent_id = layer.ParentLayerId
        
        layer_info.append({
            "index": layer.Index if hasattr(layer, "Index") else None,
            "name": layer.Name,
            "visible": not layer.Visible,
            "locked": layer.Locked,
            "color": rgb,
            "color_tuple": color,
            "parent": parent_id
        })
    
    return layer_info


def get_geometry_by_layer(model: rhino3dm.File3dm) -> Dict[int, Dict[str, Any]]:
    """
    Analyze geometry by layer in a Rhino model.
    """
    if not model:
        return {}
    
    objects = model.Objects
    layer_geometry = {}
    
    for obj in objects:
        obj_layer_index = obj.Attributes.LayerIndex
        
        if obj_layer_index not in layer_geometry:
            layer_geometry[obj_layer_index] = {
                "count": 0,
                "types": set()
            }
        
        layer_geometry[obj_layer_index]["count"] += 1
        
        # Get object type and add to the set of types for this layer
        geometry = obj.Geometry
        if geometry:
            object_type = geometry.ObjectType
            layer_geometry[obj_layer_index]["types"].add(str(object_type))
    
    return layer_geometry


def get_object_count(model: rhino3dm.File3dm) -> int:
    if not model or not model.Objects:
        return 0
    
    return len(model.Objects)


def format_layer_info(
    layer_info: List[Dict[str, Any]], 
    geometry_info: Dict[int, Dict[str, Any]], 
    file_name: str
) -> str:
    """
    Format layer and geometry information into a readable string.
    """
    if not layer_info:
        return "No layers found in the file."
    
    output = f"Found {len(layer_info)} layers in '{file_name}':\n\n"
    
    for idx, info in enumerate(layer_info, 1):
        layer_index = info.get("index")
        output += f"{idx}. {info['name']}\n"
        output += f"   Visible: {'Yes' if info['visible'] else 'No'}\n"
        output += f"   Locked: {'Yes' if info['locked'] else 'No'}\n"
        output += f"   Color: {info['color']}\n"
        
        if layer_index is not None and layer_index in geometry_info:
            geom = geometry_info[layer_index]
            if geom["count"] > 0:
                output += f"   Objects: {geom['count']}\n"
                if geom["types"]:
                    output += f"   Object types: {', '.join(geom['types'])}\n"
            else:
                output += f"   Objects: None (Empty layer)\n"
        else:
            output += f"   Objects: None (Empty layer)\n"
            
        if info['parent']:
            output += f"   Parent: {info['parent']}\n"
        output += "\n"
    

    total_objects = sum(geom["count"] for geom in geometry_info.values())
    layers_with_geometry = len([g for g in geometry_info.values() if g["count"] > 0])
    
    output += f"Summary:\n"
    output += f"   Total objects in model: {total_objects}\n"
    output += f"   Total layers: {len(layer_info)}\n"
    output += f"   Layers with geometry: {layers_with_geometry}\n"
    
    return output

def encode_geometry(geometry: rhino3dm.CommonObject) -> str:
    """
    Encode a Rhino geometry object to a JSON string.
    """
    if not geometry:
        return ""
    
    try:
        return json.dumps(geometry.Encode())
    except Exception:
        return ""