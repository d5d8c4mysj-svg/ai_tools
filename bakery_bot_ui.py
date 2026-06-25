import streamlit as st
import cohere

API_KEY = ""
co = cohere.ClientV2(API_KEY)

system_prompt = "You are a friendly assistant for Cinnamon Bakery. You know the menu includes cupcakes, cinnamon rolls (our specialty), cakes, donuts, and pastries. You speak in a polite, calm, and warm way, answering questions gently and patiently. If asked about something outside this (like pricing changes, complaints, or custom orders), politely say: I would recommend reaching out to our staff directly at cinnamonbakery@gmail.com"

st.title("Cinnamon Bakery Chatbot")

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": system_prompt}]

for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.write(message["content"])

user_input = st.chat_input("Type your message...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    with st.chat_message("user"):
        st.write(user_input)
    
    response = co.chat(
        model="command-r-plus-08-2024",
        messages=st.session_state.messages
    )
    
    bot_reply = response.message.content[0].text
    
    with st.chat_message("assistant"):
        st.write(bot_reply)
    
    st.session_state.messages.append({"role": "assistant", "content": bot_reply})