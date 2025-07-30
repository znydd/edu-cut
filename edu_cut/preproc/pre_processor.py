from ..storage.store_manager import Storage
from pathlib import Path
import yt_dlp


class PreProcessor:
    def __init__(self, yt_url: str):
        self.yt_url = yt_url[:43]
        self.yt_id = self.yt_url[32:]
        self.storage = Storage()
        self.yt_dir, self.video_dir, self.audio_dir = self.storage.create_yt_path(
            self.yt_id
        )

    def download(self) -> None:
        video_opts = {
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "outtmpl": str(Path(self.video_dir) / f"{self.yt_id}.%(ext)s"),
            "quiet": False,
        }
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
        video_file = self.video_dir.joinpath(f"{self.yt_id}.mp4")
        audio_file = self.audio_dir.joinpath(f"{self.yt_id}.mp3")

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


x = PreProcessor(
    "https://www.youtube.com/watch?v=cmjmsgkbZuw&list=PL9aZtK5kh5WcyVuwOF80eE88U5K7Ctva-&index=9"
)
x.download()
