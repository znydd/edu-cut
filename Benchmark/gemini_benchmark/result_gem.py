"""
Accuracy metrics calculation for Gemini irrelevant segment prediction.

Compares Gemini JSON predictions against ground truth.
The segment index is the position in the JSON array (0, 1, 2, ...).
Metrics: Precision, Recall, F1-Score, Accuracy (per video and overall)
"""

import json
import os


def get_predicted_irrelevant_from_json(json_path: str) -> set[int]:
    """
    Extract predicted irrelevant segment indices from Gemini JSON file.
    Segment index = position in the array (0-indexed).
    
    Returns: Set of segment indices classified as Irrelevant
    """
    with open(json_path, "r") as f:
        segments = json.load(f)
    
    irrelevant_ids = set()
    for i, seg in enumerate(segments):
        if seg.get("type") == "Irrelevant":
            irrelevant_ids.add(i)
    
    return irrelevant_ids


def get_total_segments_from_json(json_path: str) -> int:
    """Get total number of segments in the JSON file."""
    with open(json_path, "r") as f:
        segments = json.load(f)
    return len(segments)


def flatten_groups(groups: list[list[int]]) -> set[int]:
    """Flatten 2D list of groups to a flat set of segment IDs."""
    return set(seg_id for group in groups for seg_id in group)


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
    ground_truth_path = os.path.join(os.path.dirname(base_dir), "ground_truth.json")
    predicted_dir = os.path.join(base_dir, "predicted")
    
    # Load ground truth
    with open(ground_truth_path, "r") as f:
        ground_truth = json.load(f)
    
    print("=" * 80)
    print("GEMINI IRRELEVANT SEGMENT PREDICTION - ACCURACY METRICS")
    print("=" * 80)
    print()
    
    all_results = []
    
    # Aggregate confusion matrix
    total_tp, total_fp, total_tn, total_fn = 0, 0, 0, 0
    total_segments_all = 0
    
    # Get all JSON files in predicted directory
    if not os.path.exists(predicted_dir):
        print(f"Predicted directory not found: {predicted_dir}")
        return
    
    json_files = [f for f in os.listdir(predicted_dir) if f.endswith(".json")]
    
    if not json_files:
        print(f"No JSON files found in: {predicted_dir}")
        return
    
    for json_file in sorted(json_files):
        video_id = json_file.replace(".json", "")
        json_path = os.path.join(predicted_dir, json_file)
        
        # Check if video is in ground truth
        if video_id not in ground_truth:
            print(f"[SKIP] {video_id}: Not in ground truth")
            continue
        
        gt_groups = ground_truth[video_id]
        
        # Get predicted irrelevant segments from JSON
        try:
            pred_irrelevant = get_predicted_irrelevant_from_json(json_path)
            total_segs = get_total_segments_from_json(json_path)
        except Exception as e:
            print(f"[ERROR] {video_id}: {e}")
            continue
        
        # Flatten ground truth to set of segment IDs
        gt_irrelevant = flatten_groups(gt_groups)
        
        # Calculate metrics
        metrics = calculate_metrics(pred_irrelevant, gt_irrelevant, total_segs)
        metrics["video_id"] = video_id
        
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
        print("No results to aggregate.")
        return
    
    # Overall metrics
    print("=" * 80)
    print("OVERALL METRICS (Micro-averaged)")
    print("=" * 80)
    
    overall_precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
    overall_recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0
    overall_f1 = 2 * overall_precision * overall_recall / (overall_precision + overall_recall) if (overall_precision + overall_recall) > 0 else 0.0
    overall_accuracy = (total_tp + total_tn) / total_segments_all if total_segments_all > 0 else 0.0
    
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
