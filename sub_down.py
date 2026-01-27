#!/usr/bin/env python3
"""
Simple script to download YouTube SRT subtitles by video ID with optional time range.

Configure the variables in main() to set:
- video_id: YouTube video ID
- output_path: Where to save the SRT file
- start_time: Start time in "HH:MM:SS" format (or None for beginning)
- end_time: End time in "HH:MM:SS" format (or None for full video)
"""

import sys
from pathlib import Path

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import SRTFormatter


def time_to_seconds(time_str: str) -> float:
    """
    Convert time string in HH:MM:SS or MM:SS format to seconds.

    Args:
        time_str: Time string like "01:30:45" or "10:30"

    Returns:
        Total seconds as float
    """
    parts = time_str.split(":")
    if len(parts) == 3:
        h, m, s = parts
        return int(h) * 3600 + int(m) * 60 + float(s)
    elif len(parts) == 2:
        m, s = parts
        return int(m) * 60 + float(s)
    else:
        return float(time_str)


def seconds_to_time(seconds: float) -> str:
    """Convert seconds to HH:MM:SS format."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def download_srt(
    video_id: str,
    output_path: str = None,
    start_time: str = None,
    end_time: str = None,
) -> Path:
    """
    Download YouTube transcript as SRT file with optional time range filtering.

    Args:
        video_id: YouTube video ID
        output_path: Optional custom output path (default: {video_id}.srt)
        start_time: Start time in "HH:MM:SS" format (None = from beginning)
        end_time: End time in "HH:MM:SS" format (None = until end)

    Returns:
        Path to the saved SRT file
    """
    if output_path is None:
        output_path = Path(f"{video_id}.srt")
    else:
        output_path = Path(output_path)

    # Convert time strings to seconds
    start_sec = time_to_seconds(start_time) if start_time else 0
    end_sec = time_to_seconds(end_time) if end_time else None

    print(f"📥 Fetching transcript for video: {video_id}")

    try:
        ytt_api = YouTubeTranscriptApi()
        transcript = ytt_api.fetch(video_id)

        # Get original duration
        original_count = len(transcript)
        if transcript:
            last_entry = transcript[-1]
            original_duration = last_entry.start + last_entry.duration
            print(
                f"📊 Original: {original_count} entries, {seconds_to_time(original_duration)}"
            )

        # Filter by time range
        if end_sec is not None:
            transcript = [
                entry
                for entry in transcript
                if entry.start >= start_sec and entry.start < end_sec
            ]
            print(f"🔍 Filtered: {start_time or '00:00:00'} → {end_time}")
        elif start_sec > 0:
            transcript = [entry for entry in transcript if entry.start >= start_sec]
            print(f"🔍 Filtered: {start_time} → end")

        formatter = SRTFormatter()
        srt_formatted = formatter.format_transcript(transcript)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(srt_formatted)

        print(f"✅ SRT saved to: {output_path}")
        print(f"📝 Saved entries: {len(transcript)}")

        # Show saved duration info
        if transcript:
            first_entry = transcript[0]
            last_entry = transcript[-1]
            saved_duration = last_entry.start + last_entry.duration - first_entry.start
            print(f"⏱️  Saved duration: {seconds_to_time(saved_duration)}")

        return output_path

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


def main():
    # ============== CONFIGURE HERE ==============
    video_id = "yD1Y1chp5R4"
    output_path = f"/home/znyd/hacking/edu-cut/store/{video_id}/subtitle/{video_id}.srt"

    # Time range in HH:MM:SS format (set to None for no filtering)
    start_time = "00:00:00"  # e.g., "00:00:00" or "00:05:30"
    end_time = "00:12:00"  # e.g., "00:10:00" for first 10 minutes
    # ============================================

    download_srt(video_id, output_path, start_time, end_time)


if __name__ == "__main__":
    main()
