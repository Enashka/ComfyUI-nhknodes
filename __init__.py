import os
import importlib.util

# Initialize node mappings
NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

# Get current directory
current_dir = os.path.dirname(os.path.realpath(__file__))

def load_node_file(filename):
    """Load a node file and extract its mappings"""
    file_path = os.path.join(current_dir, filename)
    if not os.path.exists(file_path):
        return
    
    try:
        # Load the module
        spec = importlib.util.spec_from_file_location(filename[:-3], file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Extract mappings
        if hasattr(module, "NODE_CLASS_MAPPINGS"):
            NODE_CLASS_MAPPINGS.update(module.NODE_CLASS_MAPPINGS)
        if hasattr(module, "NODE_DISPLAY_NAME_MAPPINGS"):
            NODE_DISPLAY_NAME_MAPPINGS.update(module.NODE_DISPLAY_NAME_MAPPINGS)
            
        print(f"Successfully loaded {filename}: {list(module.NODE_CLASS_MAPPINGS.keys()) if hasattr(module, 'NODE_CLASS_MAPPINGS') else 'No nodes'}")
        
    except Exception as e:
        print(f"Error loading {filename}: {e}")

# Load all node files
load_node_file("size_picker.py")
load_node_file("cycling_switch.py")
load_node_file("execution_counter.py")
load_node_file("image_grid_composite.py")
load_node_file("image_grid_batch.py")
load_node_file("double_switch_nodes.py")
load_node_file("image_loader_with_previews.py")
load_node_file("text_display.py")
load_node_file("simple_text_input.py")
load_node_file("text_combiner.py")
load_node_file("text_template.py")
load_node_file("openai_api.py")
load_node_file("ollama_api.py")
load_node_file("interval_gate.py")
load_node_file("visual_resizer.py")
load_node_file("load_image_series.py")
load_node_file("load_2x2_grid_series.py")
load_node_file("load_3x3_grid_series.py")
load_node_file("play_sound.py")
load_node_file("add_headroom.py")
load_node_file("edit_with_krita.py")
load_node_file("flux2_image_edit_encode.py")

print(f"NHK Nodes: Loaded {len(NODE_CLASS_MAPPINGS)} nodes: {list(NODE_CLASS_MAPPINGS.keys())}")

# Declare web directory for frontend JavaScript files
WEB_DIRECTORY = "./web"

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS', 'WEB_DIRECTORY']