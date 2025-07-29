import http.client
import json

# Create the connection to localhost:8080
conn = http.client.HTTPConnection("localhost", 8080)

# Prepare the headers and data
headers = {"Content-Type": "application/json"}
data = {"content": "hello world"}
json_data = json.dumps(data)

# Send the POST request
conn.request("POST", "/embedding", body=json_data, headers=headers)

# Get the response
response = conn.getresponse()
result = response.read().decode()

print("Status:", response.status)
print("Response:", result)
with open("resp.json", "w", encoding="utf-8") as f:
    f.write(result)

# Close the connection
conn.close()
