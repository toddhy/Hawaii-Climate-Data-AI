import json
import os

def find_stations():
    json_path = r'c:\SCIPE\my_maps\HCDPstations.json'
    
    # Range specified by user: 20 to 22 latitude, -156 to -158 longitude
    lat_min, lat_max = 18, 20
    lng_min, lng_max = -157.0, -155.0 # -158 is less than -156
    
    if not os.path.exists(json_path):
        print(f"Error: {json_path} not found.")
        return

    print(f"Filtering stations in {json_path}...")
    print(f"Range: Lat [{lat_min}, {lat_max}], Lng [{lng_min}, {lng_max}]")
    
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    stations = data.get('result', [])
    matching_ids = []
    
    for entry in stations:
        val = entry.get('value', {})
        try:
            lat = float(val.get('lat'))
            lng = float(val.get('lng'))
            # Using 'skn' as the representative station_id
            sid = val.get('skn')
            
            if lat_min <= lat <= lat_max and lng_min <= lng <= lng_max:
                if sid:
                    matching_ids.append(str(sid))
        except (ValueError, TypeError):
            continue
            
    # Sort for cleaner output
    matching_ids.sort()
    
    print(f"Found {len(matching_ids)} stations.")
    
    output_file = r'c:\SCIPE\HCDP-data-for-AI\HCDP_API\matching_stations.txt'
    with open(output_file, 'w') as f_out:
        f_out.write(", ".join(matching_ids))
    
    print(f"Full list saved to: {output_file}")
    # Print first 20 for quick view
    print(f"First 20 IDs: {', '.join(matching_ids[:20])}...")

if __name__ == "__main__":
    find_stations()
