import streamlit as st
import cohere

API_KEY = st.secrets["COHERE_API_KEY"]
co = cohere.ClientV2(API_KEY)
st.title("Product Description Generator")
text = st.text_area("Paste your product name, its three features and the target audience")

if st.button("Generate") and text:
    prompt = f"""you have to write 3 product descriptions in plain text, no JSON, no code, no extra explanation
    DESCRIPTION: {text}

    write:
    ---FOMO---
    create urgency, fear of missing out, make them feel they need it now

    ---BUDGET---
    value focused, practical, highlight savings

    ---FUN---
    playful, energetic, use humor
     """


    response = co.chat(model="command-r-plus-08-2024", messages=[{"role": "user", "content": prompt}])
    result = response.message.content[0].text
    st.write(result)
