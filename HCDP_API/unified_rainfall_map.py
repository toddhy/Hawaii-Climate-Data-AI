"""
Unified Rainfall Map Generator

This script creates an interactive Folium map that combines:
1. Weather station markers with average monthly rainfall (from station_rainfall_data.json).
2. A raster (gridded) rainfall overlay (aggregated from TIFF files in the downloads directory).

Usage:
    python unified_rainfall_map.py [--json PATH] [--tiff_dir DIR] [--output FILENAME]
                                   [--lat LAT] [--lon LON] [--radius KM]

Note: This script DOES NOT download new data. It only processes existing local files.
If JSON or TIFF data is missing, the corresponding layer will be omitted from the map.
"""
import os
import glob
import json
import math
import numpy as np
import rasterio
from rasterio.transform import xy
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import folium
from folium.raster_layers import ImageOverlay
import branca
import argparse

# --- Configuration ---
DEFAULT_JSON = "station_rainfall_data.json"
DEFAULT_TIFF_DIR = "downloads"
OUTPUT_MAP = "unified_rainfall_map.html"

def get_station_data(json_path):
    """
    Extracts and averages station rainfall data from JSON.
    """
    if not os.path.exists(json_path):
        return []

    with open(json_path, 'r') as f:
        data = json.load(f)

    stations = []
    for entry in data:
        info = entry['station_info']
        api_res = entry['api_response']
        if isinstance(api_res, dict) and "error" not in api_res:
            values = [v for v in api_res.values() if isinstance(v, (int, float))]
            if values:
                avg_rf = sum(values) / len(values)
                stations.append({
                    'lat': info['lat'], 'lon': info['lon'],
                    'name': info['name'], 'skn': info['skn'],
                    'avg_rainfall': avg_rf
                })
    return stations

def haversine_dist(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points on the earth.
    Can accept numpy arrays.
    """
    R = 6371.0  # Earth radius in km
    dlat = np.radians(lat2 - lat1)
    dlon = np.radians(lon2 - lon1)
    a = np.sin(dlat/2)**2 + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(dlon/2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
    return R * c

def mask_raster_to_circle(data, meta, center_lat, center_lon, radius_km):
    """
    Masks raster data to a circular area using Haversine distance.
    """
    rows, cols = data.shape
    transform = meta['transform']
    
    # Generate meshgrid of row/col indices
    r_idx, c_idx = np.meshgrid(np.arange(rows), np.arange(cols), indexing='ij')
    
    # Convert to coordinates (lon, lat) using the transform
    # transform is (a, b, c, d, e, f) where x = a*col + b*row + c, y = d*col + e*row + f
    # Rasterio transform: (res_x, shear_x, x_min, shear_y, res_y, y_max)
    # x = transform[0] * c + transform[1] * r + transform[2]
    # y = transform[3] * c + transform[4] * r + transform[5]
    
    lons = transform[0] * c_idx + transform[1] * r_idx + transform[2]
    lats = transform[3] * c_idx + transform[4] * r_idx + transform[5]
    
    # Calculate distance for all pixels
    dist = haversine_dist(center_lat, center_lon, lats, lons)
    
    masked_data = data.copy()
    masked_data[dist > radius_km] = np.nan
    return masked_data

def process_tiffs(tiff_dir):
    """
    Aggregates TIFF files and returns data + metadata for overlay.
    """
    tiff_files = glob.glob(os.path.join(tiff_dir, "*.tiff"))
    if not tiff_files:
        return None, None, None
    
    aggregated_data = None
    meta = None
    count = 0

    for tiff_path in tiff_files:
        with rasterio.open(tiff_path) as src:
            data = src.read(1).astype(float)
            if src.nodata is not None:
                data[data == src.nodata] = np.nan
            
            if aggregated_data is None:
                aggregated_data = data
                meta = src.meta
            else:
                aggregated_data = np.nansum([aggregated_data, data], axis=0)
            count += 1

    if aggregated_data is not None:
        aggregated_data /= count
    
    with rasterio.open(tiff_files[0]) as src:
        bounds = src.bounds
        folium_bounds = [[bounds.bottom, bounds.left], [bounds.top, bounds.right]]
    
    return aggregated_data, folium_bounds, meta

def create_unified_map(json_path, tiff_dir, output_file, center_lat=None, center_lon=None, radius_km=None):
    """
    Creates a map with both raster overlay and station markers.
    """
    print("Loading data...")
    stations = get_station_data(json_path)
    raster_data, raster_bounds, raster_meta = process_tiffs(tiff_dir)

    if not stations and raster_data is None:
        print("No data found (JSON or TIFFs).")
        return

    # Determine map center and radius for clipping
    if center_lat and center_lon:
        center = [center_lat, center_lon]
    elif stations:
        center = [np.mean([s['lat'] for s in stations]), np.mean([s['lon'] for s in stations])]
    elif raster_bounds:
        center = [(raster_bounds[0][0] + raster_bounds[1][0]) / 2, (raster_bounds[0][1] + raster_bounds[1][1]) / 2]
    else:
        center = [21.3069, -157.8583] # Honolulu default

    if radius_km is None and stations:
        # Auto-calculate radius to cover all stations
        distances = [haversine_dist(center[0], center[1], s['lat'], s['lon']) for s in stations]
        radius_km = max(distances) * 1.1 if distances else 10.0
    elif radius_km is None:
        radius_km = 10.0

    print(f"Masking raster to {radius_km:.2f}km radius around {center}...")
    
    m = folium.Map(location=center, zoom_start=9, tiles='cartodbpositron')

    # Mask the raster data
    if raster_data is not None:
        raster_data = mask_raster_to_circle(raster_data, raster_meta, center[0], center[1], radius_km)

    # Define Unified Colormap based on LOCAL range
    colors = ['#f7fbff', '#deebf7', '#c6dbef', '#9ecae1', '#6baed6', '#4292c6', '#2171b5', '#084594']
    
    # Calculate LOCAL range for normalization
    vals = []
    if stations:
        # Use only stations within the circle for the scale if possible
        for s in stations:
            d = haversine_dist(center[0], center[1], s['lat'], s['lon'])
            if d <= radius_km:
                vals.append(s['avg_rainfall'])
    
    if raster_data is not None:
        r_min, r_max = np.nanmin(raster_data), np.nanmax(raster_data)
        if not np.isnan(r_min): vals.append(r_min)
        if not np.isnan(r_max): vals.append(r_max)
    
    if not vals:
        vmin, vmax = 0, 100
    else:
        vmin, vmax = min(vals), max(vals)

    print(f"Color range (relative): {vmin:.2f} to {vmax:.2f} mm")
    colormap = branca.colormap.LinearColormap(colors=colors, vmin=vmin, vmax=vmax, caption="Average Monthly Rainfall (mm)")

    # 1. Add Raster Overlay
    if raster_data is not None:
        print("Adding raster overlay...")
        cmap = mcolors.LinearSegmentedColormap.from_list("hcdp", colors)
        norm = plt.Normalize(vmin=vmin, vmax=vmax)
        colored_data = cmap(norm(raster_data))
        colored_data[np.isnan(raster_data), 3] = 0
        
        plt.imsave("temp_unified.png", colored_data)
        ImageOverlay(image="temp_unified.png", bounds=raster_bounds, opacity=0.6, interactive=True, zindex=1).add_to(m)

    # 2. Add Station Markers
    if stations:
        print(f"Adding {len(stations)} station markers...")
        station_group = folium.FeatureGroup(name="Weather Stations").add_to(m)
        for s in stations:
            popup_text = f"<b>{s['name']}</b><br>SKN: {s['skn']}<br>Avg Rainfall: {s['avg_rainfall']:.2f} mm"
            folium.CircleMarker(
                location=[s['lat'], s['lon']],
                radius=6,
                popup=folium.Popup(popup_text, max_width=200),
                color='black', weight=1, fill=True,
                fill_color=colormap(s['avg_rainfall']),
                fill_opacity=0.9
            ).add_to(station_group)

    # Add Circle for visualization of the mask area
    folium.Circle(
        location=center,
        radius=radius_km * 1000,
        color='blue',
        weight=1,
        fill=False,
        dash_array='5, 5'
    ).add_to(m)

    # Add Layer Control and Legend
    folium.LayerControl().add_to(m)
    colormap.add_to(m)
    
    m.save(output_file)
    print(f"Success! Unified map generated: {os.path.abspath(output_file)}")
    if os.path.exists("temp_unified.png"):
        os.remove("temp_unified.png")

def main():
    parser = argparse.ArgumentParser(description="Create a unified rainfall map (Stations + Raster).")
    parser.add_argument("--json", default=DEFAULT_JSON, help=f"Station JSON file (default: {DEFAULT_JSON})")
    parser.add_argument("--tiff_dir", default=DEFAULT_TIFF_DIR, help=f"Directory with TIFFs (default: {DEFAULT_TIFF_DIR})")
    parser.add_argument("--output", default=OUTPUT_MAP, help=f"Output file (default: {OUTPUT_MAP})")
    parser.add_argument("--lat", type=float, help="Center latitude for clipping")
    parser.add_argument("--lon", type=float, help="Center longitude for clipping")
    parser.add_argument("--radius", type=float, help="Radius in km for clipping")
    
    args = parser.parse_args()
    create_unified_map(args.json, args.tiff_dir, args.output, args.lat, args.lon, args.radius)

if __name__ == "__main__":
    main()
