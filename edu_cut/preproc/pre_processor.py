import csv
import json
import math
import re
import subprocess
from pathlib import Path
from typing import Any

import imagehash
import imageio
import pandas as pd
import yt_dlp
from PIL import Image
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import SRTFormatter
from yt_dlp.utils import DownloadError

from ..storage.store_manager import Storage


class PreProcessor:
    def __init__(self, yt_id: str):
        self.yt_id = yt_id
        self.yt_url = "https://www.youtube.com/watch?v=" + self.yt_id
        self.storage = Storage()
        self._create_yt_store()
        self.silent_gap = 5.0

    def _create_yt_store(self):
        (
            self.yt_dir,
            self.audio_dir,
            self.video_dir,
            self.video_cut_dir,
            self.subtitle_dir,
            self.merged_input_dir,
            self.responses_dir,
        ) = self.storage.create_yt_store_dir(self.yt_id)

    def _get_video_duration(self) -> float:
        video_path = self.video_dir.joinpath(f"{self.yt_id}.mp4")
        if self.storage.exist(video_path):
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v",
                    "error",
                    "-show_entries",
                    "format=duration",
                    "-of",
                    "default=noprint_wrappers=1:nokey=1",
                    video_path,
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            return float(result.stdout.strip())
        else:
            print("Video does not exist ❌")
            return float(0.00)

    def _time_to_seconds(self, time_str):
        """Convert 'HH:MM:SS,mmm' to total seconds (float)."""
        h, m, s_ms = time_str.split(":")
        s, ms = s_ms.split(",")
        return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000

    def _parse_srt(self, srt_path):
        """Parse SRT into list of (start_seconds, end_seconds, text)."""
        with open(srt_path, "r", encoding="utf-8") as f:
            content = f.read()

        blocks = re.split(r"\n\s*\n", content.strip())
        subtitles = []

        for block in blocks:
            lines = block.strip().split("\n")
            if len(lines) >= 3:
                time_line = lines[1]
                match = re.match(
                    r"(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})",
                    time_line,
                )
                if match:
                    start, end = match.groups()
                    start_sec = round(self._time_to_seconds(start), 3)
                    end_sec = round(self._time_to_seconds(end), 4)
                    text = " ".join(lines[2:]).replace("\n", " ").strip()
                    subtitles.append((start_sec, end_sec, text))
        return subtitles

    def _srt_to_csv(self, srt_path, csv_path):
        """Convert .srt to .csv with Start, End (in seconds), and Segment."""
        subtitles = self._parse_srt(srt_path)
        with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Start", "End", "Segment"])
            writer.writerows(subtitles)
        print(f"✅ CSV created successfully at: {csv_path}")

    def download_video(self) -> None:
        video_opts: dict[str, Any] = {
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "outtmpl": str(Path(self.video_dir) / f"{self.yt_id}.%(ext)s"),
            "quiet": False,
        }
        video_file = self.video_dir.joinpath(f"{self.yt_id}.mp4")

        if self.storage.exist(video_file):
            print(f"\n---- {self.yt_id}.mp4 Already Exist")
        else:
            print("\n--- Downloading Video ---")
            try:
                with yt_dlp.YoutubeDL(video_opts) as ydl:
                    ydl.download([self.yt_url])
                print("Video download completed successfully!")
            except DownloadError as e:
                print(f"An error occurred during video download: {e}")
            except Exception as e:
                print(f"An unexpected error occurred during video download: {e}")

    def download_audio(self) -> None:
        audio_opts = {
            "format": "bestaudio/best",
            "outtmpl": str(Path(self.audio_dir) / f"{self.yt_id}.%(ext)s"),
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
            "quiet": False,
        }

        audio_file = self.audio_dir.joinpath(f"{self.yt_id}.mp3")

        if self.storage.exist(audio_file):
            print(f"\n---- {self.yt_id}.mp3 Already Exist")
        else:
            print("\n--- Downloading Audio ---")
            try:
                with yt_dlp.YoutubeDL(audio_opts) as ydl:
                    ydl.download([self.yt_url])
                print("Audio download completed successfully!")
            except DownloadError as e:
                print(f"An error occurred during audio download: {e}")
            except Exception as e:
                print(f"An unexpected error occurred during audio download: {e}")

    def process_subtitle(self):
        pk_csv = self.subtitle_dir.joinpath("pk_transcript.csv")
        if not pk_csv.exists():
            print("Subtitle file does not exist.")
            raise FileNotFoundError("Subtitle file does not exist.")

        srt_path = self.subtitle_dir.joinpath(f"{self.yt_id}.srt")
        csv_path = self.subtitle_dir.joinpath(f"{self.yt_id}.csv")
        final_transcript_path = self.subtitle_dir.joinpath(
            f"{self.yt_id}_transcript.csv"
        )
        if final_transcript_path.exists():
            self.transcript = final_transcript_path
            print("Final transcript already exists. Skipping processing.")
            return

        # Check if SRT file already exists (for manual editing)
        if srt_path.exists():
            print(f"✅ SRT file already exists at: {srt_path}. Skipping download.")
        else:
            print("Downloading transcript from YouTube...")
            ytt_api = YouTubeTranscriptApi()
            transcript = ytt_api.fetch(self.yt_id)
            formatter = SRTFormatter()

            srt_formatted = formatter.format_transcript(transcript)
            with open(srt_path, "w", encoding="utf-8") as srt_file:
                srt_file.write(srt_formatted)
            print(f"✅ SRT file saved at: {srt_path}")

        self._srt_to_csv(srt_path, csv_path)

        pk_sub = pd.read_csv(pk_csv)
        counter = 0
        gap_lst = []
        for index, row in pk_sub.iterrows():
            duration = row["Start"] - counter
            if duration >= 2:
                gap_lst.append(
                    (math.ceil(counter), math.floor(counter + duration), index)
                )
            counter = row["End"]

        yt_sub = pd.read_csv(csv_path)
        merged_dict = {}
        for gap in gap_lst:
            selected_seg = []
            for index, row in yt_sub.iterrows():
                start = math.floor(row["Start"])
                end = math.floor(row["End"])
                if start >= gap[0] and end <= gap[1]:
                    selected_seg.append((start, end, index))
            merged_dict[gap[2]] = selected_seg

        final_sub = []
        for index, row in pk_sub.iterrows():
            if index in merged_dict.keys():
                print(merged_dict[index])
                for seg in merged_dict[index]:
                    ith_seg = yt_sub.iloc[seg[2]]
                    final_sub.append(
                        {
                            "Start": ith_seg["Start"],
                            "End": ith_seg["End"],
                            "Segment": ith_seg["Segment"],
                        }
                    )

            final_sub.append(
                {"Start": row["Start"], "End": row["End"], "Segment": row["Segment"]}
            )

        for idx, row in enumerate(final_sub):
            if idx != 0:
                prev_seg = final_sub[idx - 1]
                prev_end = prev_seg["End"]
                curr_start = row["Start"]
                gap = curr_start - prev_end
                if gap > self.silent_gap:
                    silent = {
                        "Start": math.ceil(prev_end),
                        "End": math.floor(curr_start),
                        "Segment": f"[Silent] for {gap:.2f} sec",
                    }
                    final_sub.insert(idx, silent)

        merged_df = pd.DataFrame(final_sub)
        merged_df.to_csv(final_transcript_path, index=False, encoding="utf-8-sig")
        self.transcript = final_transcript_path

    def segment_timestamps(self) -> None:
        transcript_path = self.transcript
        if self.storage.exist(transcript_path):
            transcript = pd.read_csv(transcript_path)
            start_time = 0
            frame_sampling_times = []
            prev_end_time = 0
            for idx, row in transcript.iterrows():
                start_time = row["Start"]
                end_time = row["End"]
                if idx == 0:
                    start_time = 0
                    prev_end_time = end_time
                else:
                    start_time = prev_end_time

                frame_sampling_times.append([start_time, end_time])
                prev_end_time = end_time
            vid_length = self._get_video_duration()
            frame_sampling_times[-1][1] = vid_length
            print(frame_sampling_times)

            self.frame_sampling_time_path = self.storage.make_file(
                self.merged_input_dir.joinpath("frame_sample_time.json")
            )
            with open(self.frame_sampling_time_path, "w", encoding="utf-8") as f:
                json.dump(frame_sampling_times, f)
            print("Done Samplig ")

    def video_cut(self):
        with open(
            self.frame_sampling_time_path,
            "r",
            encoding="utf-8",
        ) as f:
            ts_arr = json.load(f)

        print(ts_arr[:5])
        in_path = self.video_dir.joinpath(f"{self.yt_id}.mp4")
        out_dir = self.video_cut_dir

        def sec_to_ffmpeg_time(seconds):
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = seconds % 60
            return f"{hours:02}:{minutes:02}:{secs:06.3f}"

        for idx, ts in enumerate(ts_arr):
            start_str = sec_to_ffmpeg_time(ts[0])
            end_str = sec_to_ffmpeg_time(ts[1])
            out_path = out_dir.joinpath(f"{self.yt_id}-{idx:04}.mp4")
            cmd = [
                "ffmpeg",
                "-hide_banner",
                "-ss",
                start_str,
                "-to",
                end_str,
                "-i",
                in_path,
                "-c:v",
                "h264_nvenc",
                "-preset",
                "p7",
                "-tune",
                "lossless",
                "-profile:v",
                "high444p",
                "-pix_fmt",
                "yuv444p",
                "-c:a",
                "copy",
                out_path,
            ]
            subprocess.run(cmd, check=True)
            print(f"Done {idx}/{len(ts_arr)} ✅")

    def frame_sample(self, similarity_threshold=10, desired_processing_fps=1):  # 5, 3
        video_dir = self.video_cut_dir

        files = [f.name for f in video_dir.iterdir() if f.is_file()]
        files = sorted(files)
        frames_grp = []
        counter = 0

        for idx, file in enumerate(files):
            video_path = video_dir.joinpath(file)

            # --- 1. Setup and Validation ---
            print(f"Starting frame extraction for '{video_path}'...")

            if not self.storage.exist(video_path):
                print(f"Error: Video file not found at '{video_path}'")
                return

            output_dir = self.storage.make_dir(self.yt_dir.joinpath("frames"))
            print(f"Frames will be saved in '{output_dir}'")

            # --- 2. Open Video and Get Metadata ---
            try:
                reader = imageio.get_reader(video_path)
            except Exception as e:
                print(f"Error opening video file with imageio: {e}")
                print(
                    "Please ensure FFmpeg is installed and accessible on your system."
                )
                print(
                    "You can often install it by running: pip install imageio[ffmpeg]"
                )
                return

            meta_data = reader.get_meta_data()
            fps = meta_data.get("fps", 30)

            # Get total video duration directly from metadata
            video_duration = meta_data.get("duration")
            if video_duration is None:
                # Fallback calculation if duration is not in metadata
                video_duration = reader.count_frames() / fps
            print(f"Detected video duration: {video_duration:.2f} seconds.")

            # Process one frame per second
            # frame_interval = int(round(fps))
            frame_interval = int(round(fps / desired_processing_fps))
            if frame_interval < 1:  # Ensure we don't divide by zero or go below 1
                frame_interval = 1

            # --- 3. Frame Extraction Loop ---
            saved_frame_count = 0
            last_hash = None

            # Use a temporary dict with integer keys for efficiency
            sampled_frame = {}
            frames = []

            # Iterate through each frame in the video
            for frame_num, frame in enumerate(reader):
                # --- 4. Process Frame at ~1 FPS Interval ---
                if frame_num % frame_interval == 0:
                    pil_img = Image.fromarray(frame)
                    current_hash = imagehash.phash(pil_img)

                    # --- 5. Check for Uniqueness ---
                    if (
                        last_hash is None
                        or (current_hash - last_hash) > similarity_threshold
                    ):
                        filename = f"frame_{counter:05d}.png"
                        output_path = output_dir.joinpath(filename)

                        imageio.imwrite(output_path, frame)

                        current_time_sec = frame_num / fps
                        print(
                            f"Saved unique frame: {filename} (at video time ~{current_time_sec:.2f}s)"
                        )
                        sampled_frame[current_time_sec] = filename
                        frames.append(filename)
                        last_hash = current_hash
                        saved_frame_count += 1
                        counter += 1
            frames_grp.append(frames)
            frames = []
        try:
            self.frame_grp_path = self.storage.make_file(
                self.merged_input_dir.joinpath("frames_grp.json")
            )
            with open(self.frame_grp_path, "w") as f:
                json.dump(frames_grp, f, indent=4)
            print(f"\nSuccessfully created metadata: {self.frame_grp_path}")
        except Exception as e:
            print(f"\nError writing metadata file: {e}")

    def merge_frame_transcript(self):
        with open(self.frame_sampling_time_path, "r", encoding="utf-8") as f:
            frame_smaple_time = json.load(f)
        with open(self.frame_grp_path, "r", encoding="utf-8") as f:
            frames = json.load(f)

        transcript = pd.read_csv(self.transcript)

        merged_frame_transcript = []

        for idx, ts in enumerate(frame_smaple_time):
            start = ts[0]
            end = ts[1]
            frm_pick = frames[idx]
            segment = {
                "id": idx,
                "start": start,
                "end": end,
                "frames": frm_pick,
                "transcript": transcript.at[idx, "Segment"],
            }
            merged_frame_transcript.append(segment)

        merged_file = self.storage.make_file(
            self.merged_input_dir.joinpath("merged_input.json")
        )
        try:
            with open(merged_file, "w", encoding="utf-8") as f:
                json.dump(merged_frame_transcript, f, indent=4)
            print(f"Succssfully file created at: {merged_file} ✅")
        except Exception as e:
            print(f"Failed to write ❌ {e}")
