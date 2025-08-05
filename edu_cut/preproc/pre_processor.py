import yt_dlp
import imageio
import json
import subprocess
import imagehash
from PIL import Image
import pandas as pd
from pathlib import Path
from pydub import AudioSegment, silence

from ..storage.store_manager import Storage


class PreProcessor:
    def __init__(self, yt_url: str):
        self.yt_url = yt_url[:43]
        self.yt_id = self.yt_url[32:]
        self.storage = Storage()
        self.yt_dir, self.video_dir, self.audio_dir = self.storage.create_yt_path(
            self.yt_id
        )

    def download_video(self) -> None:
        video_opts = {
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
            except yt_dlp.utils.DownloadError as e:
                print(f"An error occurred during video download: {e}")
            except Exception as e:
                print(f"An unexpected error occurred during video download: {e}")

    def get_video_duration(self) -> float:
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
            except yt_dlp.utils.DownloadError as e:
                print(f"An error occurred during audio download: {e}")
            except Exception as e:
                print(f"An unexpected error occurred during audio download: {e}")

    def audio_cut(self, min_silence_len=700, silence_thresh=14, keep_silence=300):
        audio_cut_path = self.storage.create_audio_cut_path(self.yt_id)
        audio_file_path = self.audio_dir.joinpath(f"{self.yt_id}.mp3")

        # Load the audio
        audio = AudioSegment.from_file(
            audio_file_path,
            format="mp3",
        )
        silence_thresh = audio.dBFS - silence_thresh  # Adaptive threshold

        silent_ranges = silence.detect_silence(
            audio, min_silence_len=min_silence_len, silence_thresh=silence_thresh
        )
        cut_points = [0] + [r[1] for r in silent_ranges] + [len(audio)]

        # Remove very short segments (optional)
        cut_points = sorted(set(cut_points))
        cut_pairs = [
            (cut_points[i], cut_points[i + 1]) for i in range(len(cut_points) - 1)
        ]

        metadata = []

        # Process chunks
        for i, (start, end) in enumerate(cut_pairs):
            # Adjust for silence padding if needed
            start_adj = max(0, start - keep_silence // 2)
            end_adj = min(len(audio), end + keep_silence // 2)

            filename = audio_cut_path.joinpath(f"segment_{i + 1}.wav")
            if not filename.exists():
                chunk = audio[start_adj:end_adj]
                chunk.export(filename, format="wav")
                print(
                    f"✔️  Segment {i + 1} cut: "
                    f"{start_adj}ms–{end_adj}ms "
                    f"({(end_adj - start_adj) / 1000:.2f}s) → {filename}"
                )
            else:
                print(f"⚠️  Skipping segment {i + 1}: already exists at {filename}")

            metadata.append(
                {
                    "chunk_index": i + 1,
                    "filename": str(filename),
                    "start_time_ms": start_adj // 1000,
                    "end_time_ms": end_adj // 1000,
                    "duration_ms": (end_adj - start_adj) // 1000,
                }
            )

        file_path = str(audio_cut_path.joinpath("segments_metadata.json"))
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        print(
            f"✅ Processed {len(metadata)} segments. Metadata saved to segments_metadata.json"
        )

        return

    def segment_timestamps(self) -> None:
        transcript_path = self.yt_dir.joinpath("transcription.csv")
        if self.storage.exist(transcript_path):
            transcript = pd.read_csv(transcript_path)
            start_time = 0
            frame_sampling_times = []
            prev_end_time = 0
            for idx, row in transcript.iterrows():
                start_time = row["Start (s)"]
                end_time = row["End (s)"]
                if idx == 0:
                    start_time = 0
                    prev_end_time = end_time
                else:
                    start_time = prev_end_time

                frame_sampling_times.append([start_time, end_time])
                prev_end_time = end_time
            vid_length = self.get_video_duration()
            frame_sampling_times[-1][1] = vid_length
            print(frame_sampling_times)

            json_pth = self.yt_dir.joinpath("frame_sample_time.json")
            with open(json_pth, "w", encoding="utf-8") as f:
                json.dump(frame_sampling_times, f)
            print("Done Samplig ")

    def frame_sample(self, similarity_threshold=2, desired_processing_fps=3):
        video_path = self.video_dir.joinpath(f"{self.yt_id}.mp4")

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
            print("Please ensure FFmpeg is installed and accessible on your system.")
            print("You can often install it by running: pip install imageio[ffmpeg]")
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
                    filename = f"frame_{saved_frame_count:05d}.png"
                    output_path = output_dir.joinpath(filename)

                    imageio.imwrite(output_path, frame)

                    current_time_sec = frame_num / fps
                    print(
                        f"Saved unique frame: {filename} (at video time ~{current_time_sec:.2f}s)"
                    )
                    sampled_frame[current_time_sec] = filename
                    last_hash = current_hash
                    saved_frame_count += 1
        try:
            metadata_pth = self.yt_dir.joinpath("frame_metadata.json")
            with open(metadata_pth, "w") as f:
                json.dump(sampled_frame, f, indent=4)
            print(f"\nSuccessfully created metadata: {metadata_pth}")
        except Exception as e:
            print(f"\nError writing metadata file: {e}")

    def merge_frame_transcript(self):
        with (
            open(
                self.yt_dir.joinpath("frame_sample_time.json"), "r", encoding="utf-8"
            ) as f1,
            open(
                self.yt_dir.joinpath("frame_metadata.json"), "r", encoding="utf-8"
            ) as f2,
        ):
            frame_smaple_time = json.load(f1)
            frame_metadata = json.load(f2)
        transcript = pd.read_csv(self.yt_dir.joinpath("transcription.csv"))
        frame_ts = [float(t) for t in list(frame_metadata.keys())]

        merged_frame_transcript = []

        for idx, ts in enumerate(frame_smaple_time):
            start = ts[0]
            end = ts[1]
            frm_pick = [f for f in frame_ts if f >= start and f <= end]

            segment = {
                "id": idx,
                "start": start,
                "end": end,
                "frames": [frame_metadata[str(f)] for f in frm_pick],
                "transcript": transcript.at[idx, "Segment"],
            }
            merged_frame_transcript.append(segment)

        merged_file = self.storage.make_file(self.yt_dir.joinpath("merged_input.json"))
        try:
            with open(merged_file, "w", encoding="utf-8") as f:
                json.dump(merged_frame_transcript, f, indent=4)
            print(f"Succssfully file created at: {merged_file} ✅")
        except Exception as e:
            print(f"Failed to write ❌ {e}")
