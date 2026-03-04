
import requests
import json
import logging

def get_closest_image(structure_id):
    # 1. Get Structure Center
    base_url = "http://api.brain-map.org/api/v2/data/query.json"
    center_query = f"model::StructureCenter,rma::criteria,[structure_id$eq{structure_id}]"
    
    try:
        r = requests.get(base_url, params={'criteria': center_query})
        data = r.json()
        if not data['success'] or not data['msg']:
            print("Center not found")
            return None
        
        center = data['msg'][0]
        z_coord = center['z'] # 3600 microns?
        print(f"Structure Center Z: {z_coord}")
        
    except Exception as e:
        print(f"Error getting center: {e}")
        return None

    # 2. Get Atlas Images for P56 Coronal (100048576)
    # We want to find the image with 'position' closest to z_coord?
    # Or maybe 'z'? Let's check a sample image.
    
    atlas_id = 100048576 
    # Query: model::AtlasImage
    # criteria: data_set_id = 100048576
    # options: order by position? or just get all and sort in python
    
    image_query = f"model::AtlasImage,rma::criteria,[data_set_id$eq{atlas_id}],rma::options[num_rows$eq5]"
    
    try:
        r = requests.get(base_url, params={'criteria': image_query})
        imgs = r.json()['msg']
        print(f"Sample Image Metadata: {imgs[0]}")
        # Check if 'position' or 'section_number' matches Z
        
        # Let's try to get ALL images (there are ~132)
        # Sort by |image.position - z_coord|
        full_query = f"model::AtlasImage,rma::criteria,[data_set_id$eq{atlas_id}],rma::options[num_rows$eq200]"
        r = requests.get(base_url, params={'criteria': full_query})
        all_imgs = r.json()['msg']
        
        # Find closest
        # Note: position in API might be in different units?
        # CCFv3 Z is usually Anterior-Posterior in microns.
        # Atlas images usually have 'position' in microns too?
        # Let's check the range of positions in all_imgs
        positions = [i['position'] for i in all_imgs]
        print(f"Position Range: {min(positions)} to {max(positions)}")
        
        closest = min(all_imgs, key=lambda x: abs(x['position'] - z_coord))
        print(f"Closest Image: ID={closest['id']}, Position={closest['position']}")
        
        # 3. Construct URL
        # We want the SVG with the structure highlighted.
        # URL: http://api.brain-map.org/api/v2/svg_download/{id}?groups={structure_id}
        # But wait, structure_id in 'groups' checks for ontology Node? 
        # Usually annotations are stored by StructureID.
        
        url = f"http://api.brain-map.org/api/v2/svg_download/{closest['id']}?groups={structure_id}"
        print(f"Proposed URL: {url}")
        
    except Exception as e:
        print(f"Error getting images: {e}")

    

# Debug App Logic
print("--- Debugging App Logic ---")
base_url = "http://api.brain-map.org/api/v2/data/query.json"

# 1. Get Images
atlas_id = 100048576
# Removed order parameter to avoid syntax error. Sorting in Python is fine.
img_q = f"model::AtlasImage,rma::criteria,[data_set_id$eq{atlas_id}],rma::options[num_rows$eq500]"
print(f"Query: {base_url}?criteria={img_q}")
r = requests.get(base_url, params={'criteria': img_q})
data = r.json()
success = data.get('success', False)
msg = data.get('msg')
print(f"Image Query Success: {success}, Msg Type: {type(msg)}, Count: {len(msg) if isinstance(msg, list) else 'N/A'}")

if not success:
    print(f"API Error Message: {msg}")

if not success or not isinstance(msg, list):
    print("FAILED to get images list.")
    exit()
    
# Sort in Python
imgs = sorted(msg, key=lambda x: x['section_number'])

# 2. Get Amygdala Center
structure_id = 403
center_q = f"model::StructureCenter,rma::criteria,[structure_id$eq{structure_id}]"
r = requests.get(base_url, params={'criteria': center_q})
data = r.json()
if data['success'] and data['msg']:
    center_x = data['msg'][0]['x']
    print(f"Amygdala Center X: {center_x}")
    
    # 3. Find Closest
    closest = min(imgs, key=lambda i: abs(i['x'] - center_x))
    print(f"Closest Image: {closest['id']}, X={closest['x']}, Section={closest['section_number']}")
    
    url = f"http://api.brain-map.org/api/v2/atlas_image_download/{closest['id']}?annotation=true&atlas=1&downsample=3"
    print(f"URL: {url}")
    
    # Check if URL works?
    r_img = requests.head(url)
    print(f"URL Status: {r_img.status_code}")
    
else:
    print("Failed to get center.")

