import streamlit as st
import cohere
import pandas as pd
import json
import re
import random
import smtplib
from datetime import datetime
from email.mime.text import MIMEText

API_KEY = st.secrets["COHERE_API_KEY"]
co = cohere.ClientV2(API_KEY)

st.set_page_config(page_title="Business Chatbot Builder")

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

delivery_info = st.text_area(
    "Delivery / pickup info",
    placeholder="e.g. Pickup available Tue-Sat 10am-6pm. Delivery within 5 miles, $5 fee."
)
faq_info = st.text_area(
    "FAQ / common questions",
    placeholder="e.g. Q: Do you offer gluten-free? A: Yes, ask about our GF options."
)
business_hours = st.text_input(
    "Business hours",
    placeholder="e.g. Tue-Sat 9am-7pm, closed Sun-Mon"
)
advance_notice = st.text_input(
    "Advance notice required for custom orders",
    placeholder="e.g. 48 hours"
)
sold_out_items = st.text_input(
    "Out of stock today (comma separated, leave blank if none)",
    placeholder="e.g. Red velvet cake, Croissants"
)
menu_photos = st.file_uploader(
    "Menu photos (optional)",
    accept_multiple_files=True,
    type=["png", "jpg", "jpeg"]
)
social_link = st.text_input(
    "Instagram / website link (optional)",
    placeholder="e.g. instagram.com/yourbakery"
)

if menu_photos:
    st.write("Menu photo previews:")
    st.image(menu_photos, width=150)

if st.button("Start Chat"):
    at_position = contact.find("@")
    dot_position = contact.find(".")
    if at_position == -1 or dot_position < at_position:
        st.error("Please enter a valid email")
    else:
        current_time_str = datetime.now().strftime("%A, %Y-%m-%d %I:%M %p")

        prompt = f"""You are a friendly ordering assistant for {business_name}.
You know the menu includes {menu}, including each item's price and ingredients. If a customer asks what something is made of or about allergens, answer using the ingredients listed.
The business address is {address}.
Delivery and pickup details: {delivery_info}
Frequently asked questions: {faq_info}
Business hours: {business_hours}
The current date and time is: {current_time_str}. Use this to tell customers if the business is currently open or closed, and to sanity-check any pickup/delivery date they request.
Advance notice required for custom orders: {advance_notice}. If a customer requests something sooner than this, politely warn them it may not be possible and ask if they'd like to proceed anyway or pick a later date.
Items that are OUT OF STOCK today and must NOT be offered or confirmed: {sold_out_items if sold_out_items else "none"}.
If asked about something outside this, direct customers to {contact}.
Speak in a warm, polite, and helpful tone, with a bit of natural personality and warmth, like a friendly local shopkeeper -- not robotic or overly formal.

If a customer orders a large quantity (for example, more than 10 of an item, or mentions an event/party/wholesale), treat this as a BULK order: mention that bulk orders may need extra lead time and ask if they'd like a deposit conversation, rather than confirming it exactly like a small retail order.

The business's social media / website link is: {social_link if social_link else "not provided"}. Mention it naturally when relevant (e.g. if a customer asks to see photos, or wants to follow the business) -- don't force it into every message.

Customers may write to you in English, Hindi, or Hinglish (a natural mix of Hindi and English, written in Roman script). Always reply in the same style the customer is using, naturally. Don't force pure English or pure Hindi if the customer is mixing languages.

You can also take orders. When a customer wants to order something, ask any clarifying questions you need: quantity, size, flavor, customizations (like "no nuts" or a message written on a cake), whether it's pickup or delivery, and the date/time they want it. Before the order is confirmed, also ask for the customer's name and a phone number or email so the business can reach them if needed. Use the menu prices to calculate a running estimated total.

Once you have enough detail on the CURRENT state of their order (even if it's not finished, even if they might add more), append a hidden summary block to the END of your reply in exactly this format, with no other text after it:

ORDER_SUMMARY: {{"items": [{{"item": "name", "quantity": 1, "customizations": "notes or empty string"}}], "fulfillment": "pickup or delivery or unspecified", "order_type": "retail or bulk", "requested_datetime": "date/time text or empty string", "estimated_total": 0, "customer_name": "name or empty string", "customer_contact": "phone or email or empty string", "status": "in_progress or confirmed"}}

Only set "status" to "confirmed" once the customer has explicitly confirmed AND you have their name and contact info. Always include ALL items discussed so far in this block, not just the newest one, so it reflects the full running order. If there is no order-related content yet, do not include this block at all."""
        st.session_state.messages = [{"role": "system", "content": prompt}]
        st.session_state.current_order = None
        st.session_state.order_email_sent = False
        st.session_state.order_number = None
        st.session_state.orders_this_session = 0


def send_order_email(order, business_name, business_email, order_number):
    """Send the confirmed order details to the business owner's inbox."""
    body_lines = [f"New confirmed order #{order_number} for {business_name}:", ""]
    for item in order.get("items", []):
        line = f"- {item.get('quantity', 1)} x {item.get('item', 'Unknown')}"
        if item.get("customizations"):
            line += f" ({item['customizations']})"
        body_lines.append(line)
    body_lines.append("")
    body_lines.append(f"Order type: {order.get('order_type', 'retail')}")
    body_lines.append(f"Requested date/time: {order.get('requested_datetime', 'not specified')}")
    body_lines.append(f"Estimated total: {order.get('estimated_total', 'N/A')}")
    body_lines.append(f"Fulfillment: {order.get('fulfillment', 'unspecified')}")
    body_lines.append("")
    body_lines.append(f"Customer name: {order.get('customer_name', 'not provided')}")
    body_lines.append(f"Customer contact: {order.get('customer_contact', 'not provided')}")
    body = "\n".join(body_lines)

    msg = MIMEText(body)
    msg["Subject"] = f"New Order #{order_number} - {business_name}"
    msg["From"] = st.secrets["EMAIL_ADDRESS"]
    msg["To"] = business_email

    customer_contact = order.get("customer_contact", "")
    if "@" in customer_contact:
        msg["Reply-To"] = customer_contact

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(st.secrets["EMAIL_ADDRESS"], st.secrets["EMAIL_PASSWORD"])
        server.send_message(msg)


if st.session_state.get("messages"):
    st.title(f"{business_name} Chatbot")

    with st.sidebar:
        st.caption(f"Orders this session: {st.session_state.get('orders_this_session', 0)}")
        st.subheader("Current Order")
        order = st.session_state.get("current_order")
        if order and order.get("items"):
            for item in order["items"]:
                line = f"- {item.get('quantity', 1)} x {item.get('item', 'Unknown')}"
                if item.get("customizations"):
                    line += f" ({item['customizations']})"
                st.write(line)
            st.write(f"**Requested for:** {order.get('requested_datetime', 'not specified')}")
            st.write(f"**Estimated total:** {order.get('estimated_total', 'N/A')}")
            st.write(f"**Fulfillment:** {order.get('fulfillment', 'unspecified')}")
            if order.get("status") == "confirmed":
                st.success(f"Order #{st.session_state.get('order_number')} confirmed")
            else:
                st.info("Order in progress")
        else:
            st.write("No order yet")

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

        order_match = re.search(r"ORDER_SUMMARY:\s*(\{.*\})\s*$", bot_reply, re.DOTALL)
        display_reply = bot_reply
        if order_match:
            display_reply = bot_reply[:order_match.start()].strip()
            try:
                parsed_order = json.loads(order_match.group(1))
                st.session_state.current_order = parsed_order

                if (
                    parsed_order.get("status") == "confirmed"
                    and not st.session_state.get("order_email_sent", False)
                ):
                    if not st.session_state.get("order_number"):
                        st.session_state.order_number = random.randint(1000, 9999)

                    send_order_email(
                        parsed_order,
                        business_name,
                        contact,
                        st.session_state.order_number
                    )
                    st.session_state.order_email_sent = True
                    st.session_state.orders_this_session = st.session_state.get("orders_this_session", 0) + 1

                    display_reply += f"\n\n**Your order #{st.session_state.order_number} is confirmed! We'll be in touch shortly.**"

            except json.JSONDecodeError:
                pass

        with st.chat_message("assistant"):
            st.write(display_reply)

        st.session_state.messages.append({"role": "assistant", "content": bot_reply})

    st.caption("Powered by [Your Tool Name]")
