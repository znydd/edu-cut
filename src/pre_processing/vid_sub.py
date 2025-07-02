import json
import os

def combine_json_data(frames_json_path, subtitles_json_path, output_json_path):
    """
    Combines JSON data from frame extraction and subtitle generation into a
    single structured JSON file.

    Args:
        frames_json_path (str): Path to the JSON file containing frame data.
        subtitles_json_path (str): Path to the JSON file with subtitle data.
        output_json_path (str): Path for the combined output JSON file.
    """
    print("Starting JSON combination process...")

    # --- 1. Read and Load Input JSON Files ---
    try:
        with open(frames_json_path, 'r', encoding='utf-8') as f:
            frames_data = json.load(f)
        print(f"Successfully loaded frames data from '{frames_json_path}'")
    except FileNotFoundError:
        print(f"Error: Frames JSON file not found at '{frames_json_path}'")
        return
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from '{frames_json_path}'. Check for formatting errors.")
        return

    try:
        with open(subtitles_json_path, 'r', encoding='utf-8') as f:
            subtitles_data = json.load(f)
        print(f"Successfully loaded subtitles data from '{subtitles_json_path}'")
    except FileNotFoundError:
        print(f"Error: Subtitles JSON file not found at '{subtitles_json_path}'")
        return
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from '{subtitles_json_path}'. Check for formatting errors.")
        return

    # --- 2. Combine Data for Each Time Segment ---

    # Get all unique keys (time segments) from both dictionaries
    all_keys = set(frames_data.keys()) | set(subtitles_data.keys())

    # Sort keys chronologically based on the start time (the number before '-')
    # This ensures the final list is in order.
    sorted_keys = sorted(list(all_keys), key=lambda x: int(x.split('-')[0]))
    
    combined_list = []
    for key in sorted_keys:
        # Create a dictionary for the current segment
        segment_data = {
            "time_stamps": key,
            # Use .get(key, []) to safely get the list, or an empty list if the key doesn't exist
            "frames": frames_data.get(key, []),
            "subtitle": subtitles_data.get(key, [])
        }
        combined_list.append(segment_data)

    # --- 3. Write the Combined List to a New JSON File ---
    try:
        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump(combined_list, f, indent=4)
        print(f"\nSuccessfully combined data into '{output_json_path}'")
    except Exception as e:
        print(f"\nAn error occurred while writing the output file: {e}")


if __name__ == "__main__":
    # Define file paths for our dummy data
    frames_file = "/home/znyd/hacking/edu-cut/src/pre_processing/vid_frames/metadata_10s.json"
    subtitles_file = "/home/znyd/hacking/edu-cut/src/pre_processing/segmented_subtitles.json"
    output_file = "combined_output.json"

   
    # --- Run the main combination function ---
    combine_json_data(frames_file, subtitles_file, output_file)

    # --- Print the content of the final combined file ---
    print(f"\n--- Content of '{output_file}' ---")
    if os.path.exists(output_file):
        with open(output_file, 'r') as f:
            print(f.read())

