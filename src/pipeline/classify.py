import os
from dotenv import load_dotenv
from openai import OpenAI

with open("my_file.txt", "r", encoding="utf-8") as f:
    resp = f.read()

query = (
    "On which sections(can be multiple) the instructor is talking about absolute loss?"
)
out2 = [
    {
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": f"""### ROLE & GOAL ###
You are an intelligent retrieval expert. Your task is to analyze a user's query and find the most relevant sections within a
structured list of video content summaries.

### CONTEXT & INPUT STRUCTURE ###
I am providing you with two pieces of information:
1.  **User Query:** The specific question the user is asking.
2.  **Video Content Index:** A JSON array where each object summarizes a 10-second clip from a video. Each object contains
`chunk_timestamps`, a `summary_of_content`, and a list of `key_concepts_and_visuals`.

### PRIMARY OBJECTIVE ###
Your mission is to carefully read the User Query and then scan the entire Video Content Index. Identify all the
`chunk_timestamps` that contain information relevant to answering the query.

Your final output must be a single, valid JSON object containing a list of the relevant timestamp strings. If no sections 
are relevant, return an empty list.

### REQUIRED JSON STRUCTURE ###
{{
  "relevant_chunks": "array[string] | A list of the chunk_timestamps that directly address the user's query (e.g., ['10-20s',
  '30-40s'])."
}}

---
---

### INPUT DATA ###

#### User Query ####
{query}

#### Video Content Index ####
{resp}
                    """,
            }
        ],
    }
]

load_dotenv()
client = OpenAI(
    api_key=os.getenv("GEMINI_API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)
response2 = client.chat.completions.create(
    model="gemma-3-27b-it", messages=out2, stream=True
)

for chunk in response2:
    out_token = chunk.choices[0].delta.content
    if out_token is not None:
        print(out_token, end="")
print("\n")
