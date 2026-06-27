import streamlit as st 
import cohere 
API_KEY = st.secrets["COHERE_API_KEY"]
co = cohere.ClientV2(API_KEY)
st.title("AI Toolkit")
tab1, tab2, tab3, tab4 = st.tabs(["Summarizer", "Content Repurposer", "Cold Email", "Product Description"])
with tab1:
    text = st.text_area("Paste your text here", height=200)

    if st.button("Summarize", key="sum_btn") and text:
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

with tab2:
    text = st.text_area("Paste your content here", height=200)
    if st.button("Repurpose", key="rep_btn") and text:
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
        result=response.message.content[0].text

        
        st.write(result)


with tab3:
    name = st.text_input("prospect's name")
    company=st.text_input("company's name")
    problem= st.text_input("problem ")
    offer=st.text_input("offer")
    if st.button("Generate", key="email_btn") and name and company and problem and offer:
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

with tab4:
    text = st.text_area("Paste your product name, its three features and the target audience")

    if st.button("Generate", key="desc_btn") and text:
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
