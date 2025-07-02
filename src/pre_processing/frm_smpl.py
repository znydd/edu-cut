import os
import json
import math
from PIL import Image
import imagehash
import imageio

def extract_unique_frames(video_path, output_dir, similarity_threshold=15, interval_seconds=10):
    """
    Extracts unique frames from a video and generates a JSON metadata file
    grouping frames into accurately timed segments based on video duration.

    Args:
        video_path (str): The full path to the input video file.
        output_dir (str): The path to the directory where frames will be saved.
        similarity_threshold (int): The threshold for hash comparison. A lower
                                    value means frames must be more similar to
                                    be considered duplicates. Default is 5.
        interval_seconds (int): The duration of each time segment in seconds.
    """
    # --- 1. Setup and Validation ---
    print(f"Starting frame extraction for '{video_path}'...")

    if not os.path.exists(video_path):
        print(f"Error: Video file not found at '{video_path}'")
        return

    os.makedirs(output_dir, exist_ok=True)
    print(f"Frames will be saved in '{output_dir}'")

    # --- 2. Open Video and Get Metadata ---
    try:
        reader = imageio.get_reader(video_path)
    except Exception as e:
        print(f"Error opening video file with imageio: {e}")
        print("Please ensure FFmpeg is installed and accessible on your system.")
        print("You can often install it by running: pip install imageio[ffmpeg]")
        return
        
    meta_data = reader.get_meta_data()
    fps = meta_data.get('fps', 30)
    
    # Get total video duration directly from metadata
    video_duration = meta_data.get('duration')
    if video_duration is None:
        # Fallback calculation if duration is not in metadata
        video_duration = reader.count_frames() / fps
    print(f"Detected video duration: {video_duration:.2f} seconds.")
    
    # Process one frame per second
    frame_interval = int(round(fps))

    # --- 3. Frame Extraction Loop ---
    saved_frame_count = 0
    last_hash = None
    
    # Use a temporary dict with integer keys for efficiency
    temp_metadata = {}
    
    # Iterate through each frame in the video
    for frame_num, frame in enumerate(reader):
        # --- 4. Process Frame at ~1 FPS Interval ---
        if frame_num % frame_interval == 0:
            pil_img = Image.fromarray(frame)
            current_hash = imagehash.phash(pil_img)

            # --- 5. Check for Uniqueness ---
            if last_hash is None or (current_hash - last_hash) > similarity_threshold:
                filename = f"frame_{saved_frame_count:05d}.png"
                output_path = os.path.join(output_dir, filename)

                imageio.imwrite(output_path, frame)
                
                current_time_sec = frame_num / fps
                print(f"Saved unique frame: {filename} (at video time ~{current_time_sec:.2f}s)")

                # MODIFICATION: Logic to add filename to the correct 10-second segment
                segment_start_time = int(current_time_sec // interval_seconds) * interval_seconds
                if segment_start_time not in temp_metadata:
                    temp_metadata[segment_start_time] = []
                temp_metadata[segment_start_time].append(filename)
                
                last_hash = current_hash
                saved_frame_count += 1
                
    # --- 6. Cleanup & Finalization ---
    reader.close()
    
    # Create final metadata with correctly formatted keys
    final_metadata = {}
    for start_time in sorted(temp_metadata.keys()):
        # MODIFICATION: Calculate the end time for the 10-second interval
        segment_end_time = min(start_time + interval_seconds, video_duration)
        
        # Create the human-readable key (e.g., "10-20s")
        segment_key = f"{start_time}-{math.ceil(segment_end_time)}s"
        
        final_metadata[segment_key] = temp_metadata[start_time]

    # Write the final metadata dictionary to a JSON file
    metadata_path = os.path.join(output_dir, "metadata_10s.json")
    try:
        with open(metadata_path, 'w') as f:
            json.dump(final_metadata, f, indent=4)
        print(f"\nSuccessfully created metadata file at '{metadata_path}'")
    except Exception as e:
        print(f"\nError writing metadata file: {e}")
    
    print("\nExtraction complete.")
    print(f"Total unique frames saved: {saved_frame_count}")


if __name__ == "__main__":

    # --- Run the main function ---
    video_path = '/home/znyd/hacking/edu-cut/src/pre_processing/downloads/video/loss_func_vid.mp4'
    output_dir = "vid_frames"
    threshold = 15

    # The function will now use its default 10-second interval
    extract_unique_frames(video_path, output_dir, threshold)

    # --- Print the resulting JSON content ---
    result_json_path = os.path.join(output_dir, "metadata_10s.json")
    if os.path.exists(result_json_path):
        print(f"\n--- Content of generated JSON file '{result_json_path}' ---")
        with open(result_json_path, 'r') as f:
            print(f.read())
