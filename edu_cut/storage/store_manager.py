import os
from pathlib import Path
from dotenv import load_dotenv


class Storage:
    def __init__(self):
        load_dotenv()
        self.root_path = os.environ["APP_ROOT"]
        self.store_path = Path(self.root_path + "/store")
        self.store_path.mkdir(parents=True, exist_ok=True)

    def create_yt_path(self, yt_id: str):
        yt_dir = self.store_path.joinpath(yt_id)
        yt_video = yt_dir.joinpath("videos")
        yt_audio = yt_dir.joinpath("audios")
        if yt_video.exists() and yt_audio.exists():
            print(f"{yt_video} and {yt_audio} Exist ☑️")
            return (yt_dir, yt_video, yt_audio)
        try:
            yt_audio.mkdir(parents=True, exist_ok=True)
            yt_video.mkdir(parents=True, exist_ok=True)
            print(f"{yt_video} and {yt_audio} Created successfully ✅")
        except Exception as e:
            print("Error:", e)

        return (yt_dir, yt_video, yt_audio)

    def exist(self, path: Path):
        return path.exists()
