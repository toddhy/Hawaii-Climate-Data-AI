# Code is generated with Gemini 3 Flash
"""
This script creates an interactive map of HCDP weather stations using Folium. Takes json file as input
and outputs an html map file. Uses output from fetch_station_data.py.
"""

import json
import folium
import os

# --- Configuration ---
INPUT_FILE = "station_rainfall_data.json"
OUTPUT_MAP = "station_map.html"

def create_station_map(station_data=None, output_file=OUTPUT_MAP):
    """
    Creates an interactive Folium map from station data.
    If station_data is None, it attempts to read from INPUT_FILE.
    station_data should be a list of dicts or a Pandas DataFrame with keys: lat, lon/lng, name, skn, distance_km.
    """
    # 1. Load the data
    if station_data is None:
        if not os.path.exists(INPUT_FILE):
            print(f"Error: {INPUT_FILE} not found. Please run fetch_station_data.py first or provide data.")
            return
        with open(INPUT_FILE, 'r') as f:
            raw_data = json.load(f)
            # Adapt the fetch_station_data.py format
            station_data = [item['station_info'] for item in raw_data]
    
    # Convert DataFrame to list of dicts if necessary
    if hasattr(station_data, 'to_dict'):
        # Ensure 'lon' key exists if 'lng' is provided
        if 'lng' in station_data.columns and 'lon' not in station_data.columns:
            station_data = station_data.rename(columns={'lng': 'lon'})
        station_data = station_data.to_dict('records')

    if not station_data:
        print("No station data found.")
        return

    # 2. Initialize the map
    # We'll center the map on the first station's coordinates
    # Support both 'lon' and 'lng'
    for s in station_data:
        if 'lng' in s and 'lon' not in s: s['lon'] = s['lng']

    first_station = station_data[0]
    m = folium.Map(
        location=[first_station['lat'], first_station['lon']], 
        zoom_start=12,
        tiles='cartodbpositron'
    )

    print(f"Adding {len(station_data)} stations to the map...")

    # 3. Add markers for each station
    for info in station_data:
        lat = info['lat']
        lon = info['lon']
        name = info['name']
        skn = info['skn']
        dist = info.get('distance_km', 0)

        popup_html = f"""
        <div style="font-family: Arial, sans-serif; font-size: 12px;">
            <b>{name}</b><br>
            SKN: {skn}<br>
            Distance: {dist:.2f} km<br>
            Lat/Lon: {lat:.5f}, {lon:.5f}
        </div>
        """
        
        folium.CircleMarker(
            location=[lat, lon],
            radius=6,
            popup=folium.Popup(popup_html, max_width=250),
            color="#3186cc",
            fill=True,
            fill_color="#3186cc",
            fill_opacity=0.7
        ).add_to(m)

    # 4. Save the map
    m.save(output_file)
    abs_path = os.path.abspath(output_file)
    print(f"Success! Map saved to: {abs_path}")
    return abs_path

if __name__ == "__main__":
    create_station_map()
