import streamlit as st
import cohere
import json

API_KEY = st.secrets["COHERE_API_KEY"]
co = cohere.ClientV2(API_KEY)

st.title("Meeting Notes Tool")
text = st.text_area("Paste your meeting notes here", height=200)

if st.button("Extract Notes") and text:
    prompt = f"""You are a meeting notes extractor. Take these notes and return exactly this JSON and nothing else:
{{"summary": "...", "action_items": ["person: task"], "deadlines": ["..."], "key_decisions": ["..."]}}
No extra text. Just the JSON.

Meeting notes: {text}"""

    response = co.chat(
        model="command-r-plus-08-2024",
        messages=[{"role": "user", "content": prompt}]
    )
    raw = response.message.content[0].text
    data = json.loads(raw)

    st.subheader("Summary")
    st.write(data["summary"])
    st.subheader("Action Items")
    for item in data["action_items"]:
        st.write("✅", item)
    st.subheader("Deadlines")
    for d in data["deadlines"]:
        st.write("📅", d)
    st.subheader("Key Decisions")
    for k in data["key_decisions"]:
        st.write("🔑", k)