
import requests
import json
import urllib.parse

def test_query_manual(name):
    clean_name = name.replace("ABS_", "").replace("REL_", "").replace("_", " ")
    print(f"--- Searching for: '{clean_name}' ---")
    
    # Manually construct the query string
    # We want: criteria=model::Structure,rma::criteria,[name$ilike'%amygdala%'],rma::options[num_rows$eq5]
    
    # Note: Requests might encode $, which Allen API expects.
    # The error 'extraneous input' suggests it received the quote but didn't expect it there?
    # Or maybe the $ilike operator is the issue. Let's try $eq first for exact match if possible, or correct ilike usage.
    
    # Try exact match first to simplify
    criteria_val = f"model::Structure,rma::criteria,[name$ilike'%{clean_name}%']"
    
    # Manually encode only the value parts if needed, but requests params usually handles it.
    # Let's try constructing the URL directly.
    
    base = "http://api.brain-map.org/api/v2/data/query.json"
    full_url = f"{base}?criteria={criteria_val}&num_rows=5"
    
    print(f"Direct URL: {full_url}")
    
    try:
        response = requests.get(full_url)
        print(f"Response URL: {response.url}")
        
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                print(f"Success! Found {len(data['msg'])} items.")
                for s in data['msg']:
                     print(f"ID: {s['id']} | Name: {s['name']}")
                return data['msg'][0]['id'] if data['msg'] else None
            else:
                 print("API Success: False")
                 print(data)
        else:
            print(f"HTTP {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(e)

if __name__ == "__main__":
    # Test specific known name
    test_query_manual("Basolateral amygdalar nucleus")
    test_query_manual("Amygdala")
