import streamlit as st
import cohere
import json

API_KEY = st.secrets["COHERE_API_KEY"]
co = cohere.ClientV2(API_KEY)

st.title("Business Idea Validator")

business_idea = st.text_area("Your business idea")
investment = st.text_input("Your budget")
target_audience = st.text_input("Target audience")
location = st.text_input("Where are you launching?")

if st.button("Validate"):
    prompt = f"""You are a business idea validator. Given the following information:
Business Idea: {business_idea}
Investment Budget: {investment}
Target Audience: {target_audience}
Location: {location}

Return exactly this JSON and nothing else:
{{"viability_score": "X/10", "strengths": ["...", "...", "..."], "weaknesses": ["...", "...", "..."], "biggest_competitor": "...", "pivot_suggestion": "..."}}
No extra text. Just the JSON."""

    response = co.chat(
        model="command-r-plus-08-2024",
        messages=[{"role": "user", "content": prompt}]
    )
    raw = response.message.content[0].text
    data = json.loads(raw)

    st.metric("Viability Score", data["viability_score"])
    st.subheader("Strengths")
    for s in data["strengths"]:
        st.write("✅", s)
    st.subheader("Weaknesses")
    for w in data["weaknesses"]:
        st.write("❌", w)
    st.subheader("Biggest Competitor")
    st.write(data["biggest_competitor"])
    st.subheader("Pivot Suggestion")
    st.write(data["pivot_suggestion"])