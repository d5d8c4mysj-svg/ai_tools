
import cohere
import json

API_KEY = ""
co = cohere.ClientV2(API_KEY)

system_prompt = """You are an Instagram caption generator. When given a topic, return exactly this JSON format and nothing else: {"funny": "...", "professional": "...", "catchy": "..."} No extra text. Just the JSON."""
topic = input("Enter a topic: ")

response = co.chat(
    model="command-r-plus-08-2024",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": topic}
    ]
)

raw = response.message.content[0].text
data = json.loads(raw)

print("Funny:", data["funny"])
print("Professional:", data["professional"])
print("Catchy:", data["catchy"])