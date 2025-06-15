import json
from pathlib import Path



def parse_time(timestr):
    if len(timestr) < 8:
        timestr = "00:"+timestr
    h, m, s = map(int, timestr.split(":"))
    
    return int(h * 3600 + m * 60 + s)

# folder_path = Path("full_video")
# files = folder_path.glob("*")  # all files/folders

with open("irrelevant.json", "r", encoding='utf-8') as f:
    loaded_file = json.load(f)


dataset_files = []
for i in range(len(loaded_file)):
    for seg in loaded_file[i]['irrelevant_segments']:
        start_time =  parse_time(seg['start_time'][0:8])
        end_time =  parse_time(seg['end_time'][0:8])
        vid_ln = end_time - start_time
        m, s = divmod(vid_ln, 60)
        if m > 3:
        #  print(f"✅Starting Video: {i}")
        #  print(f"yt_link: {loaded_file[i]['link']}")
         m1, s1 = divmod(start_time, 60)
         m2, s2 = divmod(end_time, 60)
    
         start_time = f"{(m1)}M:{(s1)}S"
         end_time = f"{(m2)}M:{(s2)}S"
         print(f"Start Time: {start_time} -- End Time: {end_time}")
         print(f"Vid length {m}m:{s}s")
        #  print(f"✅Ending Video: {i}")

#     yt_id = loaded_file[i]['link'][32:43]

#     dataset_file = f"{yt_id}.mp4"
#     dataset_files.append(dataset_file)

# for file in files:
#     if str(file)[11:] not in dataset_files:
#         file.unlink()

print(len(loaded_file))