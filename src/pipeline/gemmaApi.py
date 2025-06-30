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
        You are an expert data summarization engine. Your function is to analyze a sequence of pre-defined video clips and create a corresponding compact JSON summary object for each one. This output will be used as a searchable index for a subsequent AI task, so clarity and density are paramount.

        ### CONTEXT & INPUT STRUCTURE ###
        I am providing you with the full content of an educational video, pre-processed and structured as a series of interleaved data chunks. You will receive the data for each 10-second segment sequentially: first, all the keyframe images for that segment, followed by a text block containing all the subtitles for that same segment.

        ### PRIMARY OBJECTIVE ###
        Your mission is to process **each 10-second segment** from the input and generate **one corresponding JSON summary object** for it. Do not combine information across segments.

        For each segment, you must synthesize the visual and spoken information into a concise summary and extract the most important concepts for every video chunk and timestamps.

        Your final output must be a single, valid JSON array `[ { ... }, { ... } ]` containing one summary object for each input segment you were given.

        ### REQUIRED JSON STRUCTURE (for each object) ###
        {
          "chunk_timestamps": "string | The time range for this chunk, taken directly from the input context (e.g., '0-10s', '10-20s').",
          "summary_of_content": "string | A dense, 1-2 sentence summary explaining the key information presented in this 10-second chunk. Synthesize both what is said and what is shown.",
          "key_concepts_and_visuals": "array[string] | A list of 3-5 of the most important and specific keywords, concepts, or visual elements mentioned or shown in this chunk."
        }

        ---
        ---

        ### INPUT DATA ###

        (Here, you will provide your interleaved sequence of frames and subtitles for the entire video.)""" 

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
resp = ""
for chunk in response:
    out_token = chunk.choices[0].delta.content
    if out_token is not None: 
        resp+=out_token
        print(out_token, end="")
print("\n")
query = "On which sections the instructor is talking about gradients?"
out2 = [{
   "role": "user",
      "content": [
         {
            "type": "text",
            "text": f"""### ROLE & GOAL ###
You are an intelligent retrieval expert. Your task is to analyze a user's query and find the most relevant sections within a structured list of video content summaries.

### CONTEXT & INPUT STRUCTURE ###
I am providing you with two pieces of information:
1.  **User Query:** The specific question the user is asking.
2.  **Video Content Index:** A JSON array where each object summarizes a 10-second clip from a video. Each object contains `chunk_timestamps`, a `summary_of_content`, and a list of `key_concepts_and_visuals`.

### PRIMARY OBJECTIVE ###
Your mission is to carefully read the User Query and then scan the entire Video Content Index. Identify all the `chunk_timestamps` that contain information relevant to answering the query.

Your final output must be a single, valid JSON object containing a list of the relevant timestamp strings. If no sections are relevant, return an empty list.

### REQUIRED JSON STRUCTURE ###
{{
  "relevant_chunks": "array[string] | A list of the chunk_timestamps that directly address the user's query (e.g., ['10-20s', '30-40s'])."
}}

---
---

### INPUT DATA ###

#### User Query ####
{query}

#### Video Content Index ####
{resp}
                    """
         }
      ]
   
}]

response2 = client.chat.completions.create(
  model="gemma-3-4b-it",
  messages=out2,
  stream=True
)

for chunk in response2:
    out_token = chunk.choices[0].delta.content
    if out_token is not None: 
        print(out_token, end="")
print("\n")