import streamlit as st
import cohere
import json

API_KEY = ""
co = cohere.ClientV2(API_KEY)

system_prompt = """You are a tone rewriter. When given a text, return exactly this JSON format and nothing else:
{"smirky": "...", "flirty": "...", "weird": "..."}
No extra text. No markdown. Just the raw JSON."""

text =  st.text_area("Enter a text: ")

if st.button("Rewrite"):
    response = co.chat(
        model="command-r-plus-08-2024",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text}
        ]
    )

    raw = response.message.content[0].text
    data = json.loads(raw)

    st.write("Smirky:", data["smirky"])
    st.write("Flirty:", data["flirty"])
    st.write("Weird:", data["weird"])