import os
import glob
import numpy as np
import rasterio
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import folium
from folium.raster_layers import ImageOverlay
import argparse

def process_tiffs(input_dir, output_map="rainfall_raster_map.html"):
    """
    Aggregates TIFF files in a directory and creates an interactive map with the overlay.
    """
    # 1. Find all TIFF files
    tiff_files = glob.glob(os.path.join(input_dir, "*.tiff"))
    if not tiff_files:
        print(f"No .tiff files found in {input_dir}")
        return

    print(f"Found {len(tiff_files)} TIFF files. Processing...")

    # 2. Aggregate Data
    aggregated_data = None
    meta = None
    count = 0

    for tiff_path in tiff_files:
        with rasterio.open(tiff_path) as src:
            data = src.read(1).astype(float)
            # Replace no-data values (usually very small/large or specific) with NaN
            if src.nodata is not None:
                data[data == src.nodata] = np.nan
            
            if aggregated_data is None:
                aggregated_data = data
                meta = src.meta
            else:
                # Basic averaging logic: sum then divide at the end
                # Note: Handling NaNs correctly (ignoring them in sum)
                aggregated_data = np.nansum([aggregated_data, data], axis=0)
            
            count += 1

    # Final Average
    if aggregated_data is not None:
        aggregated_data /= count

    # 3. Handle Geospatial Metadata for Bounding Box
    # We need the bounding box in [lat, lon] for Folium
    with rasterio.open(tiff_files[0]) as src:
        bounds = src.bounds
        # Folium needs [[lat_min, lon_min], [lat_max, lon_max]]
        # rasterio bounds are (left, bottom, right, top) -> (lon_min, lat_min, lon_max, lat_max)
        # Note: Assuming CRS is EPSG:4326 (WGS84). HCDP data usually is.
        folium_bounds = [[bounds.bottom, bounds.left], [bounds.top, bounds.right]]
        center = [(bounds.bottom + bounds.top) / 2, (bounds.left + bounds.right) / 2]

    # 4. Create Colored Image for Overlay
    # Define colormap (matching HCDP styles)
    colors = ['#f7fbff', '#deebf7', '#c6dbef', '#9ecae1', '#6baed6', '#4292c6', '#2171b5', '#084594']
    cmap = mcolors.LinearSegmentedColormap.from_list("hcdp_rainfall", colors)
    
    # Normalize data for coloring
    norm = plt.Normalize(vmin=np.nanmin(aggregated_data), vmax=np.nanmax(aggregated_data))
    colored_data = cmap(norm(aggregated_data))
    
    # Set transparency for NoData/NaN regions
    # The result of cmap is an RGBA array. We set Alpha to 0 where we have NaN.
    colored_data[np.isnan(aggregated_data), 3] = 0

    # Save as temporary PNG for Folium
    temp_png = "temp_raster.png"
    plt.imsave(temp_png, colored_data)

    # 5. Create Map
    m = folium.Map(location=center, zoom_start=9, tiles='cartodbpositron')

    # Add ImageOverlay
    ImageOverlay(
        image=temp_png,
        bounds=folium_bounds,
        opacity=0.7,
        interactive=True,
        cross_origin=False,
        zindex=1
    ).add_to(m)

    # 6. Add Legend (Colorbar)
    import branca
    vmin = np.nanmin(aggregated_data)
    vmax = np.nanmax(aggregated_data)
    colormap = branca.colormap.LinearColormap(
        colors=colors,
        vmin=vmin,
        vmax=vmax,
        caption="Average Monthly Rainfall (mm)"
    )
    colormap.add_to(m)

    # 7. Save and Cleanup
    m.save(output_map)
    print(f"Success! Raster map generated: {os.path.abspath(output_map)}")
    
    # Optional: Keep the PNG or delete it
    # os.remove(temp_png) 

def main():
    parser = argparse.ArgumentParser(description="Create a gridded rainfall map from TIFF files.")
    parser.add_argument("--input_dir", default="downloads", help="Directory containing TIFF files (default: downloads)")
    parser.add_argument("--output", default="rainfall_raster_map.html", help="Output HTML file name")
    
    args = parser.parse_args()
    
    # Convert relative to absolute if needed, but here we assume caller is in project root or similar
    process_tiffs(args.input_dir, args.output)

if __name__ == "__main__":
    main()
