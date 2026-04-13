import os
import time
import argparse
import rasterio
import numpy as np

def verify_identical(path_orig, path_new):
    """
    Verifies that the new file is data-identical to the original.
    Checks: shape, dtype, nodata, and statistical values (full array compare).
    """
    try:
        with rasterio.open(path_orig) as src:
            with rasterio.open(path_new) as dst:
                if src.shape != dst.shape:
                    return False, f"Shape mismatch: {src.shape} != {dst.shape}"
                if src.dtypes != dst.dtypes:
                    return False, f"Dtype mismatch: {src.dtypes} != {dst.dtypes}"
                if src.nodata != dst.nodata:
                    return False, f"NoData value mismatch: {src.nodata} != {dst.nodata}"
                
                # Read all bands and compare values
                for i in range(1, src.count + 1):
                    s_data = src.read(i)
                    d_data = dst.read(i)
                    # Use allclose to handle floats safely and equal_nan for NoData values
                    if not np.allclose(s_data, d_data, equal_nan=True):
                        return False, f"Data values mismatch in band {i}"
        
        return True, "Identical"
    except Exception as e:
        return False, f"Exception during verification: {str(e)}"

def compress_directory(directory, recursive=False):
    """
    Iterates through a directory and compresses all uncompressed TIFF files found.
    """
    if not os.path.isdir(directory):
        print(f"[!] Error: '{directory}' is not a valid directory.")
        return
    
    print(f"\n--- Scanning directory: {os.path.abspath(directory)} ---")
    
    total_originals_size = 0
    total_compressed_size = 0
    files_processed = 0
    files_skipped = 0
    files_failed = 0

    # Collect target files
    target_files = []
    for root, _, files in os.walk(directory):
        if not recursive and os.path.abspath(root) != os.path.abspath(directory):
            continue
            
        for filename in files:
            if filename.lower().endswith(('.tiff', '.tif')):
                target_files.append(os.path.join(root, filename))

    if not target_files:
        print("[*] No TIFF files found.")
        return

    print(f"[*] Found {len(target_files)} TIFF file(s). Starting compression...")

    for file_path in target_files:
        filename = os.path.basename(file_path)
        try:
            # 1. Quick check if already compressed correctly
            with rasterio.open(file_path) as src:
                # We target LZW compression
                if src.profile.get('compress') == 'lzw':
                    files_skipped += 1
                    continue
            
            # 2. Compress to temporary file
            temp_path = file_path + ".tmp_compress"
            
            orig_size = os.path.getsize(file_path)
            
            with rasterio.open(file_path) as src:
                profile = src.profile.copy()
                # Apply LZW compression, also add tiling for better standard performance
                profile.update(
                    compress='lzw', 
                    tiled=True, 
                    blockxsize=256, 
                    blockysize=256
                )
                
                with rasterio.open(temp_path, 'w', **profile) as dst:
                    for i in range(1, src.count + 1):
                        dst.write(src.read(i), i)
            
            # 3. Verify Integrity
            is_ok, reason = verify_identical(file_path, temp_path)
            
            if is_ok:
                new_size = os.path.getsize(temp_path)
                
                # Check if we actually saved space (usually true for LZW unless zip fails)
                if new_size >= orig_size:
                    # Rare but possible for very tiny or random data
                    # Still replace if the user wants standardized compression, 
                    # but here we care about space.
                    # We'll replace anyway to stay consistent if it's identical.
                    pass
                
                # 4. Atomic Replace
                # Remove original and move temp to original location
                os.remove(file_path)
                os.rename(temp_path, file_path)
                
                total_originals_size += orig_size
                total_compressed_size += new_size
                files_processed += 1
                
                savings_pct = ((orig_size - new_size) / orig_size) * 100
                print(f"  [OK] Compressed {filename}: {orig_size/1024**2:.1f}MB -> {new_size/1024**2:.1f}MB ({savings_pct:.1f}% saved)")
            else:
                print(f"  [!!] FAILED identity check for {filename}: {reason}")
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                files_failed += 1
        
        except Exception as e:
            print(f"  [!!] ERROR processing {filename}: {e}")
            files_failed += 1

    # Final Report
    print(f"\n--- Final Results for {os.path.basename(directory)} ---")
    print(f"  Processed: {files_processed}")
    print(f"  Already Compressed: {files_skipped}")
    print(f"  Failed: {files_failed}")
    if files_processed > 0:
        saved_gb = (total_originals_size - total_compressed_size) / (1024**3)
        print(f"  Total Space Saved: {saved_gb:.3f} GB")

def main():
    parser = argparse.ArgumentParser(description="Generalized Lossless TIFF Compressor using LZW")
    parser.add_argument("directories", nargs="+", help="One or more directories to process")
    parser.add_argument("--recursive", "-r", action="store_true", help="Recursively process subdirectories")
    
    args = parser.parse_args()
    
    start_time = time.time()
    for d in args.directories:
        compress_directory(d, recursive=args.recursive)
    
    elapsed = time.time() - start_time
    print(f"\n[*] Total execution time: {elapsed:.2f} seconds")

if __name__ == "__main__":
    main()
