import json
import os

def check_one_piece_missing(json_path):
    if not os.path.exists(json_path):
        print(f"Error: File {json_path} not found.")
        return

    with open(json_path, 'r') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
            return

    found_any = False
    for video_id, segments in data.items():
        for i in range(len(segments) - 1):
            seg1 = segments[i]
            seg2 = segments[i + 1]

            if not seg1 or not seg2:
                continue

            max_val1 = max(seg1)
            min_val2 = min(seg2)

            # Check if there is exactly one integer missing between segments
            if min_val2 - max_val1 == 2:
                missing_val = max_val1 + 1
                print(f"Video ID: {video_id}")
                print(f"  Gap detected between index {i} and {i+1}")
                print(f"  Segment {i}: {seg1}")
                print(f"  Segment {i+1}: {seg2}")
                print(f"  Missing piece: {missing_val}")
                print("-" * 30)
                found_any = True

    if not found_any:
        print("No 'one piece missing' patterns found.")

if __name__ == "__main__":
    base_path = os.path.dirname(os.path.abspath(__file__))
    # Assuming the ground_truth.json is relative to the Benchmark folder if that's where the script is
    # The user provided the path Benchmark/total_20_vid_pred/ground_truth.json
    # If the script is in Benchmark/, the path should be total_20_vid_pred/ground_truth.json
    # However, I will use the full path provided by the user for clarity.
    target_path = "/home/znyd/hacking/edu-cut/Benchmark/total_20_vid_pred/ground_truth.json"
    check_one_piece_missing(target_path)
