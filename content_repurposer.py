import streamlit as st
import cohere
API_KEY = st.secrets["COHERE_API_KEY"]
co = cohere.ClientV2(API_KEY)
st.title("Content Repurposer")
text = st.text_area("Paste your content here", height=200)
if st.button("Repurpose") and text:
    prompt = f"""Take this content and rewrite it in 4 formats:

    CONTENT: {text}

    Write:
    🐦 TWITTER THREAD: 3-5 tweets, numbered, under 280 chars each
    📸 INSTAGRAM CAPTION: 150 words, conversational, 5 hashtags at end
    💼 LINKEDIN POST: professional, starts with hook, ends with question
    💬 WHATSAPP STATUS: one punchy line under 150 characters"""
    response = co.chat(
    model="command-r-plus-08-2024",
    messages=[{"role": "user", "content": prompt}]
)
result = response.message.content[0].text
st.write(result)
