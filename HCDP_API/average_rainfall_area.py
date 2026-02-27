import os
import requests
import folium
from folium.plugins import HeatMap
import json
import urllib3

# Suppress InsecureRequestWarning if verify=False is used
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def fetch_station_metadata():
    """
    Fetches all station metadata to create a coordinate lookup table.
    Returns: {station_id: (lat, lng, name, island)}
    """
    api_token = os.environ.get("HCDP_API_TOKEN")
    url = "https://api.hcdp.ikewai.org/stations"
    headers = {"Authorization": f"Bearer {api_token}"}
    params = {
        "q": json.dumps({"name": "hcdp_station_metadata"}),
        "limit": 5000
    }
    
    print("Fetching station metadata for coordinate lookup...")
    metadata_lookup = {}
    try:
        response = requests.get(url, headers=headers, params=params, verify=False)
        response.raise_for_status()
        raw_metadata = response.json().get('result', [])
        
        for item in raw_metadata:
            val = item.get('value', {})
            # We use 'skn' as the primary ID as it matches station_value['station_id']
            sid = val.get('skn') or val.get('station_id')
            lat = val.get('lat')
            lng = val.get('lng')
            name = val.get('name', 'Unknown')
            island = val.get('island', 'N/A')
            
            if sid and lat and lng:
                try:
                    metadata_lookup[str(sid)] = (float(lat), float(lng), name, island)
                except ValueError:
                    continue
        print(f"Loaded {len(metadata_lookup)} station metadata records.")
        return metadata_lookup
    except Exception as e:
        print(f"Error fetching metadata: {e}")
        return {}

def get_rainfall_for_area(date="2023-01", bbox=None):
    """
    Fetches rainfall station values, joins with metadata, and filters by area.
    """
    api_token = os.environ.get("HCDP_API_TOKEN")
    if not api_token:
        print("Error: HCDP_API_TOKEN environment variable not set.")
        return [], 0

    # 1. Get coordinate lookup table
    metadata = fetch_station_metadata()
    if not metadata:
        return [], 0

    # 2. Fetch rainfall values
    url = "https://api.hcdp.ikewai.org/stations"
    headers = {"Authorization": f"Bearer {api_token}"}
    query = {
        "name": "hcdp_station_value",
        "value.datatype": "rainfall",
        "value.date": date
    }
    params = {"q": json.dumps(query), "limit": 5000}

    print(f"Fetching rainfall values for {date}...")
    try:
        response = requests.get(url, headers=headers, params=params, verify=False)
        response.raise_for_status()
        value_data = response.json().get('result', [])
        print(f"Fetched {len(value_data)} rainfall records.")
        
        parsed_points = []
        total_rainfall = 0
        count = 0
        
        for item in value_data:
            val = item.get('value', {})
            sid = str(val.get('station_id'))
            rain_val = val.get('value')
            
            if sid in metadata and rain_val is not None:
                lat, lng, name, island = metadata[sid]
                rain_f = float(rain_val)
                
                # Apply spatial filter
                if bbox:
                    if not (bbox['lat_min'] <= lat <= bbox['lat_max'] and 
                            bbox['lng_min'] <= lng <= bbox['lng_max']):
                        continue
                
                parsed_points.append([lat, lng, rain_f])
                total_rainfall += rain_f
                count += 1
        
        avg_rainfall = total_rainfall / count if count > 0 else 0
        print(f"Stations in area: {count}")
        print(f"Average rainfall in area: {avg_rainfall:.2f} mm")
        
        return parsed_points, avg_rainfall

    except Exception as e:
        print(f"Error fetching rainfall values: {e}")
        return [], 0

def create_rainfall_map(data, avg_rainfall, bbox, output_file="average_rainfall_map.html"):
    if not data:
        print("No data to map.")
        return

    center_lat = (bbox['lat_min'] + bbox['lat_max']) / 2
    center_lng = (bbox['lng_min'] + bbox['lng_max']) / 2
    
    m = folium.Map(location=[center_lat, center_lng], zoom_start=10, tiles='cartodbpositron')

    # Add Target Area Box
    folium.Rectangle(
        bounds=[[bbox['lat_min'], bbox['lng_min']], [bbox['lat_max'], bbox['lng_max']]],
        color="#2a73e8",
        weight=2,
        fill=True,
        fill_opacity=0.1,
        popup=f"Target Area<br>Avg Rainfall: {avg_rainfall:.2f} mm"
    ).add_to(m)

    # Add heatmap layer
    HeatMap(data, radius=20, blur=15, min_opacity=0.3).add_to(m)

    # Add marker for the average result
    folium.Marker(
        [center_lat, center_lng],
        icon=folium.DivIcon(html=f"""<div style="font-family: sans-serif; color: white; background: rgba(42, 115, 232, 0.8); padding: 5px; border-radius: 5px; border: 1px solid white;">Average: {avg_rainfall:.2f} mm</div>""")
    ).add_to(m)

    m.save(output_file)
    print(f"Successfully created: {os.path.abspath(output_file)}")

if __name__ == "__main__":
    # Example Area: Larger bounding box for Big Island to ensure we catch stations
    my_bbox = {
        'lat_min': 18.8,
        'lat_max': 20.3,
        'lng_min': -156.1,
        'lng_max': -154.7
    }
    
    # 2023-01 has data (from previous debug run)
    points, avg = get_rainfall_for_area(date="2023-01", bbox=my_bbox)
    if points:
        create_rainfall_map(points, avg, my_bbox)
