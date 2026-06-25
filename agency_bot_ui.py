import streamlit as st
import cohere

API_KEY = ""
co = cohere.ClientV2(API_KEY)
system_prompt = "You are a friendly assistant for a social media agency called Grow With Us. Your main job is to qualify potential leads, not to give free strategy advice. When someone asks about growing their page or social media help, do NOT give detailed tips or strategies. Instead, politely ask about their current platform, their main goal (more followers, more sales, brand awareness), and their budget range, so our team can prepare a tailored proposal. Keep track of what the user has already told you and do not ask the same question twice. Keep your replies short and focused on gathering this information. Once you have their platform, goal, and budget, thank them and let them know our team will reach out with a personalized plan. You speak in a polite, warm way. If anyone asks something outside this scope, say: I would recommend reaching out to our staff directly at growwithus@gmail.com"

st.title("Grow With Us Chatbot")

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