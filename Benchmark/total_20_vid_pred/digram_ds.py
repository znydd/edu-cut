#!/usr/bin/env python3
"""
Benchmark Dataset Statistics Generator

This script analyzes video prediction CSV files to compute dataset statistics:
- Number of videos
- Video length statistics (avg, min, max)
- Segment count statistics (avg, min, max)

Outputs a LaTeX table for easy copy-paste into LaTeX documents.
"""

import os
import csv
import re
from pathlib import Path
from datetime import timedelta


def parse_timestamp(ts: str) -> float:
    """Parse timestamp string like '00:10:35.001' to seconds."""
    pattern = r'(\d{2}):(\d{2}):(\d{2})\.(\d{3})'
    match = re.match(pattern, ts)
    if match:
        hours, minutes, seconds, millis = map(int, match.groups())
        return hours * 3600 + minutes * 60 + seconds + millis / 1000
    return 0.0


def get_video_duration(csv_file: Path) -> float:
    """Get video duration from the last segment's end timestamp."""
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        last_row = None
        for row in reader:
            last_row = row
        
        if last_row and 'timestamp' in last_row:
            # Timestamp format: "00:00:00.000-00:00:07.440"
            ts = last_row['timestamp']
            if '-' in ts:
                end_ts = ts.split('-')[-1]
                return parse_timestamp(end_ts)
    return 0.0


def get_segment_count(csv_file: Path) -> int:
    """Count the number of segments in a CSV file."""
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return sum(1 for _ in reader)


def format_duration(seconds: float) -> str:
    """Format seconds as HH:MM:SS."""
    td = timedelta(seconds=seconds)
    total_seconds = int(td.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def generate_latex_table(stats: dict) -> str:
    """Generate LaTeX table from statistics dictionary (no external packages)."""
    latex = r"""
\begin{table}[htbp]
\centering
\caption{Benchmark Dataset Statistics}
\label{tab:benchmark_stats}
\begin{tabular}{|l|c|}
\hline
\textbf{Metric} & \textbf{Value} \\
\hline
Number of Videos & """ + str(stats['num_videos']) + r""" \\
\hline
\multicolumn{2}{|c|}{\textit{Video Duration}} \\
\hline
Total Duration & """ + stats['total_duration'] + r""" \\
Average Duration & """ + stats['avg_duration'] + r""" \\
Minimum Duration & """ + stats['min_duration'] + r""" \\
Maximum Duration & """ + stats['max_duration'] + r""" \\
\hline
\multicolumn{2}{|c|}{\textit{Segment Count}} \\
\hline
Total Segments & """ + str(stats['total_segments']) + r""" \\
Average Segments & """ + f"{stats['avg_segments']:.1f}" + r""" \\
Minimum Segments & """ + str(stats['min_segments']) + r""" \\
Maximum Segments & """ + str(stats['max_segments']) + r""" \\
\hline
\end{tabular}
\end{table}
"""
    return latex


def main():
    predicted_dir = Path(__file__).parent / "predicted"
    
    if not predicted_dir.exists():
        print(f"Error: Directory not found: {predicted_dir}")
        return
    
    csv_files = list(predicted_dir.glob("*.csv"))
    
    if not csv_files:
        print(f"Error: No CSV files found in {predicted_dir}")
        return
    
    print(f"Found {len(csv_files)} video files")
    print("-" * 50)
    
    # Collect statistics
    video_durations = []
    segment_counts = []
    
    for csv_file in csv_files:
        duration = get_video_duration(csv_file)
        segments = get_segment_count(csv_file)
        
        video_durations.append(duration)
        segment_counts.append(segments)
        
        print(f"{csv_file.name}: {format_duration(duration)} ({segments} segments)")
    
    print("-" * 50)
    
    # Calculate statistics
    stats = {
        'num_videos': len(csv_files),
        'total_duration': format_duration(sum(video_durations)),
        'avg_duration': format_duration(sum(video_durations) / len(video_durations)),
        'min_duration': format_duration(min(video_durations)),
        'max_duration': format_duration(max(video_durations)),
        'total_segments': sum(segment_counts),
        'avg_segments': sum(segment_counts) / len(segment_counts),
        'min_segments': min(segment_counts),
        'max_segments': max(segment_counts),
    }
    
    # Print summary
    print("\n=== Dataset Summary ===")
    print(f"Number of Videos: {stats['num_videos']}")
    print(f"Total Duration: {stats['total_duration']}")
    print(f"Average Duration: {stats['avg_duration']}")
    print(f"Min Duration: {stats['min_duration']}")
    print(f"Max Duration: {stats['max_duration']}")
    print(f"Total Segments: {stats['total_segments']}")
    print(f"Average Segments: {stats['avg_segments']:.1f}")
    print(f"Min Segments: {stats['min_segments']}")
    print(f"Max Segments: {stats['max_segments']}")
    
    # Generate and print LaTeX table
    latex_table = generate_latex_table(stats)
    
    print("\n" + "=" * 50)
    print("LaTeX Table (Copy and paste into your document):")
    print("=" * 50)
    print(latex_table)


if __name__ == "__main__":
    main()
