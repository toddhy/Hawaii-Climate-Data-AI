import os
import argparse
import shutil

# Hardcoded directory to search in
SEARCH_DIRECTORY = r"C:\SCIPE\HCDP-data-for-AI\HCDP_PublicationScraper\downloads"  # Change this to your desired directory path

def search_files(substring, directory):
    """
    Searches for a substring in all .txt files in the specified directory.
    Prints the filename if the substring is found.
    Returns a list of absolute paths to matching files.
    """
    matches = []
    if not os.path.isdir(directory):
        print(f"Error: Directory '{directory}' does not exist.")
        return matches

    for filename in os.listdir(directory):
        if filename.endswith(".txt"):
            filepath = os.path.join(directory, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    if substring in f.read():
                        print(filename)
                        matches.append(os.path.abspath(filepath))
            except Exception as e:
                print(f"Could not read file {filename}: {e}")
    
    if not matches:
        print(f"No matches found for '{substring}' in {directory}")
    
    return matches

def copy_matches(matches, destination_dir):
    """
    Copies matching files to the destination directory.
    Skips files that already exist in the destination.
    """
    if not os.path.exists(destination_dir):
        os.makedirs(destination_dir)
        print(f"Created directory: {destination_dir}")

    count = 0
    skipped = 0
    for filepath in matches:
        filename = os.path.basename(filepath)
        dest_path = os.path.join(destination_dir, filename)
        
        if os.path.exists(dest_path):
            skipped += 1
            continue
            
        try:
            shutil.copy2(filepath, dest_path)
            count += 1
        except Exception as e:
            print(f"Error copying {filename}: {e}")
    
    print(f"Copied {count} files to '{destination_dir}'. (Skipped {skipped} already existing files)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Search for a substring in text files and optionally copy matches.")
    parser.add_argument("substring", help="The substring to search for.")
    
    args = parser.parse_args()
    
    matching_files = search_files(args.substring, SEARCH_DIRECTORY)
    
    if matching_files:
        choice = input(f"\nFound {len(matching_files)} matches. Copy them to 'matches' directory? (y/n): ").strip().lower()
        if choice == 'y':
            # Create 'matches' directory in the current working directory
            copy_matches(matching_files, "matches")
        else:
            print("Copy cancelled.")
