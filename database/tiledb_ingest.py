import os
import glob
import json
import rasterio
import tiledb
import numpy as np

def create_array_if_not_exists(array_uri, template_tiff):
    if tiledb.array_exists(array_uri):
        return True

    print(f"Creating new TileDB array at {array_uri} based on {template_tiff}...")
    with rasterio.open(template_tiff) as src:
        height = src.height
        width = src.width
        transform = src.transform
        crs_wkt = src.crs.to_wkt()
        nodata = src.nodata if src.nodata is not None else np.nan

    # Dimensions: time_index, y (lat), x (lon)
    # Using a dense array since grid data is continuous
    dom = tiledb.Domain(
        tiledb.Dim(name="time_index", domain=(0, 10000), tile=1, dtype=np.int32),
        tiledb.Dim(name="y", domain=(0, height - 1), tile=height, dtype=np.int32),
        tiledb.Dim(name="x", domain=(0, width - 1), tile=width, dtype=np.int32)
    )

    schema = tiledb.ArraySchema(
        domain=dom,
        sparse=False,
        attrs=[tiledb.Attr(name="value", dtype=np.float32, fill=np.nan)]
    )

    tiledb.DenseArray.create(array_uri, schema)
    
    # Store spatial metadata as array metadata for later reprojection/mapping
    with tiledb.DenseArray(array_uri, mode='w') as array:
        # Save Affine transform matrix as list [a,b,c,d,e,f]
        array.meta["transform"] = json.dumps(transform[:6]) 
        array.meta["crs"] = crs_wkt
        array.meta["nodata"] = float(nodata)
        array.meta["width"] = width
        array.meta["height"] = height
        
        # time mapping maps String Date "YYYY-MM" to integer time_index
        array.meta["time_mapping"] = json.dumps({}) 
        array.meta["next_time_index"] = 0

    return True

def ingest_tiffs(input_dir, array_uri):
    tiff_files = glob.glob(os.path.join(input_dir, "*.tiff")) + glob.glob(os.path.join(input_dir, "*.tif"))
    if not tiff_files:
        print(f"No TIFF files found in {input_dir}")
        return

    create_array_if_not_exists(array_uri, tiff_files[0])

    with tiledb.DenseArray(array_uri, mode='r') as array:
        time_mapping = json.loads(array.meta["time_mapping"])
        next_time_index = array.meta["next_time_index"]
        
    dates_to_ingest = []
    paths_to_ingest = []
    
    for tiff_path in sorted(tiff_files):
        filename = os.path.basename(tiff_path)
        date_str = os.path.splitext(filename)[0] # Expects e.g. "2024-01.tiff"
        
        if date_str in time_mapping:
            print(f"Skipping {date_str}, already ingested in array.")
            continue
            
        dates_to_ingest.append(date_str)
        paths_to_ingest.append(tiff_path)

    MAX_FILES = 120
    if len(dates_to_ingest) > MAX_FILES:
        print(f"Limiting to {MAX_FILES} files to bypass Windows TileDB fragment lock bugs and stay in memory.")
        dates_to_ingest = dates_to_ingest[:MAX_FILES]
        paths_to_ingest = paths_to_ingest[:MAX_FILES]
        
    print(f"Loading {len(dates_to_ingest)} files into memory to avoid fragment locks...")
    data_to_ingest = []
    for tiff_path in paths_to_ingest:
        with rasterio.open(tiff_path) as src:
            data_to_ingest.append(src.read(1).astype(np.float32))
            
    print(f"Writing all data sequentially to TileDB at once starting from time_index {next_time_index}...")
    batch_data = np.stack(data_to_ingest)
    
    with tiledb.DenseArray(array_uri, mode='w') as array:
        end_index = next_time_index + len(dates_to_ingest)
        array[int(next_time_index):int(end_index), :, :] = batch_data
        
        for date_str in dates_to_ingest:
            time_mapping[date_str] = int(next_time_index)
            next_time_index += 1
            
        array.meta["time_mapping"] = json.dumps(time_mapping)
        array.meta["next_time_index"] = next_time_index

    # Final summary
    print(f"Successfully finished ingestion. Array {array_uri} now has {next_time_index} time slices.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Ingest TIFFs into a TileDB Array")
    parser.add_argument("--input_dir", required=True, help="Directory containing TIFF files")
    parser.add_argument("--array_uri", required=True, help="Path/URI for the target TileDB array")
    args = parser.parse_args()
    
    ingest_tiffs(args.input_dir, args.array_uri)
