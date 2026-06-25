import streamlit as st
import cohere

API_KEY = st.secrets["COHERE_API_KEY"]
co = cohere.ClientV2(API_KEY)

st.title("Text Summarizer")
st.write("Paste any text below and get a clean summary.")

text = st.text_area("Paste your text here", height=200)

if st.button("Summarize"):
    prompt = """You are an AI assistant that summarizes text. When given a piece of text, return your response in exactly this format:

SUMMARY: [3 sentences max]

KEY POINTS:
- [point 1]
- [point 2]
- [point 3]

ACTION ITEM: [one clear thing to do]

No extra text. Just follow the format exactly.

Here is the text to summarize: """ + text

    response = co.chat(
        model="command-r-plus-08-2024",
        messages=[{"role": "user", "content": prompt}]
    )
    
    result = response.message.content[0].text
    st.write(result)