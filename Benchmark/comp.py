#!/usr/bin/env python3
"""
Compare segment counts between Gemini benchmark and total_20_vid_pred predictions.
"""

import os
import json
import csv


def load_json_segments(file_path):
    """Load segments from a JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                return len(data)
            return 0
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None


def load_csv_segments(file_path):
    """Load segments from a CSV file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            return len(rows)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None


def main():
    # Define paths
    gemini_dir = "/home/znyd/hacking/edu-cut/Benchmark/gemini_benchmark/predicted"
    total_20_dir = "/home/znyd/hacking/edu-cut/Benchmark/total_20_vid_pred/predicted"
    
    # Get all video IDs from both directories
    gemini_files = {os.path.splitext(f)[0]: f for f in os.listdir(gemini_dir) if f.endswith('.json')}
    total_20_files = {os.path.splitext(f)[0]: f for f in os.listdir(total_20_dir) if f.endswith('.csv')}
    
    # Combine all video IDs
    all_video_ids = sorted(set(gemini_files.keys()) | set(total_20_files.keys()))
    
    # Compare segments
    comparison_data = []
    total_gemini = 0
    total_20_pred = 0
    
    for video_id in all_video_ids:
        gemini_count = None
        total_20_count = None
        
        # Load Gemini segments
        if video_id in gemini_files:
            gemini_path = os.path.join(gemini_dir, gemini_files[video_id])
            gemini_count = load_json_segments(gemini_path)
            if gemini_count is not None:
                total_gemini += gemini_count
        
        # Load total_20_vid_pred segments
        if video_id in total_20_files:
            total_20_path = os.path.join(total_20_dir, total_20_files[video_id])
            total_20_count = load_csv_segments(total_20_path)
            if total_20_count is not None:
                total_20_pred += total_20_count
        
        # Calculate difference
        diff = None
        if gemini_count is not None and total_20_count is not None:
            diff = gemini_count - total_20_count
        
        # Status indicator
        status = ""
        if gemini_count is None:
            status = "Missing in Gemini"
        elif total_20_count is None:
            status = "Missing in total_20"
        elif gemini_count == total_20_count:
            status = "Match"
        else:
            status = "Mismatch"
        
        comparison_data.append({
            'video_id': video_id,
            'gemini': gemini_count,
            'total_20': total_20_count,
            'diff': diff,
            'status': status
        })
    
    # Print comparison table
    print("\n" + "=" * 100)
    print("SEGMENT COUNT COMPARISON: Gemini vs Total_20_vid_pred")
    print("=" * 100 + "\n")
    
    # Print header
    print(f"{'Video ID':<20} {'Gemini Segments':>18} {'Total_20 Segments':>18} {'Difference':>12} {'Status':<20}")
    print("-" * 100)
    
    for row in comparison_data:
        gemini_str = str(row['gemini']) if row['gemini'] is not None else "N/A"
        total_20_str = str(row['total_20']) if row['total_20'] is not None else "N/A"
        diff_str = str(row['diff']) if row['diff'] is not None else "N/A"
        
        print(f"{row['video_id']:<20} {gemini_str:>18} {total_20_str:>18} {diff_str:>12} {row['status']:<20}")
    
    print("-" * 100)
    
    # Summary
    print("\n" + "=" * 100)
    print("SUMMARY")
    print("=" * 100)
    print(f"Total videos compared: {len(all_video_ids)}")
    print(f"Videos in Gemini benchmark: {len(gemini_files)}")
    print(f"Videos in total_20_vid_pred: {len(total_20_files)}")
    print(f"\nTotal segments in Gemini: {total_gemini}")
    print(f"Total segments in total_20_vid_pred: {total_20_pred}")
    print(f"Overall difference: {total_gemini - total_20_pred}")
    
    # Count matches/mismatches
    matches = sum(1 for row in comparison_data if row['status'] == "Match")
    mismatches = sum(1 for row in comparison_data if row['status'] == "Mismatch")
    missing = sum(1 for row in comparison_data if "Missing" in row['status'])
    
    print(f"\nMatches: {matches}")
    print(f"Mismatches: {mismatches}")
    print(f"Missing: {missing}")


if __name__ == "__main__":
    main()
