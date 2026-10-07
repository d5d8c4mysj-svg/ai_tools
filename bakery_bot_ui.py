import streamlit as st
import cohere
import pandas as pd
import json
import re
import random
import smtplib
import hashlib
import html
from datetime import datetime
from email.mime.text import MIMEText

API_KEY = st.secrets["COHERE_API_KEY"]
co = cohere.ClientV2(API_KEY)
from supabase import create_client

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- Read mode + slug from the URL ---
params = st.query_params
slug_from_url = params.get("slug", "")
mode = params.get("mode", "customer")  # defaults to customer view

st.set_page_config(page_title="Loaf")

# ---------------------------------------------------------
# LOAF DESIGN — mobile-first storefront
# ---------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');

:root {
    --chocolate:#633229; --chocolate-dark:#35211D; --pink:#E9A9A8;
    --sage:#B7B58A; --vanilla:#F4EBC8; --cream:#FFF9F3;
    --white:#FFFFFF; --ink:#252321; --muted:#706B67; --border:#E8E0DB;
}
html, body, [class*="css"] { font-family:"Inter",sans-serif; }
.stApp { background:var(--cream); color:var(--ink); }
.block-container { max-width:980px; padding-top:2rem; padding-bottom:4rem; }
#MainMenu, footer { visibility:hidden; }

.loaf-topbar { display:flex; align-items:center; justify-content:space-between; padding-bottom:9px; margin-bottom:14px; border-bottom:1px solid var(--border); }
.loaf-wordmark { font-family:"Manrope",sans-serif; font-size:13px; font-weight:800; letter-spacing:.15em; color:var(--chocolate); }
.loaf-topnote { font-size:12px; color:var(--muted); }
.bakery-name { font-family:"Manrope",sans-serif; font-size:46px; font-weight:800; letter-spacing:-.045em; line-height:1.04; color:var(--ink); margin:0 0 10px; }
.bakery-subtitle { max-width:650px; color:var(--muted); font-size:15px; line-height:1.5; margin:0 0 12px; }
.brand-dot { width:42px; height:4px; border-radius:999px; background:var(--pink); margin-bottom:16px; }

.assistant-intro { margin:12px 0 7px; padding-top:11px; border-top:1px solid var(--border); }
.assistant-title { font-family:"Manrope",sans-serif; font-size:21px; font-weight:800; letter-spacing:-.025em; color:var(--ink); margin-bottom:5px; }
.assistant-copy { color:var(--muted); font-size:13px; line-height:1.55; }

.chat-row { display:flex; width:100%; margin:8px 0; }
.chat-row.user { justify-content:flex-end; }
.chat-row.assistant { justify-content:flex-start; }
.chat-wrap { max-width:74%; }
.chat-name { font-size:10px; font-weight:700; color:var(--muted); margin:0 0 4px 2px; }
.chat-row.user .chat-name { text-align:right; margin-right:2px; }
.chat-bubble { font-family:"Inter",sans-serif; font-size:14px; line-height:1.55; padding:11px 14px; border-radius:15px; }
.chat-row.assistant .chat-bubble { background:var(--white); color:var(--ink); border:1px solid var(--border); border-bottom-left-radius:5px; }
.chat-row.user .chat-bubble { background:var(--chocolate); color:#fff; border:1px solid var(--chocolate); border-bottom-right-radius:5px; }

[data-testid="stChatMessage"] { display:none; }
[data-testid="stChatInput"] {
    max-width:680px;
    margin:0 auto 10px auto;
    border:1px solid #E6C9C7;
    border-radius:10px;
    background:#FFFDFC;
    box-shadow:0 5px 16px rgba(53,33,29,.045);
}
[data-testid="stChatInput"] textarea {
    min-height:42px !important;
    height:42px !important;
    padding-top:10px !important;
    padding-bottom:8px !important;
    font-size:13px !important;
}
[data-testid="stChatInput"] button {
    width:34px !important;
    height:34px !important;
    min-height:34px !important;
    border-radius:8px !important;
}
[data-testid="stBottom"] {
    background:rgba(255,249,243,.96) !important;
    padding-top:8px !important;
    padding-bottom:4px !important;
}
[data-testid="stBottomBlockContainer"] {
    padding-top:0 !important;
    padding-bottom:0 !important;
}
[data-testid="stExpander"] {
    background:var(--white);
    border:1px solid var(--border);
    border-radius:10px;
    box-shadow:none;
    margin-bottom:5px;
}
[data-testid="stExpander"] summary {
    min-height:38px !important;
    padding-top:6px !important;
    padding-bottom:6px !important;
}

.popular-title {
    font-family:"Manrope",sans-serif;
    font-size:18px;
    font-weight:800;
    letter-spacing:-.02em;
    color:var(--ink);
    margin:24px 0 14px;
}
.product-card-copy {
    padding:8px 2px 16px;
}
.product-card-name {
    font-family:"Manrope",sans-serif;
    font-size:14px;
    font-weight:700;
    color:var(--ink);
    margin-bottom:3px;
}
.product-card-desc {
    font-size:11px;
    line-height:1.45;
    color:var(--muted);
    min-height:28px;
    display:-webkit-box;
    -webkit-line-clamp:2;
    -webkit-box-orient:vertical;
    overflow:hidden;
}
.product-card-price {
    margin-top:7px;
    font-size:13px;
    font-weight:700;
    color:var(--chocolate);
}
[data-testid="stImage"] img {
    width:100%;
    height:170px;
    max-height:170px;
    object-fit:cover;
    object-position:center;
    border-radius:9px;
}
[data-testid="stVerticalBlock"] { gap:.55rem; }
[data-testid="stExpander"] summary { font-family:"Inter",sans-serif; font-weight:600; }
.stButton > button { border-radius:8px; border:1px solid var(--chocolate); background:var(--chocolate); color:white; font-weight:600; }
.stButton > button:hover { background:var(--chocolate-dark); border-color:var(--chocolate-dark); color:white; }
.loaf-footer { text-align:center; color:#9B918C; font-size:10px; margin-top:20px; }
[data-testid="stSidebar"] { display:none; }

[data-testid="stToolbar"] { visibility:hidden; height:0; }
[data-testid="stDecoration"] { display:none; }
[data-testid="stStatusWidget"] { visibility:hidden; }

@media (max-width:768px) {
    [data-testid="stImage"] img {
        height:145px;
        max-height:145px;
    }

    .block-container {
        padding-top:.5rem;
        padding-left:1rem;
        padding-right:1rem;
        padding-bottom:4rem;
    }
    .loaf-topbar {
        margin-bottom:7px;
        padding-bottom:7px;
    }
    .loaf-topnote { display:none; }
    .bakery-name {
        font-size:29px;
        line-height:1.1;
        letter-spacing:-.035em;
        margin-bottom:7px;
    }
    .bakery-subtitle {
        font-size:13px;
        line-height:1.45;
        margin-bottom:13px;
        max-width:95%;
    }
    .brand-dot {
        width:28px;
        height:3px;
        margin-bottom:11px;
    }
    .assistant-intro {
        margin-top:9px;
        padding-top:9px;
    }
    .assistant-title {
        font-size:18px;
        margin-bottom:3px;
    }
    .assistant-copy {
        font-size:12px;
        line-height:1.45;
    }
    .chat-row { margin:9px 0; }
    .chat-wrap { max-width:90%; }
    .chat-name { font-size:9px; }
    .chat-bubble {
        font-size:13px;
        line-height:1.5;
        padding:9px 12px;
        border-radius:13px;
    }
    [data-testid="stExpander"] {
        border-radius:8px;
    }
}

/* Compact product imagery inside columns */
[data-testid="stHorizontalBlock"] [data-testid="stImage"] img {
    height:125px !important;
    max-height:125px !important;
    object-fit:cover !important;
}

/* Smaller fixed chat composer */
[data-testid="stChatInput"] {
    max-width:560px !important;
    min-height:44px !important;
    margin:0 auto 6px auto !important;
}
[data-testid="stChatInput"] textarea {
    min-height:36px !important;
    height:36px !important;
    padding-top:8px !important;
    padding-bottom:6px !important;
    font-size:13px !important;
}
[data-testid="stChatInput"] button {
    width:30px !important;
    height:30px !important;
    min-height:30px !important;
}
[data-testid="stBottom"] {
    padding-top:5px !important;
    padding-bottom:2px !important;
}

/* Compact the entire fixed composer, not only the input element */
[data-testid="stBottom"] > div {
    max-width:520px !important;
    margin-left:auto !important;
    margin-right:auto !important;
}
[data-testid="stBottomBlockContainer"] {
    max-width:520px !important;
    width:calc(100% - 32px) !important;
    margin:0 auto !important;
    padding:4px 0 6px !important;
}
[data-testid="stChatInput"] {
    width:100% !important;
    max-width:520px !important;
    min-height:34px !important;
    margin:0 !important;
    border-radius:9px !important;
}
[data-testid="stChatInput"] textarea {
    min-height:34px !important;
    height:34px !important;
    padding:7px 42px 5px 12px !important;
    font-size:11px !important;
    line-height:20px !important;
}
[data-testid="stChatInput"] button {
    width:28px !important;
    height:28px !important;
    min-height:28px !important;
    margin:3px 4px 3px 0 !important;
}


@media (max-width:768px) {
    [data-testid="stBottom"] > div,
    [data-testid="stBottomBlockContainer"] {
        max-width:100% !important;
    }
    [data-testid="stBottomBlockContainer"] {
        width:calc(100% - 20px) !important;
        padding:3px 0 5px !important;
    }
}


/* Inline message composer */
[data-testid="stForm"] {
    max-width:700px;
    margin:20px auto 10px auto;
    padding:0 !important;
    border:0 !important;
    background:transparent !important;
}
[data-testid="stForm"] [data-testid="stHorizontalBlock"] {
    align-items:center;
    gap:6px;
}
[data-testid="stForm"] .stTextInput input {
    height:44px !important;
    min-height:44px !important;
    border:1px solid #E6C9C7 !important;
    border-radius:9px !important;
    background:#FFFDFC !important;
    font-size:12px !important;
    padding:0 12px !important;
    box-shadow:none !important;
}
[data-testid="stForm"] .stButton > button,
[data-testid="stForm"] [data-testid="stFormSubmitButton"] button {
    height:44px !important;
    min-height:44px !important;
    width:44px !important;
    padding:0 !important;
    border-radius:9px !important;
    background:var(--chocolate) !important;
    border-color:var(--chocolate) !important;
    color:white !important;
    font-size:16px !important;
}
[data-testid="stBottom"],
[data-testid="stBottomBlockContainer"] {
    display:none !important;
}
@media (max-width:768px) {
    [data-testid="stForm"] {
        max-width:100%;
        margin:12px 0 6px 0;
    }
    [data-testid="stForm"] .stTextInput input {
        height:40px !important;
        min-height:40px !important;
        font-size:12px !important;
    }
    [data-testid="stForm"] .stButton > button,
    [data-testid="stForm"] [data-testid="stFormSubmitButton"] button {
        height:40px !important;
        min-height:40px !important;
        width:40px !important;
    }
}


/* Remove Streamlit's reserved top chrome so the storefront starts higher */
header[data-testid="stHeader"] {
    display: none !important;
    height: 0 !important;
}
[data-testid="stToolbar"],
[data-testid="stDecoration"] {
    display: none !important;
}
.stApp > header {
    display: none !important;
}
.block-container {
    padding-top: 1rem !important;
}
@media (max-width:768px) {
    .block-container {
        padding-top: .75rem !important;
    }
}


/* AI ordering is the primary action */
.assistant-intro {
    background:#FFFDFC;
    border:1px solid #E8D9D3;
    border-left:4px solid var(--pink);
    border-radius:12px;
    padding:16px 18px !important;
    margin:18px 0 10px !important;
}
.assistant-title { font-size:20px !important; }
.assistant-copy { max-width:700px; }

@media (max-width:768px) {
    .assistant-intro {
        padding:13px 14px !important;
        margin:14px 0 8px !important;
    }
    .assistant-title { font-size:18px !important; }
    [data-testid="stForm"] [data-testid="stHorizontalBlock"] {
        flex-wrap:nowrap !important;
    }
    [data-testid="stForm"] [data-testid="column"]:first-child {
        width:calc(100% - 44px) !important;
        flex:1 1 auto !important;
    }
    [data-testid="stForm"] [data-testid="column"]:last-child {
        width:40px !important;
        flex:0 0 40px !important;
    }
}


/* Final mobile polish: no horizontal overflow + compact one-row composer */
html, body, .stApp {
    max-width:100%;
    overflow-x:hidden !important;
}
.block-container {
    overflow-x:hidden !important;
}
[data-testid="stForm"] {
    width:100% !important;
    max-width:700px !important;
    margin:14px 0 10px 0 !important;
}
[data-testid="stForm"] [data-testid="stHorizontalBlock"] {
    display:grid !important;
    grid-template-columns:minmax(0, 1fr) 44px !important;
    gap:8px !important;
    width:100% !important;
    align-items:center !important;
}
[data-testid="stForm"] [data-testid="column"] {
    width:auto !important;
    min-width:0 !important;
    flex:none !important;
}
[data-testid="stForm"] .stTextInput {
    width:100% !important;
    min-width:0 !important;
}
[data-testid="stForm"] .stTextInput input {
    width:100% !important;
    box-sizing:border-box !important;
}
[data-testid="stForm"] [data-testid="stFormSubmitButton"] {
    width:44px !important;
}
[data-testid="stForm"] [data-testid="stFormSubmitButton"] button {
    width:44px !important;
    min-width:44px !important;
    max-width:44px !important;
    margin:0 !important;
}
@media (max-width:768px) {
    [data-testid="stForm"] {
        max-width:100% !important;
        margin:10px 0 8px 0 !important;
    }
    [data-testid="stForm"] [data-testid="stHorizontalBlock"] {
        grid-template-columns:minmax(0, 1fr) 40px !important;
        gap:6px !important;
    }
    [data-testid="stForm"] [data-testid="stFormSubmitButton"],
    [data-testid="stForm"] [data-testid="stFormSubmitButton"] button {
        width:40px !important;
        min-width:40px !important;
        max-width:40px !important;
    }
    .assistant-intro {
        padding:11px 13px !important;
        margin:12px 0 7px !important;
    }
    .assistant-copy {
        line-height:1.4 !important;
    }
}

</style>
""", unsafe_allow_html=True)


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
    except Exception as e:
        st.error("Something went wrong looking that up. Please try again in a moment.")
        st.exception(e)  # TEMPORARY -- remove once we've found the root cause
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

    msg = MIMEText(body)
    msg["Subject"] = f"New Order #{order_number} - {business_name}"
    msg["From"] = st.secrets["EMAIL_ADDRESS"]
    msg["To"] = business_email

    if "@" in customer_contact:
        msg["Reply-To"] = customer_contact

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(st.secrets["EMAIL_ADDRESS"], st.secrets["EMAIL_PASSWORD"])
        server.send_message(msg)



def render_chat_message(role, content, business_name):
    safe_content = html.escape(str(content)).replace("\n", "<br>")
    if role == "user":
        label = "You"
        css_role = "user"
    else:
        display_name = str(business_name)
        for suffix in [" Bakery Test", " Bakery", " Test"]:
            if display_name.endswith(suffix):
                display_name = display_name[:-len(suffix)]
        label = f"{html.escape(display_name)} Assistant"
        css_role = "assistant"

    st.markdown(
        f"""
        <div class="chat-row {css_role}">
            <div class="chat-wrap">
                <div class="chat-name">{label}</div>
                <div class="chat-bubble">{safe_content}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


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

    display_business_name = str(business_name)
    for suffix in [" Bakery Test", " Bakery", " Test"]:
        if display_business_name.endswith(suffix):
            display_business_name = display_business_name[:-len(suffix)]

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

    st.markdown(
        '<div class="loaf-topbar"><div class="loaf-wordmark">LOAF</div><div class="loaf-topnote">Online ordering</div></div>',
        unsafe_allow_html=True
    )
    st.markdown('<div class="brand-dot"></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="bakery-name">{business_name}</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="bakery-subtitle">Browse today\'s bakes, ask about ingredients or custom orders, and place your order in one conversation.</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        f"""
        <div class="assistant-intro">
            <div class="assistant-title">Order with {display_business_name}</div>
            <div class="assistant-copy">Ask for recommendations, menu details, or simply tell me what you would like to order.</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    if not st.session_state.get("display_messages"):
        render_chat_message(
            "assistant",
            "Hi! What can I help you order today?",
            business_name
        )

    for message in st.session_state.get("display_messages", []):
        render_chat_message(message["role"], message["content"], business_name)

    with st.form("chat_form", clear_on_submit=True):
        chat_col, send_col = st.columns([12, 1])
        with chat_col:
            user_input = st.text_input(
                "Message",
                placeholder=f"Ask {display_business_name} anything...",
                label_visibility="collapsed"
            )
        with send_col:
            send_message = st.form_submit_button("↑", use_container_width=True)

    if not send_message:
        user_input = None

    # Product storefront. New saves persist PhotoURL on each menu item;
    # older bakeries fall back to the legacy photo list by position.
    visible_menu_items = [item for item in menu if item.get("Item")][:6]

    if visible_menu_items:
        st.markdown('<div class="popular-title">Popular picks</div>', unsafe_allow_html=True)

        card_cols = st.columns(3)
        for idx, item in enumerate(visible_menu_items):
            item_name = item.get("Item", "")
            price = item.get("Price", "")
            ingredients = item.get("Ingredients", "")
            photo_url = item.get("PhotoURL") or (menu_photo_urls[idx] if idx < len(menu_photo_urls) else None)

            with card_cols[idx % 3]:
                if photo_url:
                    st.image(photo_url, use_container_width=True)

                price_text = f"₹{price}" if price not in ("", None, 0) else ""
                st.markdown(
                    f"""
                    <div class="product-card-copy">
                        <div class="product-card-name">{item_name}</div>
                        <div class="product-card-desc">{ingredients}</div>
                        <div class="product-card-price">{price_text}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

    # Popular Picks already shows the first six products.
    # Only show View menu when there are additional products.
    full_menu_items = [item for item in menu if item.get("Item")]
    remaining_menu_items = full_menu_items[6:]

    if remaining_menu_items:
        with st.expander(f"View full menu · {len(remaining_menu_items)} more", expanded=False):
            menu_cols = st.columns(3)
            for display_idx, item in enumerate(remaining_menu_items):
                original_idx = display_idx + 6
                item_name = item.get("Item", "")
                price = item.get("Price", "")
                ingredients = item.get("Ingredients", "")
                photo_url = item.get("PhotoURL") or (
                    menu_photo_urls[original_idx]
                    if original_idx < len(menu_photo_urls)
                    else None
                )

                with menu_cols[display_idx % 3]:
                    if photo_url:
                        st.image(photo_url, use_container_width=True)

                    price_text = f"₹{price}" if price not in ("", None, 0) else ""
                    st.markdown(
                        f"""
                        <div class="product-card-copy">
                            <div class="product-card-name">{item_name}</div>
                            <div class="product-card-desc">{ingredients}</div>
                            <div class="product-card-price">{price_text}</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

    order = st.session_state.get("current_order")
    order_count = len(order.get("items", [])) if order and order.get("items") else 0
    with st.expander(f"Your order · {order_count} item{'s' if order_count != 1 else ''}", expanded=bool(order_count)):
        if order_count:
            for item in order["items"]:
                line = f"**{item.get('quantity', 1)} × {item.get('item', 'Unknown')}**"
                st.markdown(line)
                if item.get("customizations"):
                    st.caption(item["customizations"])
            st.divider()
            st.write(f"**Requested for:** {order.get('requested_datetime', 'not specified')}")
            st.write(f"**Estimated total:** {order.get('estimated_total', 'N/A')}")
            st.write(f"**Fulfillment:** {order.get('fulfillment', 'unspecified')}")
            if order.get("status") == "confirmed":
                st.success(f"Order #{st.session_state.get('order_number')} confirmed")
            else:
                st.info("Order in progress")
        else:
            st.markdown('<div class="order-empty">Your items will appear here as you order.</div>', unsafe_allow_html=True)

        if order_count > 0:
            if st.button("Start New Order", key="top_start_new_order"):
                for key in [
                    "messages", "display_messages", "current_order",
                    "order_email_sent", "order_number"
                ]:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()


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

        render_chat_message("user", user_input, business_name)

        try:
            with st.spinner("Typing..."):
                response = co.chat(
                    model="command-r-plus-08-2024",
                    messages=st.session_state.messages
                )
            bot_reply = response.message.content[0].text
        except Exception:
            render_chat_message(
                "assistant",
                "Sorry, I'm having trouble responding right now. Please try again in a moment, or contact the business directly.",
                business_name
            )
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

        render_chat_message("assistant", display_reply, business_name)

        st.session_state.messages.append({"role": "assistant", "content": bot_reply})
        st.session_state.display_messages.append({"role": "assistant", "content": display_reply})

    st.markdown('<div class="loaf-footer">Powered by Loaf</div>', unsafe_allow_html=True)


def customer_view():
    if slug_from_url:
        slug_input = slug_from_url
    else:
        st.markdown('<div class="loaf-wordmark">LOAF</div>', unsafe_allow_html=True)
        st.title("Order from your bakery")
        slug_input = st.text_input("Bakery link name", placeholder="e.g. sweettreats")
        if not slug_input:
            st.info("Enter your bakery's link name to get started.")
            return

    clean_slug, slug_error = normalize_and_validate_slug(slug_input)
    if slug_error:
        st.error("That doesn't look like a valid bakery link.")
        return

    business = get_business(clean_slug)
    if not business:
        st.error("We couldn't find that bakery.")
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
    st.title("Loaf")
    st.caption("Set up your bakery's ordering chatbot")

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
        "Product photos (optional — upload in the same order as your menu items)",
        accept_multiple_files=True,
        type=["png", "jpg", "jpeg"],
        help="Photo 1 will be linked to menu item 1, photo 2 to menu item 2, and so on."
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

            # Persist a photo on each menu item. Old bakeries still work because
            # the customer page falls back to menu_photo_urls by position.
            menu_records = menu.to_dict(orient="records")
            existing_menu = (existing_business or {}).get("menu", []) or []
            for idx, item in enumerate(menu_records):
                if idx < len(menu_photo_urls):
                    item["PhotoURL"] = menu_photo_urls[idx]
                elif idx < len(existing_menu) and existing_menu[idx].get("PhotoURL"):
                    item["PhotoURL"] = existing_menu[idx].get("PhotoURL")

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
                "menu": menu_records,
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
