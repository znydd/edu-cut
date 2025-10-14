import os
from pathlib import Path
from typing import Tuple

from dotenv import load_dotenv


class Storage:
    def __init__(self):
        load_dotenv()
        self.root_path = os.environ["APP_ROOT"]
        self.store_path = Path(self.root_path + "/store")
        self.store_path.mkdir(parents=True, exist_ok=True)

    def create_yt_path(self, yt_id: str) -> Tuple:
        yt_dir = self.store_path.joinpath(yt_id)
        yt_video = yt_dir.joinpath("video")
        yt_audio = yt_dir.joinpath("audio")
        if yt_video.exists() and yt_audio.exists():
            print(f"{yt_video} and {yt_audio} Exist ☑️")
            return (yt_dir, yt_video, yt_audio)
        try:
            yt_audio.mkdir(parents=True, exist_ok=True)
            yt_video.mkdir(parents=True, exist_ok=True)
            print(f"{yt_video} and {yt_audio} Created successfully ✅")
        except Exception as e:
            print("Error: ", e)

        return (yt_dir, yt_video, yt_audio)

    def create_audio_cut_path(self, yt_id: str) -> Path | None:
        yt_dir = self.store_path.joinpath(yt_id)
        if self.exist(yt_dir):
            try:
                audio_cut_path = yt_dir.joinpath("audio_cut")
                audio_cut_path.mkdir(parents=True, exist_ok=True)
                return audio_cut_path
            except Exception as e:
                print("Error: ", e)
        else:
            print("YouTube Path does not exist ❌")
            return self.store_path

    def make_dir(self, dir: Path):
        try:
            dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"Error creating folder: {e}")
        return dir

    def make_file(self, file_pth: Path):
        try:
            file_pth.touch(exist_ok=True)
        except Exception as e:
            print(f"Error creating file: {e}")
        return file_pth

    def exist(self, path: Path):
        return path.exists()
