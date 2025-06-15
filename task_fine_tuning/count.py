import json

input_file = "irrelevant.json"

with open(input_file, "r", encoding="utf-8") as file:
    loaded_file = json.load(file)
total_file = 0
for i in range(len(loaded_file)):
    vid_cap_len = len(loaded_file[i]["irrelevant_segments"])
    print(f"Caption count for vid_{i:02}: {vid_cap_len}")
    total_file+=vid_cap_len
print(f"Total caption {total_file}")
    
    