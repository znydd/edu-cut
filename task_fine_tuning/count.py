import json

with open("irrelevant.json", "r", encoding='utf-8') as f:
    loaded_file = json.load(f)

print(len(loaded_file))