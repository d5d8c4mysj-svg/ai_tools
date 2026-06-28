import streamlit as st
import cohere
import json

API_KEY = st.secrets["COHERE_API_KEY"]
co = cohere.ClientV2(API_KEY)

st.title("Interview Preparation Tool")
job_title = st.text_input("Your Job Title")
experience = st.text_input("Years of Experience")

if st.button("Prepare"):
    prompt = f"""You are an interview preparation assistant.
Job Title: {job_title}
Years of Experience: {experience}
Return exactly this JSON and nothing else:
{{"questions": ["...", "...", "...", "...", "..."], "answers": ["...", "...", "...", "...", "..."]}}
No extra text. Just the JSON."""

    response = co.chat(
        model="command-r-plus-08-2024",
        messages=[{"role": "user", "content": prompt}]
    )
    raw = response.message.content[0].text
    data = json.loads(raw)

    for i in range(5):
        st.subheader(f"Q{i+1}: {data['questions'][i]}")
        st.write("💡", data['answers'][i])