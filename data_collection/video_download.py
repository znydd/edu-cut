import yt_dlp
import os
import subprocess
import shutil
import traceback

def download_video_advanced(url, target_resolution='720p', output_dir_root='.'):
   
    final_files_destination_dir = os.path.join(output_dir_root, 'data')
    temp_files_work_dir = os.path.join(output_dir_root, 'temp_merge')

    os.makedirs(final_files_destination_dir, exist_ok=True)
    print(f"Final files will be saved in: {os.path.abspath(final_files_destination_dir)}")
    os.makedirs(temp_files_work_dir, exist_ok=True)
    print(f"Temporary files will be processed in: {os.path.abspath(temp_files_work_dir)}")

    # Paths for files if merging is needed (initialized to None)
    temp_video_file_path = None
    temp_audio_file_path = None
    final_output_path_generated = None 

    try:
        # --- Step 1: Get Video Metadata ---
        print(f"\nFetching video metadata for: {url}")
        ydl_meta_opts = {
            'quiet': False, # Show some output for metadata fetching
            'force_generic_extractor': True,
            'retries': 3,
            'noplaylist': True, # Ensure we only process a single video if URL is part of a playlist
        }
        with yt_dlp.YoutubeDL(ydl_meta_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            if not info_dict:
                print("Failed to fetch video metadata. Aborting.")
                return

            video_title = info_dict.get('title', 'unknown_title')
            # Sanitize title
            video_title = "".join(c for c in video_title if c.isalnum() or c in (' ', '.', '_', '-')).strip()
            video_title = " ".join(video_title.split()) # Replace multiple spaces
            if not video_title: video_title = 'untitled_video' # Ensure there's a title

            video_id = info_dict.get('id', 'unknown_id')

        print(f"Video Title: {video_title}")
        print(f"Video ID: {video_id}")

        # --- Step 2: Check for a suitable combined audio/video stream ---
        target_h_numeric = int(target_resolution.replace('p', ''))
        direct_download_format_info = None
        preferred_mp4_format = None # To store if an MP4 combined stream is found

        print(f"\nSearching for a combined video/audio stream at {target_resolution}...")
        for f_format in info_dict.get('formats', []):
            f_height = f_format.get('height')
            f_vcodec = f_format.get('vcodec')
            f_acodec = f_format.get('acodec')

            # Check if format has video, audio, and matches target height
            if f_height == target_h_numeric and \
               f_vcodec not in ['none', None] and \
               f_acodec not in ['none', None]:
                if f_format.get('ext') == 'mp4':
                    preferred_mp4_format = f_format
                    print(f"Found preferred MP4 combined stream: Format ID {f_format.get('format_id')}")
                    break # Found an MP4, this is ideal
                elif direct_download_format_info is None: # Store the first non-MP4 match
                    direct_download_format_info = f_format
                    print(f"Found a non-MP4 combined stream: Format ID {f_format.get('format_id')}, Ext: {f_format.get('ext')}")
        
        if preferred_mp4_format:
            direct_download_format_info = preferred_mp4_format
        
        # --- Step 3: Download ---
        if direct_download_format_info:
            # Scenario A: Download directly (video has audio at target resolution)
            format_id = direct_download_format_info.get('format_id', 'N/A')
            format_ext = direct_download_format_info.get('ext', 'mp4')
            print(f"\nSuitable combined stream found (ID: {format_id}, Ext: {format_ext}).")
            print(f"Downloading directly as MP4 to {final_files_destination_dir}...")

            final_file_name = f"{video_title} - {video_id}.mp4" # Ensure .mp4 output
            final_output_path_generated = os.path.join(final_files_destination_dir, final_file_name)

            ydl_direct_opts = {
                'format': direct_download_format_info['format_id'],
                'outtmpl': final_output_path_generated,
                'noprogress': False,
                'progress_hooks': [lambda d: print(f"Direct Download {d['status']} {d.get('_percent_str', '')} {d.get('speed_str', '')} ETA {d.get('eta_str', '')}", end='\r')],
                'retries': 5, 'fragment_retries': 10, 'concurrent_fragments': 5,
                'noplaylist': True,
                'merge_output_format': 'mp4', # Ensures final output is MP4
            }
            with yt_dlp.YoutubeDL(ydl_direct_opts) as ydl:
                ydl.download([url])
            print(f"\nSuccessfully downloaded video with audio to: {final_output_path_generated}")

        else:
            # Scenario B: Download video and audio separately, then merge
            print(f"\nNo suitable single stream with audio found for {target_resolution} (or only video-only streams available at this res).")
            print("Proceeding to download video and audio separately for merging.")

            # Define temporary file paths (yt-dlp will add the correct extension)
            temp_video_filename_template = os.path.join(temp_files_work_dir, f"{video_title} - {video_id}_video.%(ext)s")
            temp_audio_filename_template = os.path.join(temp_files_work_dir, f"{video_title} - {video_id}_audio.%(ext)s")
            
            final_merged_file_name = f"{video_title} - {video_id}_merged.mp4"
            final_output_path_generated = os.path.join(final_files_destination_dir, final_merged_file_name)

            # Download Video Stream
            print(f"\nDownloading {target_resolution} video stream to temporary location: {temp_files_work_dir}")
            video_format_selector = f'bestvideo[height<={target_h_numeric}][ext=mp4]/bestvideo[height<={target_h_numeric}]/bestvideo'
            ydl_video_opts = {
                'format': video_format_selector,
                'outtmpl': temp_video_filename_template,
                'noprogress': False,
                'progress_hooks': [lambda d: print(f"Video Download {d['status']} {d.get('_percent_str', '')} {d.get('speed_str', '')} ETA {d.get('eta_str', '')}", end='\r')],
                'retries': 5, 'fragment_retries': 10, 'concurrent_fragments': 5, 'noplaylist': True,
            }
            with yt_dlp.YoutubeDL(ydl_video_opts) as ydl:
                video_dl_info = ydl.extract_info(url, download=True)
                if video_dl_info: # extract_info returns dict of downloaded file
                    temp_video_file_path = ydl.prepare_filename(video_dl_info)
                    if not os.path.exists(temp_video_file_path):
                         print(f"\nWarning: Downloaded video file not found at expected path: {temp_video_file_path}")
                         temp_video_file_path = None # Mark as failed
                else:
                    print("\nVideo download failed (no info returned by yt-dlp).")
                    temp_video_file_path = None
            
            if temp_video_file_path:
                 print(f"\nVideo temporarily downloaded to: {temp_video_file_path}")
            else:
                print("\nVideo download failed or path could not be determined. Skipping audio download and merge.")

            # Download Audio Stream (only if video downloaded successfully)
            if temp_video_file_path and os.path.exists(temp_video_file_path):
                print(f"\nDownloading best audio stream to temporary location: {temp_files_work_dir}")
                audio_format_selector = 'bestaudio[ext=m4a]/bestaudio[ext=opus]/bestaudio' # Prefer m4a (AAC)
                ydl_audio_opts = {
                    'format': audio_format_selector,
                    'outtmpl': temp_audio_filename_template,
                    'noprogress': False,
                    'progress_hooks': [lambda d: print(f"Audio Download {d['status']} {d.get('_percent_str', '')} {d.get('speed_str', '')} ETA {d.get('eta_str', '')}", end='\r')],
                    'retries': 5, 'fragment_retries': 10, 'concurrent_fragments': 5, 'noplaylist': True,
                }
                with yt_dlp.YoutubeDL(ydl_audio_opts) as ydl:
                    audio_dl_info = ydl.extract_info(url, download=True)
                    if audio_dl_info:
                        temp_audio_file_path = ydl.prepare_filename(audio_dl_info)
                        if not os.path.exists(temp_audio_file_path):
                            print(f"\nWarning: Downloaded audio file not found at expected path: {temp_audio_file_path}")
                            temp_audio_file_path = None
                    else:
                        print("\nAudio download failed (no info returned by yt-dlp).")
                        temp_audio_file_path = None

                if temp_audio_file_path:
                    print(f"\nAudio temporarily downloaded to: {temp_audio_file_path}")
                else:
                    print("\nAudio download failed or path could not be determined. Skipping merge.")

            # Merge Video and Audio (if both downloaded successfully)
            if temp_video_file_path and os.path.exists(temp_video_file_path) and \
               temp_audio_file_path and os.path.exists(temp_audio_file_path):
                print(f"\nMerging video and audio into: {final_output_path_generated}")
                ffmpeg_command = [
                    'ffmpeg',
                    '-i', temp_video_file_path,
                    '-i', temp_audio_file_path,
                    '-c:v', 'copy',      # Copy video codec without re-encoding
                    '-c:a', 'aac',       # Encode audio to AAC for compatibility
                    '-strict', 'experimental', # For older ffmpeg versions if aac is experimental
                    '-map', '0:v:0',     # Select video stream from first input
                    '-map', '1:a:0',     # Select audio stream from second input
                    '-y',                # Overwrite output file if it exists
                    final_output_path_generated
                ]
                try:
                    process = subprocess.run(ffmpeg_command, check=True, capture_output=True, text=True, encoding='utf-8')
                    print(f"\nSuccessfully merged video and audio to: {final_output_path_generated}")
                    # Delete the temporary audio file after successful merge
                    if os.path.exists(temp_audio_file_path):
                        os.remove(temp_audio_file_path)
                        print(f"Removed temporary audio file: {temp_audio_file_path}")
                        temp_audio_file_path = None # Mark as removed
                except subprocess.CalledProcessError as e:
                    print(f"\nError during FFmpeg merging. FFmpeg output below:")
                    print(f"STDOUT: {e.stdout}")
                    print(f"STDERR: {e.stderr}")
                    final_output_path_generated = None # Merge failed
                except FileNotFoundError:
                    print("\nFFmpeg command not found. Please ensure FFmpeg is correctly installed and in your system's PATH.")
                    final_output_path_generated = None # Merge failed
            else:
                if not (temp_video_file_path and os.path.exists(temp_video_file_path)):
                    print("Skipping merge: Video file was not downloaded successfully or its path is invalid.")
                if not (temp_audio_file_path and os.path.exists(temp_audio_file_path)): # Check only if video was okay
                    print("Skipping merge: Audio file was not downloaded successfully or its path is invalid.")
                final_output_path_generated = None # Merge not attempted or failed

    except yt_dlp.utils.DownloadError as e:
        print(f"\nA download error occurred with yt-dlp: {e}")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        traceback.print_exc()
    finally:
        # --- Step 5: Clean up temporary files and directory ---
        print("\nCleaning up temporary files...")
        # Remove the temporary video file if it exists (used in merge scenario)
        if temp_video_file_path and os.path.exists(temp_video_file_path):
            try:
                os.remove(temp_video_file_path)
                print(f"Removed temporary video file: {temp_video_file_path}")
            except OSError as e:
                print(f"Error removing temporary video file '{temp_video_file_path}': {e}")
        
        # Remove the temporary audio file if it still exists (e.g., merge failed or wasn't attempted and successfully removed)
        if temp_audio_file_path and os.path.exists(temp_audio_file_path):
            try:
                os.remove(temp_audio_file_path)
                print(f"Removed temporary audio file (if not already after merge): {temp_audio_file_path}")
            except OSError as e:
                print(f"Error removing temporary audio file '{temp_audio_file_path}': {e}")

        # Remove the temporary directory
        if os.path.exists(temp_files_work_dir):
            try:
                shutil.rmtree(temp_files_work_dir)
                print(f"Removed temporary directory and its contents: {temp_files_work_dir}")
            except OSError as e:
                print(f"Error removing temporary directory '{temp_files_work_dir}': {e}")
        
        if final_output_path_generated and os.path.exists(final_output_path_generated):
            print(f"\nProcess complete. Final video saved at: {final_output_path_generated}")
        else:
            print("\nProcess completed, but the final video file was not generated or its path is unknown.")


if __name__ == "__main__":
    video_url = "https://www.youtube.com/watch?v=xMrnYzTDtwY" # TRZ sir's lecture
    desired_resolution = '720p' 
    download_base_directory = '.' 

    print(f"Starting video download process for URL: {video_url}")
    print(f"Target resolution: {desired_resolution}")
    print(f"Base output directory for 'data' and 'temp_merge' folders: {os.path.abspath(download_base_directory)}")
    
    download_video_advanced(video_url, desired_resolution, download_base_directory)
