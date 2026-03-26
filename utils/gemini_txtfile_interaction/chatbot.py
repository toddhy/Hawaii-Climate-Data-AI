import os
import subprocess
import sys
from google import genai
from google.genai import types

# Get the project root directory (one level up from gemini_chat)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def run_local_script(script_path: str, args: str = "") -> str:
    """
    Executes a local Python script and returns its output.
    
    Args:
        script_path: The path to the .py script relative to the project root (e.g., 'HCDP_API/fetch_station_data.py').
        args: A string containing space-separated command-line arguments (e.g., '19.7 -155.1 5').
    """
    # Force path to be absolute within the project
    full_path = os.path.abspath(os.path.join(PROJECT_ROOT, script_path))
    
    # Security: Verify script exists and is a .py file
    if not os.path.exists(full_path):
        return f"Error: Script not found at {full_path}. Please check the relative path from project root."
    if not full_path.endswith(".py"):
        return "Error: Only .py scripts can be executed."

    # Prompt user for confirmation before running
    print(f"\n>>> GEMINI WANTS TO RUN: python {script_path} {args}")
    confirm = input("Confirm execution? (y/n): ")
    if confirm.lower() != 'y':
        return "Execution cancelled by user."

    # Run in the script's own directory to ensure relative imports and .env work
    script_dir = os.path.dirname(full_path)
    cmd = [sys.executable, full_path]
    if args:
        cmd.extend(args.split())
    
    try:
        print(f"Running in {script_dir}: {' '.join(cmd)}...")
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, cwd=script_dir)
        return f"Output:\n{result.stdout}\nErrors (if any):\n{result.stderr}"
    except subprocess.CalledProcessError as e:
        return f"Error during execution (Exit Code {e.returncode}):\n{e.stderr}\nOutput:\n{e.stdout}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"

def run_chatbot():
    # 1. Initialize Client with Tools
    client = genai.Client()
    MODEL_ID = "gemini-2.0-flash"
    
    # Define the tool configuration
    tools = [run_local_script]

    # 2. Fetch uploaded files (if any)
    print("Fetching active uploaded files...")
    all_files = []
    try:
        for file in client.files.list():
            if file.state.name == 'ACTIVE':
                all_files.append(file)
    except Exception as e:
        print(f"Note: Could not fetch files from API ({e})")

    # 3. Filter and deduplicate files
    EXCLUDE_PATTERNS = ['license', 'readme', 'authors', 'vendor', 'entry_points', '.txt.txt']
    filtered_files = {}
    for f in all_files:
        name_lower = f.display_name.lower()
        if any(pat in name_lower for pat in EXCLUDE_PATTERNS): continue
        if f.display_name not in filtered_files:
            filtered_files[f.display_name] = f

    files = list(filtered_files.values())
    if files:
        print(f"Context optimized: Using {len(files)} uploaded files.")

    # 4. Initialize chat session with tools and system instruction
    chat = client.chats.create(
        model=MODEL_ID,
        config=types.GenerateContentConfig(
            tools=tools,
            system_instruction=f"""You are a local data analysis assistant for the HCDP project.
            Current Project Root: {PROJECT_ROOT}
            
            You HAVE the capability to execute local scripts to perform HCDP tasks.
            
            AVAILABLE SCRIPTS (use these exact strings for `script_path`):
            1. 'HCDP_API/fetch_station_data.py': Downloads rainfall data.
               Args: [lat] [lon] [radius_km]. Example: 19.7 -155.1 5
            2. 'HCDP_API/average_rainfall_map.py': Generates an HTML map.
               No args required.
            3. 'HCDP_API/tiff_visualizer.py': Creates a gridded map from TIFF files.
               Args: Optional --input_dir. Example: --input_dir downloads
            
            GEOLOCATION INFERENCE:
            - If a user mentions a place name (e.g., 'Honolulu', 'Hilo', 'Manoa') without coordinates, you MUST infer the correct latitude and longitude for that location yourself and provide them as arguments to `fetch_station_data.py`.
            - Default radius is 10km unless specified otherwise.
            
            WORKFLOW:
            - When asked to 'fetch', 'download', or 'get' data for a location, call 'HCDP_API/fetch_station_data.py'.
            - When asked to 'map', 'average', or 'visualize stations', call 'HCDP_API/average_rainfall_map.py'.
            - When asked to 'visualize TIFFs', 'create raster map', or 'show gridded rainfall', call 'HCDP_API/tiff_visualizer.py'.
            - If a user asks for both, perform them sequentially.
            """
        )
    )

    print("\n--- CHATBOT READY (Automation Enabled) ---")
    print(f"Project Root: {PROJECT_ROOT}")
    print("Available scripts (path from root):")
    print(" - HCDP_API/fetch_station_data.py [lat] [lon] [radius]")
    print(" - HCDP_API/average_rainfall_map.py")
    print(" - HCDP_API/tiff_visualizer.py [--input_dir DIR]")
    print("Type 'exit' or 'quit' to end the session.\n")

    history_with_files = False

    while True:
        user_input = input("You: ")
        
        if user_input.lower() in ['exit', 'quit']:
            print("Goodbye!")
            break
        
        if not user_input.strip():
            continue

        try:
            # Prepare message
            if not history_with_files and files:
                contents = files + [user_input]
                history_with_files = True
            else:
                contents = [user_input]
            
            # Send message
            response = chat.send_message(contents)
            
            if response.text:
                print(f"\nGemini: {response.text}\n")
            else:
                print("\nGemini finished processing (no text response).\n")

        except Exception as e:
            print(f"Error during chat: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    run_chatbot()
