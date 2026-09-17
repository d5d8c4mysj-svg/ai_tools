import streamlit as st
import cohere
import pandas as pd
import json
import re
import random
import resend
import hashlib
from datetime import datetime

API_KEY = st.secrets["COHERE_API_KEY"]
resend.api_key = st.secrets["RESEND_API_KEY"]
co = cohere.ClientV2(API_KEY)
from supabase import create_client

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- Read mode + slug from the URL ---
params = st.query_params
slug_from_url = params.get("slug", "")
mode = params.get("mode", "customer")  # defaults to customer view

st.set_page_config(page_title="Business Chatbot Builder")

MAX_MESSAGES_PER_SESSION = 40  # caps Cohere API spend per customer session


def parse_advance_notice_hours(text):
    """Extract a number of hours from a free-text advance-notice setting
    like '48 hours', '2 days', or '1 week'. Returns None if it can't be
    parsed, so callers know to skip the check rather than guess."""
    if not text:
        return None
    match = re.search(r"(\d+(?:\.\d+)?)\s*(hour|hr|day|week)", text, re.IGNORECASE)
    if not match:
        return None
    value = float(match.group(1))
    unit = match.group(2).lower()
    if unit.startswith("day"):
        return value * 24
    if unit.startswith("week"):
        return value * 24 * 7
    return value  # hours or hr


def check_advance_notice(requested_datetime_iso, advance_notice_text):
    """Independently verify (in real Python, not AI arithmetic) whether a
    requested order date/time actually satisfies the business's advance
    notice requirement. Returns a dict describing what was found -- this
    is a backstop against the AI miscalculating the gap itself."""
    if not requested_datetime_iso:
        return {"checked": False}

    try:
        requested_dt = datetime.fromisoformat(requested_datetime_iso)
    except (ValueError, TypeError):
        return {"checked": False}

    required_hours = parse_advance_notice_hours(advance_notice_text)
    if required_hours is None:
        return {"checked": False}

    actual_hours = (requested_dt - datetime.now()).total_seconds() / 3600
    return {
        "checked": True,
        "ok": actual_hours >= required_hours,
        "actual_hours": round(actual_hours, 1),
        "required_hours": required_hours,
    }


def get_missing_order_fields(order):
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


def normalize_and_validate_slug(raw_slug):
    slug = raw_slug.strip().lower()
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"[^a-z0-9-]", "", slug)
    slug = re.sub(r"-{2,}", "-", slug).strip("-")
    if not slug:
        return None, "Please enter a web address name using letters and numbers."
    if len(slug) < 3:
        return None, "Web address name must be at least 3 characters."
    if len(slug) > 50:
        return None, "Web address name must be 50 characters or fewer."
    return slug, None


def upload_menu_photos(slug, uploaded_files):
    urls = []
    for photo in uploaded_files:
        safe_name = re.sub(r"[^a-zA-Z0-9._-]", "_", photo.name)
        path = f"{slug}/{int(datetime.now().timestamp())}_{safe_name}"
        try:
            supabase.storage.from_("menu-photos").upload(
                path,
                photo.getvalue(),
                {"content-type": photo.type}
            )
            public_url = supabase.storage.from_("menu-photos").get_public_url(path)
            urls.append(public_url)
        except Exception:
            st.warning(f"Couldn't upload {photo.name} -- the rest of your bot was still saved.")
    return urls


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def get_business(slug):
    try:
        result = supabase.table("businesses").select("*").eq("slug", slug).execute()
    except Exception:
        st.error("Something went wrong looking that up. Please try again in a moment.")
        return None
    if result.data:
        return result.data[0]
    return None


def send_order_email(order, business_name, business_email, order_number):
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

    email_params = {
        "from": "onboarding@resend.dev",
        "to": business_email,
        "subject": f"New Order #{order_number} - {business_name}",
        "text": body,
    }
    if "@" in customer_contact:
        email_params["reply_to"] = customer_contact

    resend.Emails.send(email_params)


def run_chatbot(business):
    business_name = business["business_name"]
    contact = business["contact_email"]
    address = business["address"]
    fulfillment_options = business["fulfillment_options"]
    delivery_info = business["delivery_info"]
    faq_info = business["faq_info"]
    business_hours = business["business_hours"]
    advance_notice = business["advance_notice"]
    sold_out_items = business["sold_out_items"]
    social_link = business["social_link"]
    menu_photo_urls = business.get("menu_photo_urls") or []
    menu = business["menu"]

    if "messages" not in st.session_state:
        current_time_str = datetime.now().strftime("%A, %Y-%m-%d %I:%M %p")

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
Advance notice required for custom orders: {advance_notice}. When a customer requests a date/time, always work out and state to the customer in your visible reply the exact number of hours between now ({current_time_str}) and their requested date/time, and compare that to the advance notice requirement -- do this out loud in the conversation, not silently, so the number is always visible and can be checked. If the requested time is sooner than required, politely warn the customer it may not be possible and ask if they'd like to proceed anyway or pick a later date.
Items that are OUT OF STOCK today and must NOT be offered or confirmed: {sold_out_items if sold_out_items else "none"}.
If asked about something outside this, direct customers to {contact}.
Speak in a warm, polite, and helpful tone, with a bit of natural personality and warmth, like a friendly local shopkeeper -- not robotic or overly formal.

Only treat an order as BULK if the customer orders MORE THAN 10 of a single item, or explicitly mentions an event, party, or wholesale quantity. A normal order of a few items (even 2-3 of something) is always a regular RETAIL order, not bulk -- do not mention deposits or extra lead time for ordinary small orders.

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

ORDER_SUMMARY: {{"items": [{{"item": "name", "quantity": 1, "customizations": "notes or empty string"}}], "fulfillment": "pickup or delivery or unspecified", "order_type": "retail or bulk", "requested_datetime": "date/time text or empty string", "requested_datetime_iso": "YYYY-MM-DDTHH:MM:SS in 24-hour time, based on the current date/time given above, or empty string if not yet known", "estimated_total": 0, "customer_name": "name or empty string", "customer_contact": "phone or email or empty string", "status": "in_progress or confirmed"}}

The requested_datetime_iso field must always be a precise, computed date and time (year-month-day and hour:minute:second), worked out from the current date/time given above plus whatever the customer said (e.g. "tomorrow at 2pm", "in two days", "next Saturday") -- never leave it as vague text; convert it to an exact timestamp.

Only set "status" to "confirmed" once the customer has explicitly confirmed AND every field in the checklist above is filled in. Always include ALL items discussed so far in this block, not just the newest one, so it reflects the full running order. If there is no order-related content yet, do not include this block at all."""

        st.session_state.messages = [{"role": "system", "content": prompt}]
        st.session_state.display_messages = []
        st.session_state.current_order = None
        st.session_state.order_email_sent = False
        st.session_state.order_number = None
        st.session_state.orders_this_session = 0

    st.title(f"{business_name} Chatbot")

    if menu_photo_urls:
        with st.expander("See menu photos", expanded=False):
            st.image(menu_photo_urls, width=150)

    for message in st.session_state.get("display_messages", []):
        with st.chat_message(message["role"]):
            st.write(message["content"])

    user_input = st.chat_input("Type your message...")

    message_count = len(st.session_state.get("display_messages", []))
    if message_count >= MAX_MESSAGES_PER_SESSION:
        st.warning(
            f"This chat has reached its message limit for one session. "
            f"Please contact {contact} directly, or start a new order below."
        )
        user_input = None

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        st.session_state.display_messages.append({"role": "user", "content": user_input})

        with st.chat_message("user"):
            st.write(user_input)

        try:
            with st.spinner("Typing..."):
                response = co.chat(
                    model="command-r-plus-08-2024",
                    messages=st.session_state.messages
                )
            bot_reply = response.message.content[0].text
        except Exception:
            with st.chat_message("assistant"):
                st.write("Sorry, I'm having trouble responding right now. Please try again in a moment, or contact the business directly.")
            st.session_state.messages.pop()
            st.session_state.display_messages.pop()
            st.stop()

        order_match = re.search(r"ORDER_SUMMARY:\s*(\{.*\})", bot_reply, re.DOTALL)
        display_reply = bot_reply
        if order_match:
            display_reply = bot_reply[:order_match.start()].strip()
            try:
                parsed_order = json.loads(order_match.group(1))

                if parsed_order.get("status") == "confirmed":
                    missing_fields = get_missing_order_fields(parsed_order)
                    if missing_fields:
                        parsed_order["status"] = "in_progress"

                # Second backstop: independently verify the advance-notice
                # math in real Python, rather than trusting the AI's own
                # arithmetic. If the AI wrongly confirmed an order that's
                # actually too soon, correct it here before it ever reaches
                # the sidebar or triggers an email.
                notice_check = check_advance_notice(
                    parsed_order.get("requested_datetime_iso"),
                    advance_notice
                )
                notice_warning = None
                if parsed_order.get("status") == "confirmed" and notice_check.get("checked") and not notice_check.get("ok"):
                    parsed_order["status"] = "in_progress"
                    notice_warning = (
                        f"Actually, let me double check that -- that's only about "
                        f"{notice_check['actual_hours']:.1f} hours from now, and we need "
                        f"{notice_check['required_hours']:.0f} hours' notice for this. "
                        f"Could you choose a later date/time, or confirm you'd still like to proceed?"
                    )

                st.session_state.current_order = parsed_order

                if (
                    parsed_order.get("status") == "confirmed"
                    and not st.session_state.get("order_email_sent", False)
                ):
                    if not st.session_state.get("order_number"):
                        st.session_state.order_number = random.randint(1000, 9999)

                    try:
                        send_order_email(
                            parsed_order,
                            business_name,
                            contact,
                            st.session_state.order_number
                        )
                        st.session_state.order_email_sent = True
                    except Exception:
                        pass

                    st.session_state.orders_this_session = st.session_state.get("orders_this_session", 0) + 1

                    display_reply += f"\n\n**Your order #{st.session_state.order_number} is confirmed! We'll be in touch shortly.**"
                elif notice_warning:
                    display_reply += f"\n\n{notice_warning}"

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


def customer_view():
    slug_input = st.text_input(
        "Enter your bakery's link name",
        value=slug_from_url,
        placeholder="e.g. sweettreats"
    )

    if not slug_input:
        st.info("Enter a slug above, or visit a link like ?slug=sweettreats")
        return

    clean_slug, slug_error = normalize_and_validate_slug(slug_input)
    if slug_error:
        st.error("That doesn't look like a valid link name.")
        return

    business = get_business(clean_slug)
    if not business:
        st.error("No business found with that slug.")
        return

    run_chatbot(business)


# ---------------------------------------------------------------------------
# QUICK UPDATE VIEW -- a fast, lightweight way for an owner to mark items
# sold out during the day, without opening the full builder form.
# ---------------------------------------------------------------------------

def quick_update_view():
    st.title("Quick Stock Update")
    st.caption("Mark items as sold out for today. This won't change anything else about your bot.")

    slug_input = st.text_input(
        "Web address name",
        value=slug_from_url,
        placeholder="e.g. sweettreats"
    )
    password = st.text_input("Password", type="password")

    if not slug_input or not password:
        st.info("Enter your slug and password to continue.")
        return

    clean_slug, slug_error = normalize_and_validate_slug(slug_input)
    if slug_error:
        st.error(slug_error)
        return

    business = get_business(clean_slug)
    if not business:
        st.error("No business found with that slug.")
        return

    if business.get("admin_password") != hash_password(password):
        st.error("Incorrect password.")
        return

    menu_items = business.get("menu") or []
    if not menu_items:
        st.info("This business doesn't have any menu items yet.")
        return

    current_sold_out = [
        name.strip()
        for name in (business.get("sold_out_items") or "").split(",")
        if name.strip()
    ]

    st.write("Check anything that's sold out right now:")
    newly_sold_out = []
    for item in menu_items:
        item_name = item.get("Item", "")
        if not item_name:
            continue
        checked = st.checkbox(item_name, value=item_name in current_sold_out, key=f"soldout_{item_name}")
        if checked:
            newly_sold_out.append(item_name)

    if st.button("Update"):
        try:
            supabase.table("businesses").update(
                {"sold_out_items": ", ".join(newly_sold_out)}
            ).eq("slug", clean_slug).execute()
        except Exception:
            st.error("Something went wrong updating this. Please try again in a moment.")
        else:
            st.success("Updated! Your bot will now reflect today's availability.")


def owner_view():
    st.title("Business Chatbot Builder")

    business_name = st.text_input("Business name")
    slug = st.text_input(
        "Web address name (letters/numbers only, no spaces)",
        placeholder="e.g. sweettreats"
    )
    password = st.text_input(
        "Password (create one if this is a new bot, or enter your existing password to edit it)",
        type="password"
    )

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

    if st.button("Save My Bakery Bot"):
        at_position = contact.find("@")
        dot_position = contact.find(".")
        clean_slug, slug_error = normalize_and_validate_slug(slug)
        if slug_error:
            st.error(slug_error)
        elif at_position == -1 or dot_position < at_position:
            st.error("Please enter a valid email")
        elif not password:
            st.error("Please create or enter a password for this bot.")
        else:
            existing_business = get_business(clean_slug)

            if existing_business:
                stored_hash = existing_business.get("admin_password")
                if stored_hash != hash_password(password):
                    st.error("Incorrect password for this business. If this is your first time saving, choose a slug that isn't already taken.")
                    st.stop()
                password_hash = stored_hash
            else:
                password_hash = hash_password(password)

            if menu_photos:
                menu_photo_urls = upload_menu_photos(clean_slug, menu_photos)
            else:
                menu_photo_urls = (existing_business or {}).get("menu_photo_urls", [])

            business_data = {
                "slug": clean_slug,
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
                "menu": menu.to_dict(orient="records"),
                "menu_photo_urls": menu_photo_urls,
                "admin_password": password_hash
            }
            try:
                supabase.table("businesses").upsert(business_data, on_conflict="slug").execute()
            except Exception:
                st.error("Something went wrong saving your bot. Please try again in a moment.")
            else:
                st.success("Saved! Share this link with your customers:")
                st.code(f"https://bakery-bot.streamlit.app/?slug={clean_slug}")
                st.caption("Bookmark this link to quickly mark items sold out during the day, without opening this full form:")
                st.code(f"https://bakery-bot.streamlit.app/?mode=quickupdate&slug={clean_slug}")


if mode == "owner":
    owner_view()
elif mode == "quickupdate":
    quick_update_view()
else:
    customer_view()
