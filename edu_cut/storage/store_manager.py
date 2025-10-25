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

    def create_yt_store_dir(self, yt_id: str) -> Tuple:
        yt_dir = self.store_path.joinpath(yt_id)
        audio_dir = yt_dir.joinpath("audio")
        video_dir = yt_dir.joinpath("video")
        video_cut_dir = yt_dir.joinpath("video_cut")
        subtitle_dir = yt_dir.joinpath("subtitle")
        merged_input_dir = yt_dir.joinpath("merged_input")
        responses_dir = yt_dir.joinpath("responses")
        if (
            yt_dir.exists()
            and video_dir.exists()
            and audio_dir.exists()
            and video_cut_dir.exists()
            and subtitle_dir.exists()
            and merged_input_dir.exists()
            and responses_dir.exists()
        ):
            print(
                f"{yt_dir},{video_dir},{video_cut_dir}, {audio_dir}, {subtitle_dir}, {merged_input_dir}, {responses_dir} Exist ✅"
            )
            return (
                yt_dir,
                audio_dir,
                video_dir,
                video_cut_dir,
                subtitle_dir,
                merged_input_dir,
                responses_dir,
            )
        try:
            yt_dir.mkdir(parents=True, exist_ok=True)
            audio_dir.mkdir(parents=True, exist_ok=True)
            video_dir.mkdir(parents=True, exist_ok=True)
            video_cut_dir.mkdir(parents=True, exist_ok=True)
            subtitle_dir.mkdir(parents=True, exist_ok=True)
            merged_input_dir.mkdir(parents=True, exist_ok=True)
            responses_dir.mkdir(parents=True, exist_ok=True)
            print(
                f"{yt_dir},{video_dir},{video_cut_dir}, {audio_dir}, {subtitle_dir}, {merged_input_dir}, {responses_dir} Created successfully ✅"
            )
            return (
                yt_dir,
                audio_dir,
                video_dir,
                video_cut_dir,
                subtitle_dir,
                merged_input_dir,
                responses_dir,
            )
        except Exception as e:
            print("Error: ", e)

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
