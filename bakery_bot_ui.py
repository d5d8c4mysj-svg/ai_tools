import streamlit as st
import cohere
import pandas as pd

API_KEY = st.secrets["COHERE_API_KEY"]
co = cohere.ClientV2(API_KEY)

st.title("Business Chatbot Builder")

business_name = st.text_input("Business name")
menu_df = pd.DataFrame({
    "Item": [""],
    "Price": [0],
    "Ingredients": [""]
})
menu = st.data_editor(menu_df, num_rows="dynamic")
contact = st.text_input("Contact email")
address = st.text_input("Business address")

if st.button("Start Chat"):
    at_position = contact.find("@")
    dot_position = contact.find(".")
    if at_position == -1 or dot_position < at_position:
        st.error("Please enter a valid email")
    else:
        prompt = f"""You are a friendly assistant for {business_name}.
You know the menu includes {menu}, including each item's price and ingredients. If a customer asks what something is made of or about allergens, answer using the ingredients listed.
The business address is {address}.
If asked about something outside this, direct customers to {contact}.
Speak in a warm, polite, and helpful tone."""
        st.session_state.messages = [{"role": "system", "content": prompt}]

if st.session_state.get("messages"):
    st.title(f"{business_name} Chatbot")

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
