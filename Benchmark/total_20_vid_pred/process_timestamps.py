import json
import csv
import os
import glob
import re

def parse_timestamp_range(ts_range):
    """Parses '00:00:00.000-00:00:07.440' into ('00:00:00.000', '00:00:07.440')"""
    parts = ts_range.split('-')
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    return None, None

def merge_timestamps(indices, id_to_ts):
    """Given a list of indices and a mapping of id -> (start, end), return a merged timestamp string."""
    if not indices:
        return None
    
    # Sort indices just in case, though they are usually sequential in ground truth groups
    sorted_indices = sorted(indices)
    
    start_ts = None
    end_ts = None
    
    for idx in sorted_indices:
        if idx in id_to_ts:
            curr_start, curr_end = id_to_ts[idx]
            if start_ts is None:
                start_ts = curr_start
            end_ts = curr_end
            
    if start_ts and end_ts:
        return f"{start_ts}-{end_ts}"
    return None

def process():
    base_dir = "/home/znyd/hacking/edu-cut/Benchmark/total_20_vid_pred"
    gt_file = os.path.join(base_dir, "ground_truth.json")
    pred_dir = os.path.join(base_dir, "predicted")
    output_gt_ts = os.path.join(base_dir, "ground_truth_ts.json")
    output_pred_ts = os.path.join(base_dir, "predicted_ts.json")

    with open(gt_file, 'r') as f:
        ground_truth = json.load(f)

    gt_ts_dict = {}
    pred_ts_dict = {}

    for video_id, gt_indices_list in ground_truth.items():
        csv_file = os.path.join(pred_dir, f"{video_id}.csv")
        if not os.path.exists(csv_file):
            print(f"Warning: CSV for {video_id} not found at {csv_file}")
            continue

        id_to_ts = {}
        relevant_indices = []
        
        with open(csv_file, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    idx = int(row['id'])
                    ts_range = row['timestamp']
                    cls = row['class']
                    
                    id_to_ts[idx] = parse_timestamp_range(ts_range)
                    
                    # For prediction: check if "Relevant"
                    if "Relevant" in cls:
                        relevant_indices.append(idx)
                except (ValueError, KeyError):
                    continue

        # Process Ground Truth
        gt_timestamps = []
        for group in gt_indices_list:
            merged = merge_timestamps(group, id_to_ts)
            if merged:
                gt_timestamps.append(merged)
        gt_ts_dict[video_id] = gt_timestamps

        # Process Predictions (group contiguous indices)
        pred_timestamps = []
        if relevant_indices:
            relevant_indices.sort()
            current_group = [relevant_indices[0]]
            for i in range(1, len(relevant_indices)):
                if relevant_indices[i] == relevant_indices[i-1] + 1:
                    current_group.append(relevant_indices[i])
                else:
                    merged = merge_timestamps(current_group, id_to_ts)
                    if merged:
                        pred_timestamps.append(merged)
                    current_group = [relevant_indices[i]]
            # Add last group
            merged = merge_timestamps(current_group, id_to_ts)
            if merged:
                pred_timestamps.append(merged)
        
        pred_ts_dict[video_id] = pred_timestamps

    # Save outputs
    with open(output_gt_ts, 'w') as f:
        json.dump(gt_ts_dict, f, indent=4)
    
    with open(output_pred_ts, 'w') as f:
        json.dump(pred_ts_dict, f, indent=4)

    print(f"Successfully created {output_gt_ts} and {output_pred_ts}")

if __name__ == "__main__":
    process()
