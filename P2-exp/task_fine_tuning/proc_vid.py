from pathlib import Path
import json
import yt_dlp
from pathlib import Path
from moviepy import VideoFileClip

total_clip = 180



def download_youtube(url, output_dir, filename="video.mp4"):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    ydl_opts = {
        'format': 'bestvideo[height<=720]+bestaudio/best[height<=720]/best',
        'outtmpl': str(output_dir / filename),
        'merge_output_format': 'mp4',
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return




def trim_video(input_file, output_dir, timestamps, yt_id):
    global total_clip
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    video = VideoFileClip(input_file)
    
    for idx, ts in enumerate(timestamps):
        start = parse_time(ts["start_time"])
        end = parse_time(ts["end_time"])
        start = min(start, video.duration)
        end = min(end, video.duration)

        output_path = output_dir / f"{idx:03}_{yt_id}.mp4"
        # ✅ check if clip already exists
        if output_path.exists():
            print(f"✅ Clip {output_path.name} already exists — skipping.")
            total_clip -= 1
            continue

        subclip = video.subclipped(start, end)
        subclip.write_videofile(str(output_path), codec="libx264")

        total_clip-=1
        print(f"Clip left: {total_clip}📜")
    
    video.close()

def parse_time(timestr):
    if len(timestr) < 8:
        timestr = "00:"+timestr
    h, m, s = map(int, timestr.split(":"))
    
    return h * 3600 + m * 60 + s



input_file = "irrelevant.json"
output_dir = "full_video" 

with open(input_file, "r", encoding="utf-8") as file:
    loaded_file = json.load(file)

# for i in range(26, len(loaded_file)):
#     yt_link = loaded_file[i]['link']
#     yt_id = yt_link[32:43]
#     print(yt_link)

#     output_dir = Path(output_dir)
#     output_file = output_dir / f"{yt_id}.mp4"

#     # ✅ Check if file exists
#     if output_file.exists():
#         print(f"✅ Skipping {yt_id} — file already exists.")
#         continue

#     download_youtube(yt_link, output_dir, yt_id+".mp4")

# print("All video downloaded✅✅")

for i in range(len(loaded_file)):
    yt_id = loaded_file[i]['link'][32:43]

    timestamps = []
    for caption in loaded_file[i]["irrelevant_segments"]:
        start_time = caption['start_time']
        end_time = caption['end_time'] 
        segment = {"start_time": start_time, "end_time": end_time}
        timestamps.append(segment)
    trim_video(f"full_video/{yt_id}.mp4", "cropped_vid", timestamps, yt_id)
        
    print(f"vid-{yt_id} Done✅")