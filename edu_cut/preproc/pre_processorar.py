import yt_dlp
import json
from ..storage.store_manager import Storage
from pathlib import Path
from pydub import AudioSegment, silence
import pandas as pd


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

    def timestamps_frame_sample(self) -> None:
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
            print(frame_sampling_times)

            json_pth = self.yt_dir.joinpath("frame_sample_time.json")
            with open(json_pth, "w", encoding="utf-8") as f:
                json.dump(frame_sampling_times, f)
            print("Done Samplig ")

    def frame_sample(self):
        pass


x = PreProcessor("https://www.youtube.com/watch?v=O4bjWrhL4z0")
# x.download_video()
# x.download_audio()
# x.audio_cut()
