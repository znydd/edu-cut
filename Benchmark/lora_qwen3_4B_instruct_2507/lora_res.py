"""
Accuracy metrics calculation for irrelevant segment prediction.
Compares LoRA fine-tuned model predictions against ground truth.

Compares predicted irrelevant segments (from classifier + filtering) against ground truth.
Metrics: Precision, Recall, F1-Score, Accuracy (per video and overall)
"""

import json
import os
import sys

import pandas as pd

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from test.viz.visualizer import (
    _filter_irrelevant_segments,
    _parse_classification,
    _parse_timestamp,
    _get_segment_duration,
)


def get_predicted_irrelevant_segments(csv_path: str) -> list[list[int]]:
    """
    Extract predicted irrelevant segment groups from a classified CSV file.
    Uses the same filtering and grouping logic as the visualizer.
    
    Returns: 2D list of segment IDs grouped together
    """
    classified_df = pd.read_csv(csv_path)
    
    # Extract all segments with classification
    segments = []
    for _, row in classified_df.iterrows():
        raw_timestamp = row["timestamp"]
        class_resp = str(row["class"])

        try:
            start_secs, end_secs = _parse_timestamp(raw_timestamp)
        except (ValueError, IndexError):
            continue

        classification = _parse_classification(class_resp)
        if classification is None:
            continue

        segments.append({
            "id": row["id"],
            "start": start_secs,
            "end": end_secs,
            "duration": end_secs - start_secs,
            "classification": classification,
        })

    # Apply filtering rules (same as visualizer)
    irrelevant_segments = _filter_irrelevant_segments(segments)
    
    # Group adjacent segments
    if not irrelevant_segments:
        return []
    
    groups = []
    current_group = [irrelevant_segments[0]["id"]]
    current_end = irrelevant_segments[0]["end"]

    for i in range(1, len(irrelevant_segments)):
        seg = irrelevant_segments[i]
        if abs(current_end - seg["start"]) < 0.1:  # Adjacent
            current_group.append(seg["id"])
            current_end = seg["end"]
        else:
            groups.append(current_group)
            current_group = [seg["id"]]
            current_end = seg["end"]

    groups.append(current_group)
    return groups


def flatten_groups(groups: list[list[int]]) -> set[int]:
    """Flatten 2D list of groups to a flat set of segment IDs."""
    return set(seg_id for group in groups for seg_id in group)


def get_total_segments(csv_path: str) -> int:
    """Get total number of segments in the CSV file."""
    df = pd.read_csv(csv_path)
    return len(df)


def calculate_metrics(
    pred_irrelevant: set[int],
    gt_irrelevant: set[int],
    total_segments: int
) -> dict:
    """
    Calculate precision, recall, F1, accuracy for irrelevant segment prediction.
    
    - True Positive (TP): Predicted irrelevant AND actually irrelevant
    - False Positive (FP): Predicted irrelevant BUT actually relevant
    - True Negative (TN): Predicted relevant AND actually relevant
    - False Negative (FN): Predicted relevant BUT actually irrelevant
    """
    all_segments = set(range(total_segments))
    
    # Ground truth sets
    gt_relevant = all_segments - gt_irrelevant
    
    # Predicted sets
    pred_relevant = all_segments - pred_irrelevant
    
    # Confusion matrix values
    tp = len(pred_irrelevant & gt_irrelevant)  # Correctly predicted irrelevant
    fp = len(pred_irrelevant & gt_relevant)    # Wrongly predicted as irrelevant
    tn = len(pred_relevant & gt_relevant)      # Correctly predicted relevant
    fn = len(pred_relevant & gt_irrelevant)    # Missed irrelevant (predicted as relevant)
    
    # Metrics
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    accuracy = (tp + tn) / total_segments if total_segments > 0 else 0.0
    
    return {
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "accuracy": accuracy,
        "total_segments": total_segments,
        "gt_irrelevant_count": len(gt_irrelevant),
        "pred_irrelevant_count": len(pred_irrelevant),
    }


def main():
    # Paths
    base_dir = os.path.dirname(__file__)
    # Use ground truth from total_20_vid_pred folder
    ground_truth_path = os.path.join(
        os.path.dirname(base_dir), 
        "total_20_vid_pred", 
        "ground_truth.json"
    )
    predicted_dir = os.path.join(base_dir, "predicted")
    
    # Load ground truth
    with open(ground_truth_path, "r") as f:
        ground_truth = json.load(f)
    
    # Get available predicted files
    available_videos = set()
    if os.path.exists(predicted_dir):
        for filename in os.listdir(predicted_dir):
            if filename.endswith(".csv"):
                video_id = filename.replace(".csv", "")
                available_videos.add(video_id)
    
    print("=" * 80)
    print("LORA QWEN3 4B INSTRUCT - IRRELEVANT SEGMENT PREDICTION METRICS")
    print("=" * 80)
    print(f"Ground Truth: {ground_truth_path}")
    print(f"Predictions: {predicted_dir}")
    print(f"Available videos: {len(available_videos)} / {len(ground_truth)}")
    print()
    
    all_results = []
    
    # Aggregate confusion matrix
    total_tp, total_fp, total_tn, total_fn = 0, 0, 0, 0
    total_segments_all = 0
    
    # Only process videos that exist in both ground truth and predictions
    for video_id, gt_groups in ground_truth.items():
        if video_id not in available_videos:
            continue  # Skip videos without predictions
            
        csv_path = os.path.join(predicted_dir, f"{video_id}.csv")
        
        if not os.path.exists(csv_path):
            print(f"[SKIP] {video_id}: CSV not found")
            continue
        
        # Get predicted groups
        pred_groups = get_predicted_irrelevant_segments(csv_path)
        
        # Flatten to sets of segment IDs
        pred_irrelevant = flatten_groups(pred_groups)
        gt_irrelevant = flatten_groups(gt_groups)
        
        # Get total segments
        total_segs = get_total_segments(csv_path)
        
        # Calculate metrics
        metrics = calculate_metrics(pred_irrelevant, gt_irrelevant, total_segs)
        metrics["video_id"] = video_id
        metrics["gt_groups"] = gt_groups
        metrics["pred_groups"] = pred_groups
        
        all_results.append(metrics)
        
        # Aggregate
        total_tp += metrics["tp"]
        total_fp += metrics["fp"]
        total_tn += metrics["tn"]
        total_fn += metrics["fn"]
        total_segments_all += total_segs
        
        # Print per-video results
        print(f"Video: {video_id}")
        print(f"  Segments: {total_segs} | GT Irrelevant: {metrics['gt_irrelevant_count']} | Pred Irrelevant: {metrics['pred_irrelevant_count']}")
        print(f"  TP: {metrics['tp']} | FP: {metrics['fp']} | TN: {metrics['tn']} | FN: {metrics['fn']}")
        print(f"  Precision: {metrics['precision']:.4f} | Recall: {metrics['recall']:.4f} | F1: {metrics['f1']:.4f} | Accuracy: {metrics['accuracy']:.4f}")
        print()
    
    if not all_results:
        print("No matching videos found between ground truth and predictions!")
        return
    
    # Overall metrics
    print("=" * 80)
    print("OVERALL METRICS (Micro-averaged)")
    print("=" * 80)
    
    overall_precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
    overall_recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0
    overall_f1 = 2 * overall_precision * overall_recall / (overall_precision + overall_recall) if (overall_precision + overall_recall) > 0 else 0.0
    overall_accuracy = (total_tp + total_tn) / total_segments_all if total_segments_all > 0 else 0.0
    
    print(f"Videos Evaluated: {len(all_results)}")
    print(f"Total Segments: {total_segments_all}")
    print(f"TP: {total_tp} | FP: {total_fp} | TN: {total_tn} | FN: {total_fn}")
    print(f"Precision: {overall_precision:.4f}")
    print(f"Recall: {overall_recall:.4f}")
    print(f"F1-Score: {overall_f1:.4f}")
    print(f"Accuracy: {overall_accuracy:.4f}")
    print()
    
    # Macro-averaged metrics
    if all_results:
        macro_precision = sum(r["precision"] for r in all_results) / len(all_results)
        macro_recall = sum(r["recall"] for r in all_results) / len(all_results)
        macro_f1 = sum(r["f1"] for r in all_results) / len(all_results)
        macro_accuracy = sum(r["accuracy"] for r in all_results) / len(all_results)
        
        print("=" * 80)
        print("OVERALL METRICS (Macro-averaged)")
        print("=" * 80)
        print(f"Precision: {macro_precision:.4f}")
        print(f"Recall: {macro_recall:.4f}")
        print(f"F1-Score: {macro_f1:.4f}")
        print(f"Accuracy: {macro_accuracy:.4f}")


if __name__ == "__main__":
    main()
