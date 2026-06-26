import streamlit as st
import cohere

client = cohere.Client("")
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


    response = client.chat(model="command-r-plus-08-2024", message=prompt)
    result = response.text
    st.write(result)