"""
Script to print RELEVANT timestamps (segments NOT in ground_truth.json).
These are the segments that are NOT marked as irrelevant.
"""

import json
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


def get_relevant_segments(csv_path: str, irrelevant_ids: set[int]) -> list[list[int]]:
    """
    Get all segment IDs that are NOT in the irrelevant set, grouped by adjacency.
    Returns list of groups of relevant segment IDs.
    """
    df = pd.read_csv(csv_path)
    all_ids = set(df["id"].tolist())
    relevant_ids = sorted(all_ids - irrelevant_ids)
    
    if not relevant_ids:
        return []
    
    # Group adjacent relevant segments
    groups = []
    current_group = [relevant_ids[0]]
    
    for i in range(1, len(relevant_ids)):
        if relevant_ids[i] == relevant_ids[i-1] + 1:
            current_group.append(relevant_ids[i])
        else:
            groups.append(current_group)
            current_group = [relevant_ids[i]]
    
    groups.append(current_group)
    return groups


def get_group_timestamp(csv_path: str, segment_ids: list[int]) -> tuple[str, str]:
    """
    Get the start and end timestamp for a group of segments.
    Returns (start_time_hms, end_time_hms)
    """
    df = pd.read_csv(csv_path)
    
    first_seg_id = min(segment_ids)
    last_seg_id = max(segment_ids)
    
    first_row = df[df["id"] == first_seg_id]
    last_row = df[df["id"] == last_seg_id]
    
    if first_row.empty or last_row.empty:
        return None, None
    
    first_timestamp = first_row.iloc[0]["timestamp"]
    last_timestamp = last_row.iloc[0]["timestamp"]
    
    start_secs, _ = parse_timestamp(first_timestamp)
    _, end_secs = parse_timestamp(last_timestamp)
    
    return format_seconds_to_hms(start_secs), format_seconds_to_hms(end_secs)


def main():
    base_dir = os.path.dirname(__file__)
    ground_truth_path = os.path.join(base_dir, "ground_truth.json")
    predicted_dir = os.path.join(base_dir, "predicted")
    
    # Videos with partial analysis (not the full video)
    video_duration_notes = {
        "ZujpN1B9bz0": "till 15:00 mins",
        "9t2odwJiHOw": "till 9:25 mins",
        "HwiaWygjups": "till 10:00 mins",
        "3PL2DxXv5u0": "till 10:35 mins",
        "yD1Y1chp5R4": "till 12:00 mins",
        "SKZn2DBQuHs": "till 12:30 mins",
    }
    
    with open(ground_truth_path, "r") as f:
        ground_truth = json.load(f)
    
    for video_id, irrelevant_groups in ground_truth.items():
        csv_path = os.path.join(predicted_dir, f"{video_id}.csv")
        yt_link = f"https://www.youtube.com/watch?v={video_id}"
        
        # Add duration note if available
        duration_note = video_duration_notes.get(video_id, "")
        
        print("=" * 80)
        if duration_note:
            print(f"Video: {yt_link} ({duration_note})")
        else:
            print(f"Video: {yt_link}")
        print("=" * 80)
        
        if not os.path.exists(csv_path):
            print(f"  [CSV not found]")
            print()
            continue
        
        # Flatten irrelevant segment IDs from ground truth
        irrelevant_ids = set(seg_id for group in irrelevant_groups for seg_id in group)
        
        # Get all segment IDs from CSV
        df = pd.read_csv(csv_path)
        all_ids = sorted(df["id"].tolist())
        
        # Get relevant segment IDs (not in ground truth)
        relevant_ids = [seg_id for seg_id in all_ids if seg_id not in irrelevant_ids]
        
        if not relevant_ids:
            print("  [No relevant segments found]")
            print()
            continue
        
        # Print each relevant segment individually
        for seg_id in relevant_ids:
            row = df[df["id"] == seg_id].iloc[0]
            timestamp = row["timestamp"]
            start_secs, end_secs = parse_timestamp(timestamp)
            start_hms = format_seconds_to_hms(start_secs)
            end_hms = format_seconds_to_hms(end_secs)
            print(f"  Segment {seg_id:3d}: {start_hms} - {end_hms}")
        
        print()


if __name__ == "__main__":
    main()



# These are the segments  of this video detect  irrelevant or off-topic on this educational video so when I edit this video for future viewer would not face any unnecessary stuff of a unedited video. Do not include anything 2 or less then 2second

# now find them please out put them as start(HH:MM:SS) - end(HH:MM:SS) with reasoning for that.
# make sure the timing is aligned perfectly.  you will select segment from the given segment not outside of these.