import os
import base64
import json
from dotenv import load_dotenv
from openai import OpenAI



def msg(comb_inp_pth):
    frames_base = "/home/znyd/hacking/edu-cut/src/pre_processing/vid_frames/"
    messages = [
    {
      "role": "user",
      "content": [
        {
           "type": "text",
           "text": """### ROLE & GOAL ###
        You are an expert data processing engine specializing in semantic analysis. Your function is to analyze a sequence of pre-defined video clips and create a corresponding JSON object for each one. Each output object must be a comprehensive, self-contained summary structured for optimal retrieval from a vector database.
        ### CONTEXT & INPUT STRUCTURE ###
        I am providing you with the full content of an educational video, pre-processed and structured as a series of interleaved data chunks. You will receive the data for each 10-second segment sequentially: first, all the keyframe images for that segment, followed by a text block containing all the subtitles for that same segment. You will process all of these sequential chunks to understand the entire video.
        ### PRIMARY OBJECTIVE ###
        Your mission is to process **each 10-second segment** from the input and generate **one corresponding JSON summary object** for it.
        The most critical part of your output is the `llm_explanation` field within each object. This paragraph must be a dense, descriptive summary that synthesizes all the visual and spoken information from its corresponding 10-second clip, making the content fully understandable in isolation. This field is paramount as it will be used for vector embedding.
        Your final output must be a single, valid JSON array `[ { ... }, { ... } ]` containing one summary object for each input segment you were given.
        ### REQUIRED JSON STRUCTURE (for each object) ###
        {
          "chunk_timestamps": "string | The time range for this chunk, which you will infer from the input context (e.g., '0-10s', '10-20s').",
          "llm_explanation": "string | A dense, self-contained descriptive paragraph explaining the key concepts, steps, and visual information presented in this chunk. This text will be used for vector embedding.",
          "keywords": "array[string] | A list of 5-7 of the most relevant keywords that summarize the content of this chunk."
        }
        ---
        ---
        ### INPUT DATA ###
        (The user will now provide the interleaved data for each 10-second segment, starting with the frames and followed by the subtitles for that segment, repeated for the entire video clip.)""" 

        }],
    }
    ]

    with open(comb_inp_pth, 'r', encoding='utf-8') as f:
       loaded_json = json.load(f)

    for seg in loaded_json:
        time_stamps = seg['time_stamps']
        frames = seg['frames']
        subtitle = seg['subtitle']

        messages[0]["content"].append({
              "type": "text",
              "text": f"--- DATA FOR SEGMENT {time_stamps} ---",
            })



        for frame in frames:
            base64_image = encode_image(frames_base+frame)
            messages[0]["content"].append( {
              "type": "image_url",
              "image_url": { "url": f"data:image/png;base64,{base64_image}" },
            })

        subtitle_prompt = f"Subtitles for {time_stamps}:\n"
        
        for sub in subtitle:
            subtitle_prompt+=sub 

        messages[0]["content"].append({
              "type": "text",
              "text": subtitle_prompt,
            })

    return messages

# Function to encode the image
def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')

out = msg("/home/znyd/hacking/edu-cut/src/pre_processing/combined_output.json")

# # File path for JSON output
# json_file_path = "output_data.json"

# # Write the array of dictionaries to a JSON file
# # 'indent=4' makes the JSON output human-readable with 4-space indentation
# with open(json_file_path, 'w') as json_file:
#     json.dump(out, json_file, indent=4)

# print(f"Data written to '{json_file_path}' in JSON format.")

# # --- How to read it back (for verification) ---
# with open(json_file_path, 'r') as json_file:
#     loaded_data = json.load(json_file)

# print("\n--- Loaded Data (from JSON) ---")
# #print(loaded_data)
# print(f"Type of loaded_data: {type(loaded_data)}")
# print(f"Type of first element: {type(loaded_data[0])}")



load_dotenv()
client = OpenAI(
    api_key=os.getenv("GEMINI_API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

# Getting the base64 string

response = client.chat.completions.create(
  model="gemma-3-4b-it",
  messages=out,
  stream=True
)
for chunk in response:
    out_token = chunk.choices[0].delta.content
    if out_token is not None: 
        print(out_token, end="")
print("\n")