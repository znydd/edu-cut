import base64
import json
import subprocess
from pathlib import Path
from typing import Any

import imagehash
import imageio
import pandas as pd
import yt_dlp
from PIL import Image
from pydub import AudioSegment, effects, silence
from yt_dlp.utils import DownloadError

from ..storage.store_manager import Storage


class PreProcessor:
    def __init__(self, yt_url: str):
        self.yt_url = yt_url[:43]
        self.yt_id = self.yt_url[32:]
        self.storage = Storage()
        self._create_dir()

    def _create_dir(self):
        self.yt_dir, self.video_dir, self.audio_dir = self.storage.create_yt_path(
            self.yt_id
        )

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
            except DownloadError as e:
                print(f"An error occurred during audio download: {e}")
            except Exception as e:
                print(f"An unexpected error occurred during audio download: {e}")

    def audio_cut(
        self,
        min_silence_len_ms: int = 800,  # increase: 700→800–1200 for lectures/conversations
        silence_rel_db: int = 18,  # threshold = audio.dBFS - silence_rel_db
        keep_silence_ms: int = 250,  # small pad around each final chunk
        min_gap_to_split_ms: int = 600,  # ignore tiny gaps; merge across pauses shorter than this
        min_chunk_ms: int = 4000,  # ensure each chunk is at least this long (merge if shorter)
        normalize_lufs: bool = False,  # optional: loudness normalize per chunk
    ):
        """
        Robust, pause-based sentence/phrase cutter:
        - Finds NON-SILENT ranges (speech) with detect_nonsilent
        - Merges across short gaps and too-short chunks
        - Exports .wav files + JSON metadata
        """
        audio_cut_path = self.storage.create_audio_cut_path(self.yt_id)
        audio_file_path = self.audio_dir.joinpath(f"{self.yt_id}.mp3")

        # Load and (optionally) set to mono for more stable silence detection
        audio = AudioSegment.from_file(audio_file_path, format="mp3").set_channels(1)

        # Adaptive silence threshold (more negative => stricter silence)
        # Example: if avg dBFS=-20 and rel=18 -> threshold≈-38 dBFS
        silence_thresh_dbfs = max(audio.dBFS - silence_rel_db, -60.0)

        # 1) Detect NON-silent regions (better than cutting at every silence)
        nonsilent = silence.detect_nonsilent(
            audio,
            min_silence_len=min_silence_len_ms,
            silence_thresh=silence_thresh_dbfs,
            seek_step=5,  # ms; lower -> finer, slower
        )
        if not nonsilent:
            print("No non-silent regions found with current parameters.")
            return

        # 2) Merge across tiny gaps and enforce minimum duration
        #    - First pass: merge when the gap is smaller than min_gap_to_split_ms
        merged = []
        cur_start, cur_end = nonsilent[0]
        for start, end in nonsilent[1:]:
            short_gap = start - cur_end < min_gap_to_split_ms
            short_cur = (cur_end - cur_start) < min_chunk_ms
            if short_gap or short_cur:
                # Extend current region
                cur_end = max(cur_end, end)
            else:
                merged.append([cur_start, cur_end])
                cur_start, cur_end = start, end
        merged.append([cur_start, cur_end])

        # 3) Second pass: if any chunk still < min_chunk_ms, glue it to the nearest neighbor
        final_ranges = []
        for i, (s, e) in enumerate(merged):
            if (e - s) >= min_chunk_ms or not final_ranges:
                final_ranges.append([s, e])
            else:
                # Merge with previous (typical and simpler). If you prefer “nearest”, compare gaps.
                final_ranges[-1][1] = e

        # 4) Apply padding after merging
        padded = []
        L = len(audio)
        for s, e in final_ranges:
            s = max(0, s - keep_silence_ms)
            e = min(L, e + keep_silence_ms)
            # Also avoid micro-chunks caused by extreme settings
            if e - s >= max(keep_silence_ms * 2, 1000):
                padded.append([s, e])

        # 5) Export and write metadata
        metadata = []
        for i, (s, e) in enumerate(padded, 1):
            chunk = audio[s:e]
            if normalize_lufs:
                # Simple normalization; replace with a LUFS-normalizer if you like
                chunk = effects.normalize(chunk)

            filename = audio_cut_path.joinpath(f"segment_{i:04d}.wav")
            if not filename.exists():
                chunk.export(filename, format="wav")
                print(
                    f"✔️  Segment {i:04d}: {s}–{e} ms ({(e - s) / 1000:.2f}s) → {filename}"
                )
            else:
                print(f"⚠️  Skipping existing {filename}")

            metadata.append(
                {
                    "chunk_index": i,
                    "filename": str(filename),
                    "start_time_ms": s,
                    "end_time_ms": e,
                    "duration_ms": e - s,
                }
            )

        out_meta = audio_cut_path.joinpath("segments_metadata.json")
        out_meta.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        print(f"✅ Processed {len(metadata)} segments. Saved → {out_meta}")

    def segment_timestamps(self) -> None:
        transcript_path = self.yt_dir.joinpath("transcription.csv")
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
            vid_length = self.get_video_duration()
            frame_sampling_times[-1][1] = vid_length
            print(frame_sampling_times)

            json_pth = self.storage.make_file(
                self.yt_dir.joinpath("frame_sample_time.json")
            )
            with open(json_pth, "w", encoding="utf-8") as f:
                json.dump(frame_sampling_times, f)
            print("Done Samplig ")

    def segment_timestamps_new(self) -> None:
        # Here Provide gap filled trascription/subtitle
        transcript_path = self.yt_dir.joinpath("transcription.csv")
        if self.storage.exist(transcript_path):
            transcript = pd.read_csv(transcript_path)
            frame_sampling_times = []
            for idx, row in transcript.iterrows():
                start_time = row["Start (s)"]
                end_time = row["End (s)"]
                frame_sampling_times.append([start_time, end_time])
            print(frame_sampling_times)

            json_pth = self.yt_dir.joinpath("frame_sample_time.json")
            with open(json_pth, "w", encoding="utf-8") as f:
                json.dump(frame_sampling_times, f)
            print("Done Samplig ")

    def video_cut(self):
        with open(
            self.yt_dir.joinpath("frame_sample_time.json"), "r", encoding="utf-8"
        ) as f:
            ts_arr = json.load(f)
        print(ts_arr[:5])
        in_path = self.video_dir.joinpath(f"{self.yt_id}.mp4")
        out_dir = self.storage.make_dir(
            Path(f"/home/znyd/hacking/edu-cut/store/{self.yt_id}/video_cut")
        )

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

    def frame_sample(self, similarity_threshold=5, desired_processing_fps=3):
        video_dir = self.yt_dir.joinpath("video_cut")

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
            metadata_pth = self.storage.make_file(
                self.yt_dir.joinpath("frames_grp.json")
            )
            with open(metadata_pth, "w") as f:
                json.dump(frames_grp, f, indent=4)
            print(f"\nSuccessfully created metadata: {metadata_pth}")
        except Exception as e:
            print(f"\nError writing metadata file: {e}")

    def merge_frame_transcript(self):
        with open(
            self.yt_dir.joinpath("frame_sample_time.json"), "r", encoding="utf-8"
        ) as f:
            frame_smaple_time = json.load(f)
        with open(self.yt_dir.joinpath("frames_grp.json"), "r", encoding="utf-8") as f:
            frames = json.load(f)

        transcript = pd.read_csv(self.yt_dir.joinpath("transcription.csv"))

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

        merged_file = self.storage.make_file(self.yt_dir.joinpath("merged_input.json"))
        try:
            with open(merged_file, "w", encoding="utf-8") as f:
                json.dump(merged_frame_transcript, f, indent=4)
            print(f"Succssfully file created at: {merged_file} ✅")
        except Exception as e:
            print(f"Failed to write ❌ {e}")

    def more_proc_merged(self):
        with open(
            self.yt_dir.joinpath("merged_input.json"), "r", encoding="utf-8"
        ) as f:
            data = json.load(f)
        print(data[:5])
        no_frame_chunk = []
        for idx, data_point in enumerate(data):
            if not data_point["frames"]:
                no_frame_chunk.append(idx)
        print(no_frame_chunk)
        no_frame_chunk = sorted(no_frame_chunk)
        no_frame_grp = []
        bucket = []
        last_one = no_frame_chunk[0]
        for idx, chunk_id in enumerate(no_frame_chunk):
            if idx == 0:
                bucket.append(chunk_id)
            else:
                if last_one + 1 == chunk_id:
                    bucket.append(chunk_id)
                    last_one = chunk_id
                else:
                    no_frame_grp.append(bucket)
                    bucket = []
                    last_one = chunk_id
                    bucket.append(chunk_id)
        print(no_frame_grp)

        for grp in no_frame_grp:
            grp_transcript = "\n"
            for chunk_idx in grp:
                grp_transcript += data[chunk_idx]["transcript"] + "\n"
            data[grp[0] - 1]["transcript"] += grp_transcript
            data[grp[0] - 1]["end"] = data[grp[-1]]["end"]
            print(grp[0])

        with open(self.yt_dir.joinpath("final.json"), "w", encoding="utf-8") as f:
            json.dump(data, f)

    def base64_image(self, path):
        b = Path(path).read_bytes()
        return "data:image/png;base64," + base64.b64encode(b).decode()

    def smart_cut_msg(self):
        msg = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": """ You are a helpful assistant who can identify and group consecutive related transcript/subtitle of any video.
                These are transcriptions/subtitles of a long video chunked with start and end
                 timestamps. Now your work is according to these transcript group all the consecutive relevant or reletaed chunk together and give me
                a json response with **only start and end timestamp not the subtitle/trnscript** just like below example:(times are in seconds)
                ```json
                {{
                part_0:[0s - 45.00s],
                part_1:[45.08s - 390.00s],
                ....
                }}
                  """,
                    },
                ],
            }
        ]
        with open(
            self.yt_dir.joinpath("merged_input.json"), "r", encoding="utf-8"
        ) as f:
            data = json.load(f)
        data_points = []
        for data_point in data:
            data_point.pop("frames")
            data_point.pop("id")
            data_points.append(dict({"type": "text", "text": str(data_point)}))
        msg[0]["content"] = msg[0]["content"] + data_points
        return msg


# msg = [{
#     "role": "user",
#     "content": [
#         {"type": "text", "text": "Describe what is happening on these video frames."},
#         {"type": "image_url", "image_url": {"url": base64_image("/home/znyd/hacking/edu-cut/store/O4bjWrhL4z0/frames/frame_00000.png")}},
#         {"type": "image_url", "image_url": {"url": base64_image("/home/znyd/hacking/edu-cut/store/O4bjWrhL4z0/frames/frame_00001.png")}},
#     ],
# }]

p = PreProcessor("https://www.youtube.com/watch?v=uuaBdjMhjoA")

# p.download_video()
# p.download_audio()

# p.segment_timestamps()
# p.video_cut()
# p.frame_sample()
# p.merge_frame_transcript()
# ./llama-server --model gemma-3-4b-it-UD-Q8_K_XL.gguf --mmproj mmproj-BF16.gguf --host 127.0.0.1 --port 8000 -c 64000 -ngl 999
# python3 -m edu_cut.preproc.pre_processor
