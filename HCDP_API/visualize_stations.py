import os
import requests
import folium
import json
import urllib3

# Suppress InsecureRequestWarning if verify=False is used
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def fetch_hcdp_stations(limit=2000):
    """
    Fetches station metadata directly from the HCDP API.
    """
    url = "https://api.hcdp.ikewai.org/stations"
    
    # Get API token from environment variable
    api_token = os.environ.get("HCDP_API_TOKEN")
    if not api_token:
        print("Error: HCDP_API_TOKEN environment variable not set.")
        return []

    # The 'q' parameter must be a JSON string. 
    # To get metadata, we use 'name': 'hcdp_station_metadata'
    params = {
        'q': json.dumps({'name': 'hcdp_station_metadata'}),
        'limit': limit
    }
    
    headers = {
        "Authorization": f"Bearer {api_token}"
    }
    
    print(f"Fetching station data from {url}...")
    try:
        # verify=False is used as a precaution for standard API access patterns
        response = requests.get(url, headers=headers, params=params, verify=False)
        response.raise_for_status()
        
        # The API response is a dictionary with a 'result' key containing the station list
        data = response.json()
        stations = data.get('result', [])
        
        if not stations:
            print("No stations found in the API response.")
            return []

        print(f"Successfully fetched {len(stations)} stations.")
        return stations
    except Exception as e:
        print(f"Error fetching stations: {e}")
        return []

def create_hcdp_api_map(stations, output_file="hcdp_api_stations_map.html"):
    """
    Creates an interactive Folium map from the API station data.
    """
    if not stations:
        print("No stations to map.")
        return None

    # Initialize map centered on Hawai'i
    m = folium.Map(location=[20.5, -157.5], zoom_start=7, tiles='cartodbpositron')

    for station in stations:
        # Station metadata is nested inside the 'value' key
        val = station.get('value', {})
        lat = val.get('lat')
        lng = val.get('lng')
        name = val.get('name', 'Unknown Station')
        sid = val.get('skn') or val.get('nws_id') or val.get('station_id') or 'N/A'
        network = val.get('network', 'N/A')
        island = val.get('island', 'N/A')

        if lat and lng:
            try:
                # API coordinates are strings; convert to float for Folium
                lat_f = float(lat)
                lng_f = float(lng)
                popup_text = f"<b>{name}</b><br>ID: {sid}<br>Network: {network}<br>Island: {island}"
                folium.CircleMarker(
                    location=[lat_f, lng_f],
                    radius=4,
                    popup=folium.Popup(popup_text, max_width=300),
                    color='#e81a73',
                    fill=True,
                    fill_color='#e81a73',
                    fill_opacity=0.6
                ).add_to(m)
            except (ValueError, TypeError):
                continue

    m.save(output_file)
    print(f"Successfully created: {os.path.abspath(output_file)}")
    return os.path.abspath(output_file)

if __name__ == "__main__":
    stations = fetch_hcdp_stations()
    if stations:
        create_hcdp_api_map(stations)
