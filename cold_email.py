
import streamlit as st
import cohere
API_KEY = st.secrets["COHERE_API_KEY"]
co = cohere.ClientV2(API_KEY)

st.title("cold email")
name = st.text_input("prospect's name")
company=st.text_input("company's name")
problem= st.text_input("problem ")
offer=st.text_input("offer")
if st.button("Generate") and name and company and problem and offer:
    prompt = f""" take the {name} {company} {problem} {offer} and write 3 emails                                                                      ---FORMAL---
    professional, respectful, clear
    ---CASUAL---
    friendly, conversational
    ---PUNCHY---
    very short, under 75 words, one clear action at the end
    """
    response = co.chat(
    model="command-r-plus-08-2024",
    messages=[{"role": "user", "content": prompt}]
    )
    result = response.message.content[0].text
    st.write(result)
