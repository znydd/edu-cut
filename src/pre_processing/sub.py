import csv
import json
import os
import math

def convert_csv_to_segmented_json(csv_path, json_path, interval_seconds=10):
    """
    Reads a subtitle CSV, infers the total video duration, and converts it
    into a JSON object where subtitles are grouped into timed segments.

    Args:
        csv_path (str): The path to the input CSV file.
        json_path (str): The path where the output JSON file will be saved.
        interval_seconds (int): The duration of each time segment in seconds.
    """
    if not os.path.exists(csv_path):
        print(f"Error: CSV file not found at '{csv_path}'")
        return

    print(f"\nProcessing '{csv_path}' with {interval_seconds}-second intervals...")

    # --- Step 1: Process CSV and group subtitles into temporary segments ---
    temp_segmented_data = {}
    video_duration = 0.0
    
    try:
        with open(csv_path, mode='r', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            for row in reader:
                try:
                    start_time = float(row['Start (s)'].strip())
                    end_time = float(row['End (s)'].strip())
                    subtitle = row['Segment'].strip()
                    
                    # Update the total video duration
                    video_duration = max(video_duration, end_time)

                    # MODIFICATION: Group subtitles by the start time of their 10-second segment
                    segment_start_time = int(start_time // interval_seconds) * interval_seconds
                    if segment_start_time not in temp_segmented_data:
                        temp_segmented_data[segment_start_time] = []
                    temp_segmented_data[segment_start_time].append(subtitle)
                    
                except (ValueError, KeyError) as e:
                    print(f"Warning: Skipping malformed row: {row}. Error: {e}")
                    continue

    except Exception as e:
        print(f"An error occurred while reading the CSV file: {e}")
        return

    print(f"Inferred video duration from CSV: {video_duration:.2f} seconds.")

    # --- Step 2: Create the final dictionary with correctly formatted keys ---
    final_data = {}
    # Sort the keys (0, 10, 20, etc.) to ensure chronological order
    for start_time in sorted(temp_segmented_data.keys()):
        # MODIFICATION: Calculate the end of the 10-second segment
        segment_end_time = min(start_time + interval_seconds, video_duration)
        
        # Create the descriptive key, e.g., "10-20s"
        segment_key = f"{start_time}-{math.ceil(segment_end_time)}s"
        
        # Assign the list of subtitles to the correctly formatted key
        final_data[segment_key] = temp_segmented_data[start_time]

    # --- Step 3: Write the final dictionary to the JSON file ---
    try:
        with open(json_path, 'w', encoding='utf-8') as outfile:
            json.dump(final_data, outfile, indent=4)
        print(f"Successfully created segmented JSON file at '{json_path}'")
    except Exception as e:
        print(f"An error occurred while writing the JSON file: {e}")

if __name__ == "__main__":
    # --- Create a dummy CSV for demonstration ---
    input_csv_file = "/home/znyd/hacking/edu-cut/src/pre_processing/downloads/backprop.csv"
    output_json_file = "segmented_subtitles_10s.json"

    # Run the main function with a 10-second interval
    convert_csv_to_segmented_json(input_csv_file, output_json_file, interval_seconds=10)
    
    print("\n--- Content of generated JSON file ---")
    if os.path.exists(output_json_file):
        with open(output_json_file, 'r') as f:
            print(f.read())
