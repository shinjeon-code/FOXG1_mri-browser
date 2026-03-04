
import requests
import json
import urllib.parse

def test_query(name):
    # Clean name
    clean_name = name.replace("ABS_", "").replace("REL_", "").replace("_", " ")
    print(f"--- Searching for: '{clean_name}' ---")
    
    base_url = "http://api.brain-map.org/api/v2/data/query.json"
    
    # Criteria: Search for Structure where name contains the string
    # We use 'ilike' (case-insensitive like)
    # properly quote the string
    criteria = f"model::Structure,rma::criteria,[name$ilike'%{clean_name}%']"
    
    # Add some options to limit rows
    criteria += ",rma::options[num_rows$eq5]"
    
    print(f"Query criteria: {criteria}")
    
    try:
        response = requests.get(base_url, params={'criteria': criteria})
        print(f"URL: {response.url}")
        
        if response.status_code != 200:
            print(f"HTTP Error: {response.status_code}")
            return

        data = response.json()
        
        if data['success']:
            structures = data['msg']
            print(f"Found {len(structures)} matches.")
            for s in structures:
                print(f"  ID: {s['id']}, Name: {s['name']}, Acronym: {s['acronym']}")
        else:
            print("Query failed in API response.")
            print(f"Message: {data.get('msg')}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_query("ABS_amygdala")
    test_query("ABS_thalamus")
