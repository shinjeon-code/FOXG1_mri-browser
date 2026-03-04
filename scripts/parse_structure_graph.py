
import json

def load_structure_graph(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    # Check if data is list or dict with 'msg'
    if isinstance(data, dict) and 'msg' in data:
        nodes = data['msg']
    else:
        nodes = data
        
    return nodes

def flatten_structures(nodes, mapping=None):
    if mapping is None:
        mapping = {}
        
    for node in nodes:
        name = node['name']
        sid = node['id']
        
        # Store exact name
        mapping[name.lower()] = sid
        
        # Store acronym
        if 'acronym' in node:
            mapping[node['acronym'].lower()] = sid

        # Store name without comma suffix (e.g., "Frontal pole, cerebral cortex" -> "Frontal pole")
        if ',' in name:
            short_name = name.split(',')[0].strip()
            mapping[short_name.lower()] = sid
        
        # Recursively process children
        if 'children' in node and node['children']:
            # Pass the same mapping object down
            flatten_structures(node['children'], mapping)
            
    return mapping

def find_match(dataset_region_name, mapping):
    # Clean up dataset name
    # e.g., "ABS_Basolateral_amygdala" -> "Basolateral amygdala"
    clean = dataset_region_name.replace("ABS_", "").replace("REL_", "").replace("_", " ")
    
    # Try exact case-insensitive match
    if clean.lower() in mapping:
        return mapping[clean.lower()]
    
    # Try fuzzy or partial?
    # Allen Atlas names are specific. "Basolateral amygdalar nucleus" vs "Basolateral amygdala"
    # Let's try to find if any map key contains our clean name or vice-versa
    
    search_name = clean.lower()
    
    # 0. Manual Overrides for high-level structures
    # These are regions that might be named differently in the ontology or are aggregates
    overrides = {
        'amygdala': 403, # Amygdalar nuclei
        'hippocampus': 1089, # Hippocampal formation
        'basolateral amygdala': 295, # Basolateral amygdalar nucleus
        'striatum': 477,
        'hypothalamus': 1097,
        'midbrain': 313,
        'pons': 771,
        'medulla': 354,
        'cerebellum': 512
    }
    
    if search_name in overrides:
        return overrides[search_name]
    
    # 1. Exact match
    if search_name in mapping:
        return mapping[search_name]
        
    # 2. Try simple cleanups
    # "Basolateral amygdala" might be "Basolateral amygdalar nucleus"
    # Try matching first word? No.
    
    # 3. Substring match
    # Find all keys where search_name is equal to key or search_name is in key or key is in search_name
    candidates = []
    for k, v in mapping.items():
        # Check if dataset name "basolateral amygdala" is part of Allen name "basolateral amygdalar nucleus"
        # Split into words
        d_words = set(search_name.split())
        a_words = set(k.split())
        
        # Intersection
        common = d_words.intersection(a_words)
        score = len(common) / len(d_words) if d_words else 0
        
        if score > 0.8: # High overlap
             candidates.append((score, len(k), v, k))
             
    # Sort by score desc, then length asc (prefer shorter exact matches)
    if candidates:
        candidates.sort(key=lambda x: (-x[0], x[1]))
        best = candidates[0]
        # print(f"  Mapping '{dataset_region_name}' -> '{best[3]}' (Score: {best[0]:.2f})")
        return best[2]
        
    return None

if __name__ == "__main__":
    file_path = 'structure_graph.json'
    try:
        nodes = load_structure_graph(file_path)
        structure_map = flatten_structures(nodes)
        print(f"Loaded {len(structure_map)} structures.")
        
        # Debug: Print some keys
        print("First 20 keys:", list(structure_map.keys())[:20])
        
        # Test some known regions from the dataset
        test_regions = [
            "ABS_Amygdala",
            "ABS_Thalamus",
            "ABS_Hippocampus",
            "ABS_Isocortex",
            "ABS_Basolateral_amygdala" # This might fail if Allen calls it "Basolateral amygdalar nucleus"
        ]
        
        for r in test_regions:
            mid = find_match(r, structure_map)
            print(f"{r} -> ID: {mid}")
            
    except Exception as e:
        print(f"Error: {e}")
