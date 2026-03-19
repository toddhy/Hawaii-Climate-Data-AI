import tiledb
import json
import numpy as np
import rasterio

def get_metadata(array_uri):
    with tiledb.DenseArray(array_uri, mode='r') as array:
        meta = {
            "transform": json.loads(array.meta["transform"]),
            "crs": array.meta["crs"],
            "nodata": array.meta["nodata"],
            "width": array.meta["width"],
            "height": array.meta["height"],
            "time_mapping": json.loads(array.meta["time_mapping"])
        }
    return meta

def get_data_for_month(array_uri, date_str):
    """
    Retrieves the 2D geospatial array for a specific month.
    """
    with tiledb.DenseArray(array_uri, mode='r') as array:
        time_mapping = json.loads(array.meta["time_mapping"])
        if date_str not in time_mapping:
            raise ValueError(f"Date {date_str} not found in array metadata.")
        
        time_index = time_mapping[date_str]
        
        # TileDB slicing is highly efficient since it only fetches the needed blocks
        data = array[time_index, :, :]["value"]
        
        # Replace the fill value inside TileDB with numpy NaNs for easier plotting
        nodata_val = array.meta["nodata"]
        if not np.isnan(nodata_val):
            data[data == nodata_val] = np.nan
            
        return data

def get_timeseries_for_pixel(array_uri, y, x):
    """
    Retrieves the temporal slice (time series) for a specific pixel coordinate.
    """
    with tiledb.DenseArray(array_uri, mode='r') as array:
        # Slice across the time dimension for a single (y, x)
        data = array[:, y, x]["value"]
        time_mapping = json.loads(array.meta["time_mapping"])
        
        # Invert mapping to return {date: value}
        inverted_mapping = {v: k for k, v in time_mapping.items()}
        
        series = {}
        for idx, val in enumerate(data):
            if idx in inverted_mapping:
                series[inverted_mapping[idx]] = float(val)
        return series

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Query a TileDB Array containing Monthly Rasters")
    parser.add_argument("--array_uri", required=True, help="Path/URI for the TileDB array")
    parser.add_argument("--month", help="Month to query (e.g., '2022-01')")
    args = parser.parse_args()
    
    if args.month:
        try:
            data = get_data_for_month(args.array_uri, args.month)
            print(f"Extracted shape for {args.month}: {data.shape}")
            print(f"Min Data Value: {np.nanmin(data)}")
            print(f"Max Data Value: {np.nanmax(data)}")
        except Exception as e:
            print(f"Error querying data: {e}")
    else:
        meta = get_metadata(args.array_uri)
        print(f"--- TileDB Array Metadata ---")
        print(f"Shape: (time: {len(meta['time_mapping'])}, y: {meta['height']}, x: {meta['width']})")
        print(f"CRS: {meta['crs']}")
        print(f"Stored Months: {sorted(list(meta['time_mapping'].keys()))}")
