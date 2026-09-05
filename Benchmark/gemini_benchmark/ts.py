"""
Script to print ALL timestamps of each video segment.
No filtering, just prints every segment with its timestamp.
"""

import os
import pandas as pd


def format_seconds_to_hms(seconds: float) -> str:
    """Convert seconds to HH:MM:SS format."""
    total_secs = int(seconds)
    hours = total_secs // 3600
    minutes = (total_secs % 3600) // 60
    secs = total_secs % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def parse_timestamp(timestamp_str: str) -> tuple[float, float]:
    """Parse '00:01:34.000-00:01:38.500' to (start_seconds, end_seconds)."""
    parts = timestamp_str.split("-")
    start_parts = parts[0].split(":")
    end_parts = parts[1].split(":")

    start_secs = (
        float(start_parts[0]) * 3600
        + float(start_parts[1]) * 60
        + float(start_parts[2])
    )
    end_secs = (
        float(end_parts[0]) * 3600 + float(end_parts[1]) * 60 + float(end_parts[2])
    )
    return start_secs, end_secs


def main():
    # Configure the CSV directory path here
    # csv_dir = "/home/znyd/hacking/edu-cut/Benchmark/gemini_benchmark/predicted"
    csv_dir = "/home/znyd/hacking/edu-cut/Benchmark/total_20_vid_pred/predicted"
    
    # Videos with partial analysis (not the full video)
    video_duration_notes = {
        "ZujpN1B9bz0": "till 15:00 mins",
        "9t2odwJiHOw": "till 9:25 mins",
        "HwiaWygjups": "till 10:00 mins",
        "3PL2DxXv5u0": "till 10:35 mins",
        "yD1Y1chp5R4": "till 12:00 mins",
        "SKZn2DBQuHs": "till 12:30 mins",
    }
    
    if not os.path.exists(csv_dir):
        print(f"Directory not found: {csv_dir}")
        return
    
    # Get all CSV files
    csv_files = sorted([f for f in os.listdir(csv_dir) if f.endswith(".csv")])
    
    if not csv_files:
        print(f"No CSV files found in: {csv_dir}")
        return
    
    for csv_file in csv_files:
        video_id = csv_file.replace(".csv", "")
        csv_path = os.path.join(csv_dir, csv_file)
        yt_link = f"https://www.youtube.com/watch?v={video_id}"
        
        # Add duration note if available
        duration_note = video_duration_notes.get(video_id, "")
        
        print("=" * 80)
        if duration_note:
            print(f"Video: {yt_link} ({duration_note})")
        else:
            print(f"Video: {yt_link}")
        print("ALL SEGMENTS")
        print("=" * 80)
        
        try:
            df = pd.read_csv(csv_path)
        except Exception as e:
            print(f"  [Error reading CSV: {e}]")
            print()
            continue
        
        if df.empty:
            print("  [No segments found]")
            print()
            continue
        
        # Print each segment
        for _, row in df.iterrows():
            seg_id = row["id"]
            timestamp = row["timestamp"]
            
            try:
                start_secs, end_secs = parse_timestamp(timestamp)
                start_hms = format_seconds_to_hms(start_secs)
                end_hms = format_seconds_to_hms(end_secs)
                print(f"  Segment {seg_id:3d}: {start_hms} - {end_hms}")
            except Exception as e:
                print(f"  Segment {seg_id:3d}: [Error parsing timestamp: {timestamp}]")
        
        print()


if __name__ == "__main__":
    main()
