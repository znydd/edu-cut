import argparse
import yt_dlp
import os


def download_media(url, output_path="downloads"):
    """
    Downloads both the best quality video and a separate MP3 audio file
    from a YouTube URL using yt-dlp.

    Args:
        url (str): The URL of the YouTube video.
        output_path (str): The base directory to save the downloaded files.
                           Video and audio will be placed in subdirectories.
    """
    # --- 1. Create Output Directories ---
    # Create separate subdirectories for video and audio to keep them organized.
    video_output_path = os.path.join(output_path, "video")
    audio_output_path = os.path.join(output_path, "audio")
    os.makedirs(video_output_path, exist_ok=True)
    os.makedirs(audio_output_path, exist_ok=True)

    # --- 2. Configure Download Options ---

    # Options for video download (best quality MP4)
    video_opts = {
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "outtmpl": os.path.join(video_output_path, "%(title)s.%(ext)s"),
        "quiet": False,
    }

    # Options for audio-only download (best quality converted to MP3)
    audio_opts = {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(audio_output_path, "%(title)s.%(ext)s"),
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
        "quiet": False,
    }

    # --- 3. Start Downloads ---
    print(f"Starting downloads for: {url}")
    print(f"Files will be saved in '{os.path.abspath(output_path)}'")

    # Download the video
    print("\n--- Downloading Video ---")
    try:
        with yt_dlp.YoutubeDL(video_opts) as ydl:
            ydl.download([url])
        print("Video download completed successfully!")
    except yt_dlp.utils.DownloadError as e:
        print(f"An error occurred during video download: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during video download: {e}")

    # Download the audio
    print("\n--- Downloading Audio ---")
    try:
        with yt_dlp.YoutubeDL(audio_opts) as ydl:
            ydl.download([url])
        print("Audio download completed successfully!")
    except yt_dlp.utils.DownloadError as e:
        print(f"An error occurred during audio download: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during audio download: {e}")
        print("Please ensure FFmpeg is installed and accessible in your system's PATH.")

    print("\nAll tasks finished.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Download both video and audio from a YouTube URL using yt-dlp.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("url", type=str, help="The full URL of the YouTube video.")
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default="downloads",
        help="The base directory where files will be saved.\nDefault is 'downloads'.",
    )

    args = parser.parse_args()

    # --- Installation Instructions ---
    # Before running, ensure you have the required libraries installed:
    #
    # 1. Install yt-dlp:
    #    pip install yt-dlp
    #
    # 2. For audio conversion (to .mp3), FFmpeg is required.
    #    It's a separate program you need to install on your system.
    #    - Windows: Download from https://ffmpeg.org/download.html and add to your system's PATH.
    #    - macOS (using Homebrew): brew install ffmpeg
    #    - Linux (using apt): sudo apt-get install ffmpeg

    # --- Example Usage from Command Line ---
    #
    # To download video and audio:
    # python your_script_name.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    #
    # To specify an output directory:
    # python your_script_name.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ" -o "C:\\my_downloads"

    download_media(args.url, args.output)

    # python3 yt.py "https://www.youtube.com/watch?v=QBbC3Cjsnjg"
    # python3 yt.py "https://www.youtube.com/watch?v=HAoL5fPmgrw"
