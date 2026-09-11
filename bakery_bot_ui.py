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
from supabase import create_client

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Business Chatbot Builder")

st.title("Business Chatbot Builder")

business_name = st.text_input("Business name")
slug = st.text_input("Web address name (letters/numbers only, no spaces)", placeholder="e.g. sweettreats")

menu_df = pd.DataFrame({
    "Item": [""],
    "Price": [0],
    "Ingredients": [""]
})
menu = st.data_editor(menu_df, num_rows="dynamic")
contact = st.text_input("Contact email")
address = st.text_input("Business address")

fulfillment_options = st.selectbox(
    "Fulfillment options offered",
    ["Pickup only", "Delivery only", "Both pickup and delivery"]
)

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
        business_data = {
            "slug": slug,
            "business_name": business_name,
            "contact_email": contact,
            "address": address,
            "fulfillment_options": fulfillment_options,
            "delivery_info": delivery_info,
            "faq_info": faq_info,
            "business_hours": business_hours,
            "advance_notice": advance_notice,
            "sold_out_items": sold_out_items,
            "social_link": social_link,
            "menu": menu.to_dict(orient="records")
        }
        supabase.table("businesses").upsert(business_data, on_conflict="slug").execute()

        if fulfillment_options == "Pickup only":
            fulfillment_instructions = f"""This business offers PICKUP ONLY -- do not offer, mention, or ask about delivery under any circumstances. Do NOT ask the customer for a delivery address. Pickup happens at the business address: {address}."""
        elif fulfillment_options == "Delivery only":
            fulfillment_instructions = f"""This business offers DELIVERY ONLY -- do not offer or mention pickup. Ask the customer for their delivery address."""
        else:
            fulfillment_instructions = f"""This business offers BOTH pickup and delivery. Ask the customer which they'd prefer. If pickup, no address is needed (pickup is at {address}). If delivery, ask for their delivery address."""

        prompt = f"""You are a friendly ordering assistant for {business_name}.
You know the menu includes {menu}, including each item's price and ingredients. If a customer asks what something is made of or about allergens, answer using the ingredients listed.
The business address is {address}.
Delivery and pickup details: {delivery_info}
{fulfillment_instructions}
Frequently asked questions: {faq_info}
Business hours: {business_hours}
The current date and time is: {current_time_str}. Use this to tell customers if the business is currently open or closed, and to sanity-check any pickup/delivery date they request.
Advance notice required for custom orders: {advance_notice}. Before confirming any requested date/time, explicitly calculate the number of hours between the current date/time and the requested date/time, state that calculation to yourself, and compare it against the advance notice requirement. Do not skip this step. If the requested time is sooner than required, politely warn the customer it may not be possible and ask if they'd like to proceed anyway or pick a later date.
Items that are OUT OF STOCK today and must NOT be offered or confirmed: {sold_out_items if sold_out_items else "none"}.
If asked about something outside this, direct customers to {contact}.
Speak in a warm, polite, and helpful tone, with a bit of natural personality and warmth, like a friendly local shopkeeper -- not robotic or overly formal.

If a customer orders a large quantity (for example, more than 10 of an item, or mentions an event/party/wholesale), treat this as a BULK order: mention that bulk orders may need extra lead time and ask if they'd like a deposit conversation, rather than confirming it exactly like a small retail order.

The business's social media / website link is: {social_link if social_link else "not provided"}. Mention it naturally when relevant (e.g. if a customer asks to see photos, or wants to follow the business) -- don't force it into every message.

Customers may write to you in English, Hindi, or Hinglish (a natural mix of Hindi and English, written in Roman script). Always reply in the same style the customer is using, naturally. Don't force pure English or pure Hindi if the customer is mixing languages.

If a customer asks for an item that is NOT on the menu, do not just say no and move on. Let them know that exact item isn't on the current menu, but that you'll check with the business owner about whether it could be made available, and that you'll follow up to confirm. Do NOT add off-menu items to the order, the ORDER_SUMMARY items list, or the estimated total -- only confirmed, on-menu items go in there. If the customer also ordered other items that ARE on the menu in the same message, proceed normally with those and separately mention that the off-menu item needs an owner check.

You can also take orders. When a customer wants to order something, ask any clarifying questions you need: quantity, size, flavor, customizations (like "no nuts" or a message written on a cake), and the date/time they want it, following the fulfillment rules above. Before the order is confirmed, also ask for the customer's name and a phone number or email so the business can reach them if needed. Use the menu prices to calculate a running estimated total.

Before setting "status" to "confirmed", you must have ALL of the following explicitly confirmed with the customer -- do not assume, guess, or let any of them quietly drop as the conversation moves on:
- Every item, with quantity
- Size/weight where relevant to the item
- Any customizations (explicitly confirmed, even if the answer is "none")
- Fulfillment method (pickup or delivery, per the options actually offered)
- Requested date/time
- Customer name
- Customer contact info (phone or email)
If ANY of these is missing or still unspecified, do NOT confirm the order -- keep "status" as "in_progress" and ask for whatever is missing next.

Once you have enough detail on the CURRENT state of their order (even if it's not finished, even if they might add more), append a hidden summary block to the END of your reply in exactly this format, with no other text after it:

ORDER_SUMMARY: {{"items": [{{"item": "name", "quantity": 1, "customizations": "notes or empty string"}}], "fulfillment": "pickup or delivery or unspecified", "order_type": "retail or bulk", "requested_datetime": "date/time text or empty string", "estimated_total": 0, "customer_name": "name or empty string", "customer_contact": "phone or email or empty string", "status": "in_progress or confirmed"}}

Only set "status" to "confirmed" once the customer has explicitly confirmed AND every field in the checklist above is filled in. Always include ALL items discussed so far in this block, not just the newest one, so it reflects the full running order. If there is no order-related content yet, do not include this block at all."""
        st.session_state.messages = [{"role": "system", "content": prompt}]
        st.session_state.display_messages = []
        st.session_state.current_order = None
        st.session_state.order_email_sent = False
        st.session_state.order_number = None
        st.session_state.orders_this_session = 0


def get_missing_order_fields(order):
    """Server-side backstop: independently verify a parsed ORDER_SUMMARY has
    everything required before we ever trust status == 'confirmed'."""
    missing = []

    items = order.get("items", [])
    if not items:
        missing.append("items")
    else:
        if any(not item.get("item") for item in items):
            missing.append("item name")
        if any(
            not isinstance(item.get("quantity"), (int, float)) or item.get("quantity", 0) <= 0
            for item in items
        ):
            missing.append("item quantity")

    if order.get("fulfillment") not in ("pickup", "delivery"):
        missing.append("fulfillment method")

    if not order.get("requested_datetime"):
        missing.append("requested date/time")

    if not order.get("customer_name"):
        missing.append("customer name")

    if not order.get("customer_contact"):
        missing.append("customer contact")

    total = order.get("estimated_total")
    if not isinstance(total, (int, float)) or total <= 0:
        missing.append("estimated total")

    return missing


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

    customer_contact = order.get("customer_contact", "")
    whatsapp_link = None
    if "@" not in customer_contact:
        digits_only = re.sub(r"\D", "", customer_contact)
        if len(digits_only) >= 10:
            whatsapp_link = f"https://wa.me/{digits_only}"
    if whatsapp_link:
        body_lines.append(f"Message customer on WhatsApp: {whatsapp_link}")

    body = "\n".join(body_lines)

    msg = MIMEText(body)
    msg["Subject"] = f"New Order #{order_number} - {business_name}"
    msg["From"] = st.secrets["EMAIL_ADDRESS"]
    msg["To"] = business_email

    if "@" in customer_contact:
        msg["Reply-To"] = customer_contact

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(st.secrets["EMAIL_ADDRESS"], st.secrets["EMAIL_PASSWORD"])
        server.send_message(msg)


if st.session_state.get("messages"):
    st.title(f"{business_name} Chatbot")

    for message in st.session_state.get("display_messages", []):
        with st.chat_message(message["role"]):
            st.write(message["content"])

    user_input = st.chat_input("Type your message...")

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        st.session_state.display_messages.append({"role": "user", "content": user_input})

        with st.chat_message("user"):
            st.write(user_input)

        response = co.chat(
            model="command-r-plus-08-2024",
            messages=st.session_state.messages
        )

        bot_reply = response.message.content[0].text

        order_match = re.search(r"ORDER_SUMMARY:\s*(\{.*\})", bot_reply, re.DOTALL)
        display_reply = bot_reply
        if order_match:
            display_reply = bot_reply[:order_match.start()].strip()
            try:
                parsed_order = json.loads(order_match.group(1))

                # Server-side backstop: don't trust the model's own "confirmed"
                # label. If required fields are missing, force it back to
                # in_progress before it can ever trigger the email.
                if parsed_order.get("status") == "confirmed":
                    missing_fields = get_missing_order_fields(parsed_order)
                    if missing_fields:
                        parsed_order["status"] = "in_progress"

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
        st.session_state.display_messages.append({"role": "assistant", "content": display_reply})

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

        st.divider()
        if st.button("Start New Order"):
            for key in [
                "messages", "display_messages", "current_order",
                "order_email_sent", "order_number"
            ]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

    st.caption("Powered by [Your Tool Name]")
