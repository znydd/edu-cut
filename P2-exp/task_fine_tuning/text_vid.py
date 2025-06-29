import json

input_file = "irrelevant.json"

with open(input_file, "r", encoding="utf-8") as file:
    loaded_file = json.load(file)

id = 0
for i in range(len(loaded_file)):
    yt_id = loaded_file[i]['link'][32:43]
    for idx, caption in enumerate(loaded_file[i]["irrelevant_segments"]):
        curr_transcript = caption['text_snippet']
        start_time = caption['start_time']
        end_time = caption['end_time'] 
        seg_type = caption['segment_type']
        reasoning = caption['reasoning']
        template = {
          "id": id,
          "video": f"videos/{idx:03}_{yt_id}.mp4",
          "conversations": [
            {
              "from": "human",
              "value": f"This video segment is a part of a long educational video.\n\nCurrent Segment Transcript: \"{curr_transcript}\"\n\nUser Query: Analyze this educational video and detect irrelevant segments that disrupt the learning process. Identify:\n1. Off-topic discussions (personal stories, unrelated chat, admin talks, etc.)\n2. Silent or non-instructional activities (e.g. instructor drawing silently, pauses, technical setups)\nFor each irrelevant segment, provide:\n- start and end timestamps\n-  brief description with reasoning why it is irrelevant"
            },
            {
              "from": "gpt",
              "value": f"Irrelevant Segment Type: {seg_type} \n- Start: {start_time}\n- End: {end_time}\n-Reasoning description: {reasoning}"
            }
          ]
        }
    
        with open("train.jsonl", "a", encoding="utf-8") as f:
            json.dump(template, f)
            f.write('\n')
        id+=1
    print(f"vid_{i:02} Done✅")

print(f"Full Done✅✅")

        
