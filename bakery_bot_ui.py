import streamlit as st
import cohere
import pandas as pd
import json
import re
import random
import smtplib
import html
from datetime import datetime
from email.mime.text import MIMEText

API_KEY = st.secrets["COHERE_API_KEY"]
co = cohere.ClientV2(API_KEY)
from supabase import create_client

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

params = st.query_params
slug_from_url = params.get("slug", "")
mode = params.get("mode", "customer")

st.set_page_config(page_title="Loaf")

# Loaf design: flat pink block, big bold headline, thin black rules, square corners.
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=Archivo:wght@400;500;600;800&family=DM+Mono:wght@400;500&display=swap');
:root { --pink:#F2C6D8; --pink-deep:#E7A6C1; --ink:#111111; --muted:#5C5558; --paper:#FFFFFF; --line:#111111; --red:#111111; --olive:#111111; --cream:#FFFFFF; }
html, body, [class*="css"] { font-family:"Archivo", sans-serif; }
*, *::before, *::after { transition:none !important; }
.stApp { background:var(--paper); color:var(--ink); }
.block-container { max-width:880px; padding:0 28px 3rem !important; margin:0 auto !important; background:transparent; }
#MainMenu, footer { visibility:hidden; }
header[data-testid="stHeader"], .stApp > header { display:none !important; height:0 !important; }
[data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"],
[data-testid="stSidebar"], [data-testid="stBottom"], [data-testid="stBottomBlockContainer"] { display:none !important; }
[data-testid="stVerticalBlock"] { gap:.7rem; }
*:focus-visible { outline:2px solid var(--ink); outline-offset:2px; }
.loaf-wordmark { font-weight:800; font-size:18px; }

/* Header: one flat pink block, big left-aligned name */
.pw-strip { display:none; }
.pw-gingham { margin:0 -28px 0; padding:56px 28px 44px; background:var(--pink); }
.pw-label { max-width:none; margin:0; padding:0; background:transparent; border:0; text-align:left; }
.bakery-name { font-weight:800; font-size:clamp(44px, 9vw, 92px); line-height:.98; letter-spacing:-.03em; color:var(--ink); margin:0 0 18px; }
.bakery-subtitle { max-width:460px; margin:0; color:var(--ink); font-size:16px; line-height:1.55; }
.pw-rule { height:1px; background:var(--ink); margin:28px 0 18px; }

/* Assistant intro */
.assistant-intro { background:transparent; border:0; padding:0; margin:8px 0 4px; }
.assistant-title { font-weight:800; font-size:30px; letter-spacing:-.02em; margin-bottom:6px; }
.assistant-copy { color:var(--muted); font-size:15px; line-height:1.6; max-width:480px; }

/* Chat */
.chat-row { display:flex; width:100%; margin:12px 0; }
.chat-row.user { justify-content:flex-end; }
.chat-wrap { max-width:82%; }
.chat-name { font-family:"DM Mono", monospace; font-size:11px; color:var(--muted); margin:0 0 4px; }
.chat-row.user .chat-name { text-align:right; }
.chat-bubble { font-size:15px; line-height:1.6; padding:11px 15px; border:1px solid var(--ink); }
.chat-row.assistant .chat-bubble { background:var(--paper); color:var(--ink); }
.chat-row.user .chat-bubble { background:var(--pink); color:var(--ink); }
[data-testid="stChatMessage"] { display:none; }

/* Composer */
[data-testid="stForm"] { width:100% !important; margin:16px 0 6px !important; padding:5px !important; border:1px solid var(--ink) !important; border-radius:0 !important; background:var(--paper) !important; }
[data-testid="stForm"]:focus-within { outline:2px solid var(--ink); }
[data-testid="stForm"] [data-testid="stHorizontalBlock"] { display:grid !important; grid-template-columns:minmax(0, 1fr) 44px !important; gap:6px !important; align-items:center !important; width:100% !important; }
[data-testid="stForm"] [data-testid="stColumn"], [data-testid="stForm"] [data-testid="column"] { width:auto !important; min-width:0 !important; flex:none !important; }
[data-testid="stForm"] [data-baseweb], [data-testid="stForm"] [data-testid="stTextInputRootElement"] { background:transparent !important; border:0 !important; box-shadow:none !important; }
[data-testid="stForm"] input { background:transparent !important; border:0 !important; box-shadow:none !important; height:44px !important; padding:0 14px !important; font-size:15px !important; color:var(--ink) !important; }
[data-testid="stForm"] input::placeholder { color:#8A8286; }
[data-testid="InputInstructions"], [data-testid="stInputInstructions"], .stTextInput small { display:none !important; }
[data-testid="stFormSubmitButton"] button { width:44px !important; min-width:44px !important; height:44px !important; padding:0 !important; border-radius:0 !important; background:var(--ink) !important; color:var(--paper) !important; border:0 !important; font-size:18px !important; }
[data-testid="stFormSubmitButton"] button:hover { background:var(--ink) !important; }

/* Favourites: flat cards, no tabs */
.pw-section-head { display:flex; align-items:baseline; gap:14px; flex-wrap:wrap; margin:4px 0 20px; }
.popular-title { font-weight:800; font-size:40px; letter-spacing:-.03em; }
.script-note { font-family:"DM Mono", monospace; font-size:12px; color:var(--muted); }
.product-card-shell { background:var(--paper); border:1px solid var(--ink); margin:0 0 18px; }
.product-card-media { padding:0; }
.product-card-photo { display:block; width:100%; aspect-ratio:4 / 3; object-fit:cover; border-bottom:1px solid var(--ink); }
.product-card-photo.placeholder { display:flex; align-items:center; justify-content:center; font-weight:800; font-size:56px; color:var(--ink); background:var(--pink); }
.product-card-copy { padding:12px 14px 14px; }
.product-card-topline { display:flex; justify-content:space-between; align-items:baseline; gap:10px; }
.product-card-name { font-weight:800; font-size:19px; line-height:1.2; letter-spacing:-.01em; }
.product-card-price { font-family:"DM Mono", monospace; font-weight:500; font-size:14px; white-space:nowrap; }
.product-card-desc { margin-top:6px; font-size:13px; line-height:1.55; color:var(--muted); }

/* Expanders and buttons */
[data-testid="stExpander"] { background:transparent !important; border:0 !important; box-shadow:none !important; margin-bottom:10px; }
[data-testid="stExpander"] details { background:var(--paper) !important; border:1px solid var(--ink) !important; border-radius:0 !important; }
[data-testid="stExpander"] summary { font-weight:800; font-size:16px; color:var(--ink); }
.order-empty { color:var(--muted); font-size:14px; }
.stButton > button { background:var(--ink); color:var(--paper); border:1px solid var(--ink); border-radius:0; font-weight:600; padding:.4rem 1.3rem; }
.stButton > button:hover { background:var(--ink); color:var(--paper); border-color:var(--ink); }
.loaf-footer { text-align:center; color:#8A8286; font-family:"DM Mono", monospace; font-size:11px; margin-top:36px; }

/* Loading cake */
.pw-cake-loader { position:relative; width:52px; height:59px; margin:4px 0 6px 3px; }
.pw-cake-dots { position:absolute; top:0; left:11px; width:30px; display:flex; justify-content:space-between; align-items:center; }
.pw-cake-dots span { width:5px; height:5px; border-radius:50%; background:var(--pink); animation:pwCakeDot 1s ease-in-out infinite; }
.pw-cake-dots span:nth-child(2) { animation-delay:.14s; }
.pw-cake-dots span:nth-child(3) { animation-delay:.28s; }
.pw-whole-cake { position:absolute; left:2px; bottom:0; width:48px; height:47px; animation:pwCakeBob 1.2s ease-in-out infinite; }
.pw-cake-body { position:absolute; left:6px; top:18px; width:36px; height:25px; box-sizing:border-box; background:#EABDB9; border:2px solid var(--ink); border-radius:3px 3px 8px 8px; }
.pw-cake-body:before { content:""; position:absolute; left:0; right:0; top:8px; height:2px; background:#fff3e8; }
.pw-cake-top { position:absolute; left:4px; top:11px; width:40px; height:12px; box-sizing:border-box; background:#FFF0E8; border:2px solid var(--ink); border-radius:50% 50% 34% 34%; z-index:3; }
.pw-cake-icing { position:absolute; left:7px; top:18px; width:34px; height:7px; background:#E89FA1; z-index:4; border-radius:0 0 8px 8px; }
.pw-cherry { position:absolute; width:7px; height:7px; border-radius:50%; background:#C96F76; border:1px solid var(--ink); top:-6px; }
.pw-cherry.ch1 { left:7px; } .pw-cherry.ch2 { left:16px; top:-9px; } .pw-cherry.ch3 { right:7px; }
.pw-cake-eye { position:absolute; top:9px; width:2px; height:3px; border-radius:50%; background:var(--ink); z-index:6; }
.pw-cake-eye.left { left:9px; } .pw-cake-eye.right { right:9px; }
.pw-cake-smile { position:absolute; left:14px; top:13px; width:6px; height:4px; border-bottom:1.5px solid var(--ink); border-radius:0 0 8px 8px; z-index:6; }
.pw-cake-plate { position:absolute; left:3px; bottom:0; width:42px; height:5px; background:#ead9d0; border:1.5px solid var(--ink); border-radius:50%; box-sizing:border-box; }
@keyframes pwCakeDot { 0%,70%,100% { opacity:.3; transform:translateY(0); } 35% { opacity:1; transform:translateY(-2px); } }
@keyframes pwCakeBob { 0%,100% { transform:translateY(0); } 50% { transform:translateY(-2px); } }
@media (prefers-reduced-motion:reduce) { .pw-cake-dots span, .pw-whole-cake { animation:none !important; } }

@media (max-width:768px) {
    .block-container { padding:0 16px 2.2rem !important; }
    .pw-gingham { margin:0 -16px; padding:36px 16px 30px; }
    .chat-wrap { max-width:92%; }
    .popular-title { font-size:32px; }
}


:root { --ink:#6E2E34; --paper:#FFF7E6; --pink:#F7C8D3; --muted:#7A4650; --line:#6E2E34; --blush:#F7C8D3; --rose:#B46A72; --sage:#A8B58A; }
.bakery-name, .assistant-title, .popular-title, .loaf-top-mark, .product-card-name,
[data-testid="stExpander"] summary { font-family:"DM Serif Display", serif !important; font-style:italic; font-weight:400 !important; letter-spacing:0 !important; }
.loaf-top { display:flex; justify-content:space-between; align-items:baseline; padding:20px 0 14px; border-bottom:1.5px solid var(--ink); font-size:13px; color:var(--ink); }
.loaf-top-mark { font-size:26px; color:var(--ink); }
.pw-gingham { margin:18px 0 0 !important; padding:44px 32px 38px !important; background:var(--blush) !important; border:1.5px solid var(--ink); }
.bakery-name { font-size:clamp(56px, 11vw, 112px) !important; line-height:.95 !important; color:var(--ink) !important; }
.bakery-subtitle { color:var(--ink); }
.assistant-intro { background:var(--sage) !important; border:1.5px solid var(--ink) !important; padding:20px 22px !important; }
.assistant-title { font-size:34px !important; color:var(--ink) !important; }
.assistant-copy { color:var(--ink); }
.chat-name { color:var(--muted); }
.chat-bubble { border:1.5px solid var(--ink) !important; }
.chat-row.assistant .chat-bubble { background:var(--blush); }
.chat-row.user .chat-bubble { background:var(--sage); }
[data-testid="stForm"] { background:var(--paper) !important; border:1.5px solid var(--ink) !important; }
[data-testid="stFormSubmitButton"] button, [data-testid="stFormSubmitButton"] button:hover,
.stButton > button, .stButton > button:hover { background:var(--ink) !important; color:var(--paper) !important; border:1.5px solid var(--ink) !important; }
.popular-title { font-size:46px !important; color:var(--ink) !important; }
.product-card-shell { border:1.5px solid var(--ink) !important; }
.product-card-media { padding:10px 10px 0 !important; }
.product-card-photo { border:1.5px solid var(--ink) !important; }
.product-card-photo.placeholder { background:var(--paper) !important; color:var(--ink); }
.product-card-name { font-size:23px !important; line-height:1.1 !important; }
.product-card-price, .product-card-desc, .product-card-name { color:inherit !important; }
.product-card-desc { font-size:13px; }
.tile-0 { background:var(--blush); color:var(--ink); }
.tile-1 { background:var(--sage); color:var(--ink); }
.tile-2 { background:var(--rose); color:var(--paper); }
[data-testid="stExpander"] details { background:var(--paper) !important; border:1.5px solid var(--ink) !important; }
.order-empty, .loaf-footer { color:var(--muted); }

/* Quieter, smaller, mobile friendly. Menu cards keep their stronger colours. */
:root { --blush-lt:#FBE4E9; --sage-lt:#DCE3CB; }
.loaf-top { padding:14px 0 10px !important; }
.loaf-top-mark { font-size:22px !important; }
.pw-gingham { margin:12px 0 0 !important; padding:22px 22px 20px !important; background:var(--blush-lt) !important; border:1px solid var(--ink) !important; }
.bakery-name { font-size:clamp(32px, 7vw, 54px) !important; margin:0 0 8px !important; }
.bakery-subtitle { font-size:14px !important; line-height:1.5 !important; max-width:none !important; }
.pw-rule { margin:16px 0 12px !important; }
.assistant-intro { background:var(--sage-lt) !important; border:1px solid var(--ink) !important; padding:16px 18px !important; margin:4px 0 !important; }
.assistant-title { font-size:24px !important; margin-bottom:4px !important; }
.assistant-copy { font-size:14px !important; line-height:1.5 !important; }
.chat-bubble { border:1px solid var(--ink) !important; font-size:14px !important; padding:9px 13px !important; }
.chat-row.assistant .chat-bubble { background:var(--blush-lt) !important; }
.chat-row.user .chat-bubble { background:var(--sage-lt) !important; }
[data-testid="stForm"] { border-width:1px !important; }
.popular-title { font-size:30px !important; }
.pw-section-head { margin:2px 0 14px !important; }
@media (max-width:768px) {
    .pw-gingham { padding:16px 16px 14px !important; }
    .assistant-intro { padding:14px !important; }
    .popular-title { font-size:26px !important; }
    .product-card-name { font-size:20px !important; }
    .product-card-photo { aspect-ratio:16 / 9 !important; width:100% !important; object-fit:cover !important; object-position:center !important; }
}

/* Cohesive menu: one card colour, photos fill the full card width, sage badge */
.tile-0 { background:var(--blush) !important; color:var(--ink) !important; }
.tile-1 { background:var(--sage) !important; color:var(--ink) !important; }
.tile-2 { background:var(--rose) !important; color:var(--paper) !important; }
.product-card-shell { border:1px solid var(--ink) !important; overflow:hidden; }
.product-card-media { padding:0 !important; }
.product-card-photo { display:block !important; width:100% !important; aspect-ratio:4 / 3 !important; object-fit:cover !important; border:0 !important; border-bottom:1px solid var(--ink) !important; }
.product-card-photo.placeholder { background:var(--blush-lt) !important; }
.product-card-price, .product-card-desc, .product-card-name { color:inherit !important; }
.script-note { display:inline-block !important; background:var(--sage) !important; color:var(--ink) !important; border:1px solid var(--ink) !important; font-family:"DM Mono", monospace !important; font-size:11px !important; font-weight:500 !important; padding:2px 9px !important; }

/* Final Theme 1 mobile image sizing */
@media (max-width:768px) {
  .product-card-photo {
    width:100% !important;
    height:280px !important;
    aspect-ratio:auto !important;
    object-fit:cover !important;
    object-position:center !important;
  }
}

/* Keep Loaf visually stable while Streamlit is processing a chat request. */
[data-testid="stStatusWidget"],
[data-testid="stStatusWidget"] *,
.stApp[data-test-script-state="running"],
.stApp[data-test-script-state="running"] > *,
[data-stale="true"],
[data-stale="true"] * {
    opacity: 1 !important;
    filter: none !important;
}


/* ===== NORMAL LOAF OWNER LOGIN ===== */
.owner-login-shell{
  max-width:520px;
  margin:72px auto 0;
}
.owner-login-brand{
  font-family:"Archivo",sans-serif;
  font-size:14px;
  font-weight:800;
  letter-spacing:.12em;
  color:#6E2E34;
  margin-bottom:24px;
}
.owner-login-title{
  font-family:"Archivo",sans-serif;
  font-style:normal;
  font-size:34px;
  font-weight:700;
  letter-spacing:-.025em;
  color:#2F2928;
  margin:0 0 7px;
}
.owner-login-copy{
  font-size:14px;
  line-height:1.5;
  color:#756C68;
  margin-bottom:22px;
}

/* Owner form only: undo the chat-composer form styling */
.owner-login-marker + div [data-testid="stForm"],
.owner-login-marker ~ div [data-testid="stForm"]{
  padding:22px !important;
  margin:0 !important;
  border:1px solid #DED5CD !important;
  border-radius:12px !important;
  background:#FFFDF9 !important;
}
.owner-login-marker ~ div [data-testid="stForm"] [data-testid="stHorizontalBlock"]{
  display:flex !important;
}
.owner-login-marker ~ div [data-testid="stForm"] input{
  height:44px !important;
  padding:0 12px !important;
  background:#FFFFFF !important;
  border:1px solid #D7CEC7 !important;
  border-radius:8px !important;
  color:#2F2928 !important;
}
.owner-login-marker ~ div [data-testid="stForm"] [data-baseweb="input"]{
  background:#FFFFFF !important;
  border-radius:8px !important;
}
.owner-login-marker ~ div [data-testid="stForm"] label{
  font-size:13px !important;
  font-weight:600 !important;
  color:#443D39 !important;
}
.owner-login-marker ~ div [data-testid="stFormSubmitButton"] button{
  width:100% !important;
  min-width:100% !important;
  height:44px !important;
  margin-top:8px !important;
  border-radius:8px !important;
  background:#6E2E34 !important;
  color:#FFF !important;
  font-size:14px !important;
  font-weight:600 !important;
}
.owner-login-help{
  margin-top:12px;
  font-size:12px;
  color:#8A817C;
}
@media(max-width:768px){
  .owner-login-shell{margin:34px auto 0;}
  .owner-login-title{font-size:28px;}
}


/* ===== OWNER PORTAL: NEUTRAL LOGIN OVERRIDE ===== */
body:has(.owner-login-marker) .stApp{
  background:#F7F7F5 !important;
}
body:has(.owner-login-marker) .block-container{
  max-width:520px !important;
  padding:0 20px 3rem !important;
}
.owner-login-shell{
  max-width:440px !important;
  margin:88px auto 0 !important;
}
.owner-login-brand{
  color:#222222 !important;
  font-size:13px !important;
  margin-bottom:28px !important;
}
.owner-login-title{
  color:#1F1F1F !important;
  font-size:30px !important;
  font-weight:700 !important;
}
.owner-login-copy{
  color:#6B6B6B !important;
  margin-bottom:18px !important;
}

/* Override all customer chat form rules on the owner login */
body:has(.owner-login-marker) [data-testid="stForm"]{
  width:100% !important;
  margin:0 !important;
  padding:22px !important;
  background:#FFFFFF !important;
  border:1px solid #E1E1DE !important;
  border-radius:12px !important;
  box-shadow:0 8px 28px rgba(0,0,0,.045) !important;
}
body:has(.owner-login-marker) [data-testid="stForm"] [data-testid="stHorizontalBlock"]{
  display:flex !important;
  flex-direction:column !important;
  gap:0 !important;
}
body:has(.owner-login-marker) [data-testid="stForm"] [data-testid="stColumn"],
body:has(.owner-login-marker) [data-testid="stForm"] [data-testid="column"]{
  width:100% !important;
}
body:has(.owner-login-marker) [data-testid="stForm"] input{
  height:44px !important;
  padding:0 12px !important;
  color:#222 !important;
  background:#FFF !important;
  border:1px solid #D8D8D5 !important;
  border-radius:7px !important;
  box-shadow:none !important;
}
body:has(.owner-login-marker) [data-testid="stForm"] [data-baseweb="input"],
body:has(.owner-login-marker) [data-testid="stForm"] [data-testid="stTextInputRootElement"]{
  background:#FFF !important;
  border-radius:7px !important;
}
body:has(.owner-login-marker) [data-testid="stForm"] input::placeholder{
  color:#9A9A96 !important;
}
body:has(.owner-login-marker) [data-testid="stForm"] label{
  color:#333 !important;
  font-size:13px !important;
  font-weight:600 !important;
}
body:has(.owner-login-marker) [data-testid="stFormSubmitButton"] button,
body:has(.owner-login-marker) [data-testid="stFormSubmitButton"] button:hover{
  width:100% !important;
  min-width:100% !important;
  height:44px !important;
  margin-top:8px !important;
  padding:0 18px !important;
  background:#222222 !important;
  color:#FFFFFF !important;
  border:1px solid #222222 !important;
  border-radius:7px !important;
  font-size:14px !important;
  font-weight:600 !important;
}
.owner-login-help{
  max-width:440px !important;
  margin:12px auto 0 !important;
  color:#858580 !important;
}
@media(max-width:768px){
  .owner-login-shell{margin-top:46px !important;}
}

</style>
""", unsafe_allow_html=True)


MAX_MESSAGES_PER_SESSION = 40  # caps Cohere API spend per customer session


def parse_advance_notice_hours(text):
    """Turn '48 hours', '2 days' or '1 week' into hours. None if unparseable."""
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
    return value


def check_advance_notice(requested_datetime_iso, advance_notice_text):
    """Verify the notice gap in real Python instead of trusting the AI's arithmetic."""
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
                path, photo.getvalue(), {"content-type": photo.type}
            )
            urls.append(supabase.storage.from_("menu-photos").get_public_url(path))
        except Exception:
            st.warning(f"Couldn't upload {photo.name}. The rest of your bot was still saved.")
    return urls


def restore_owner_auth_session():
    """Restore the Supabase Auth session after a Streamlit rerun."""
    access_token = st.session_state.get("owner_access_token")
    refresh_token = st.session_state.get("owner_refresh_token")
    if not access_token or not refresh_token:
        return False
    try:
        supabase.auth.set_session(access_token, refresh_token)
        return True
    except Exception:
        for key in [
            "owner_user_id", "owner_email",
            "owner_access_token", "owner_refresh_token"
        ]:
            st.session_state.pop(key, None)
        return False


def auth_sign_in(email, password):
    """Sign in and persist the actual Supabase JWT/session for RLS."""
    try:
        result = supabase.auth.sign_in_with_password({
            "email": email.strip(),
            "password": password,
        })
    except Exception:
        return None

    if not result or not result.user or not result.session:
        return None

    st.session_state.owner_user_id = str(result.user.id)
    st.session_state.owner_email = result.user.email or email.strip()
    st.session_state.owner_access_token = result.session.access_token
    st.session_state.owner_refresh_token = result.session.refresh_token
    return result.user


def auth_sign_out():
    restore_owner_auth_session()
    try:
        supabase.auth.sign_out()
    except Exception:
        pass
    for key in [
        "owner_user_id", "owner_email",
        "owner_access_token", "owner_refresh_token"
    ]:
        st.session_state.pop(key, None)


def current_owner_id():
    if not st.session_state.get("owner_user_id"):
        return None
    if not restore_owner_auth_session():
        return None
    return st.session_state.get("owner_user_id")


def get_owned_business(slug):
    owner_id = current_owner_id()
    if not owner_id:
        return None
    try:
        result = (
            supabase.table("businesses")
            .select("*")
            .eq("slug", slug)
            .eq("owner_id", owner_id)
            .limit(1)
            .execute()
        )
    except Exception:
        return None
    return result.data[0] if result.data else None


def get_business(slug):
    """Customer storefront lookup. Never reads private owner/admin columns."""
    try:
        result = (
            supabase.table("public_bakeries")
            .select("id,slug,business_name,address,fulfillment_options,delivery_info,faq_info,business_hours,advance_notice,sold_out_items,social_link,menu,menu_photo_urls")
            .eq("slug", slug)
            .limit(1)
            .execute()
        )
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
    if "@" not in customer_contact:
        digits_only = re.sub(r"\D", "", customer_contact)
        if len(digits_only) >= 10:
            body_lines.append(f"Message customer on WhatsApp: https://wa.me/{digits_only}")

    msg = MIMEText("\n".join(body_lines))
    msg["Subject"] = f"New Order #{order_number} - {business_name}"
    msg["From"] = st.secrets["EMAIL_ADDRESS"]
    msg["To"] = business_email
    if "@" in customer_contact:
        msg["Reply-To"] = customer_contact

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(st.secrets["EMAIL_ADDRESS"], st.secrets["EMAIL_PASSWORD"])
        server.send_message(msg)


def short_business_name(name):
    display_name = str(name)
    for suffix in [" Bakery Test", " Bakery", " Test"]:
        if display_name.endswith(suffix):
            display_name = display_name[:-len(suffix)]
    return display_name


def fmt_price(price):
    if price in ("", None):
        return ""
    try:
        value = float(price)
    except (TypeError, ValueError):
        return html.escape(str(price))
    if value <= 0:
        return ""
    return f"₹{int(value)}" if value == int(value) else f"₹{value:.2f}"


def render_chat_message(role, content, business_name):
    safe_content = html.escape(str(content)).replace("\n", "<br>")
    if role == "user":
        label, css_role = "You", "user"
    else:
        label, css_role = f"{html.escape(short_business_name(business_name))} Assistant", "assistant"
    st.markdown(
        f'<div class="chat-row {css_role}"><div class="chat-wrap">'
        f'<div class="chat-name">{label}</div>'
        f'<div class="chat-bubble">{safe_content}</div></div></div>',
        unsafe_allow_html=True
    )


def run_chatbot(business):
    business_name = business["business_name"]
    contact = "the bakery directly"
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

    display_business_name = short_business_name(business_name)
    safe_business_name = html.escape(str(business_name))
    safe_display_name = html.escape(display_business_name)

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
Speak like a fast, friendly bakery ordering assistant, not a general chatbot.
VISIBLE REPLY LENGTH IS A HARD RULE:
- Greetings such as "hi", "hey", "heyyy": ONE short sentence only, maximum 15 words. Example: "Heyyy! What are you craving today?"
- Unclear/random messages such as "blabla": ONE short sentence only, maximum 18 words. Example: "I didn't quite catch that. What are you looking for?"
- Simple menu, price, ingredient, availability, or business questions: maximum 2 short sentences.
- Recommendations: suggest at most 2 products, then ask ONE short question.
- During an order: ask only for the NEXT missing detail. Do not ask several questions at once.
- Normal visible replies should stay under 35 words.
- Only exceed 35 words when necessary for allergen uncertainty, an important ordering constraint, or a final order summary.
- Never add a second paragraph just to sound friendly.
- Ask only ONE useful next question at a time.
- Do not list the whole menu unless the customer asks to see the menu or several options are genuinely needed.
- If recommending products, suggest at most 2 relevant menu items, include their prices when useful, and then ask one short follow-up such as whether they want one added.
- If the customer simply says "hi", "hey", or similar, greet them briefly and ask what they are craving. Do not explain all your capabilities.
- Do not repeat information the customer already gave you.
- Do not repeatedly say "I'd be happy to help", "absolutely", "certainly", or other filler.
- Do not mention that you are an AI.
- If the customer asks something unrelated to ordering, answer briefly when appropriate, then naturally steer back to the bakery.
- For ingredient or allergen questions, answer only from the listed menu/FAQ information. If the information is insufficient, say you cannot confirm and direct them to the business instead of guessing.
- The product photos and menu are already visible on this page. If a customer asks to see products/photos, tell them they can browse the products below. Only mention the social link if they specifically ask for Instagram, the website, or more photos.
- When collecting an order, move efficiently through missing details instead of explaining the ordering process.
- Keep confirmation messages concise, but clearly state the important order details before final confirmation.
Match the customer's language style naturally: English, Hindi, or Hinglish.
Never use em dashes in your replies.

Only treat an order as BULK if the customer orders MORE THAN 10 of a single item, or explicitly mentions an event, party, or wholesale quantity. A normal order of a few items (even 2-3 of something) is always a regular RETAIL order, not bulk -- do not mention deposits or extra lead time for ordinary small orders.

The business's social media / website link is: {social_link if social_link else "not provided"}. The menu and product photos are already visible on this page, so do not send customers to social media just to browse products. Share the social/website link only if they specifically ask for it or want additional external information.

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
        st.session_state.awaiting_assistant = False

    # Header
    st.markdown(
        '<div class="loaf-top"><span class="loaf-top-mark">LOAF</span><span>Online ordering</span></div>'
        '<div class="pw-gingham"><div class="pw-label">'
        f'<div class="bakery-name">{safe_business_name}</div>'
        '<div class="bakery-subtitle">Pick your bakes, ask about ingredients or custom cakes, and place your order in one chat.</div>'
        '</div></div><div class="pw-rule"></div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="assistant-intro">'
        f'<div class="assistant-title">Order with {safe_display_name}</div>'
        '<div class="assistant-copy">Tell us what you are craving. Ask about ingredients, get recommendations, or place your order right here.</div>'
        '</div>',
        unsafe_allow_html=True
    )

    if not st.session_state.get("display_messages"):
        render_chat_message("assistant", "Hi! What can I help you order today?", business_name)

    for message in st.session_state.get("display_messages", []):
        render_chat_message(message["role"], message["content"], business_name)

    thinking_slot = st.empty()

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

    # Stage 1: save the customer's message and rerun immediately.
    # This makes the sent message visible before the Cohere request starts.
    if user_input and not st.session_state.get("awaiting_assistant", False):
        clean_user_input = user_input.strip()
        if clean_user_input:
            st.session_state.messages.append({"role": "user", "content": clean_user_input})
            st.session_state.display_messages.append({"role": "user", "content": clean_user_input})
            st.session_state.awaiting_assistant = True
            st.rerun()

    # Favourites: two per row
    visible_menu_items = [item for item in menu if item.get("Item")][:6]
    if visible_menu_items:
        st.markdown(
            '<div class="pw-rule"></div>'
            '<div class="pw-section-head"><span class="popular-title">Our favourites</span>'
            '<span class="script-note">fresh today</span></div>',
            unsafe_allow_html=True
        )
        card_cols = st.columns(3)
        for idx, item in enumerate(visible_menu_items):
            raw_name = str(item.get("Item", ""))
            item_name = html.escape(raw_name)
            price_text = fmt_price(item.get("Price", ""))
            ingredients = str(item.get("Ingredients", ""))
            photo_url = item.get("PhotoURL") or (menu_photo_urls[idx] if idx < len(menu_photo_urls) else None)
            parts = [p.strip() for p in ingredients.split(",") if p.strip()]
            short_desc = html.escape(" · ".join(parts[:4]) if parts else ingredients)

            if photo_url:
                safe_photo = html.escape(str(photo_url), quote=True)
                photo_html = f'<img class="product-card-photo" src="{safe_photo}" alt="{item_name}">'
            else:
                photo_html = f'<div class="product-card-photo placeholder">{html.escape(raw_name[:1].upper())}</div>'
            price_html_card = f'<div class="product-card-price">{price_text}</div>' if price_text else ""

            with card_cols[idx % 3]:
                st.markdown(
                    f'<div class="product-card-shell tile-{idx % 3}">'
                    f'<div class="product-card-media">{photo_html}</div>'
                    f'<div class="product-card-copy"><div class="product-card-topline"><div class="product-card-name">{item_name}</div>{price_html_card}</div>'
                    f'<div class="product-card-desc">{short_desc}</div></div></div>',
                    unsafe_allow_html=True
                )

    remaining_menu_items = [item for item in menu if item.get("Item")][6:]
    if remaining_menu_items:
        with st.expander(f"See the full menu ({len(remaining_menu_items)} more)", expanded=False):
            menu_cols = st.columns(3)
            for display_idx, item in enumerate(remaining_menu_items):
                original_idx = display_idx + 6
                item_name = html.escape(str(item.get("Item", "")))
                ingredients = html.escape(str(item.get("Ingredients", "")))
                price_text = fmt_price(item.get("Price", ""))
                photo_url = item.get("PhotoURL") or (
                    menu_photo_urls[original_idx] if original_idx < len(menu_photo_urls) else None
                )
                with menu_cols[display_idx % 3]:
                    if photo_url:
                        st.image(photo_url, use_container_width=True)
                    price_html = f'<div class="product-card-price">{price_text}</div>' if price_text else ""
                    st.markdown(
                        f'<div class="product-card-copy" style="padding:8px 2px 14px">'
                        f'<div class="product-card-topline"><div class="product-card-name">{item_name}</div>{price_html}</div>'
                        f'<div class="product-card-desc">{ingredients}</div></div>',
                        unsafe_allow_html=True
                    )

    # Order summary
    order = st.session_state.get("current_order")
    order_count = len(order.get("items", [])) if order and order.get("items") else 0
    order_label = f"Your order ({order_count} item{'s' if order_count != 1 else ''})"
    with st.expander(order_label, expanded=bool(order_count)):
        if order_count:
            for item in order["items"]:
                st.markdown(f"**{item.get('quantity', 1)} × {item.get('item', 'Unknown')}**")
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
            st.markdown('<div class="order-empty">Your items will show up here as you order.</div>', unsafe_allow_html=True)

        if order_count > 0:
            if st.button("Start new order", key="top_start_new_order"):
                for key in ["messages", "display_messages", "current_order", "order_email_sent", "order_number", "awaiting_assistant"]:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()

    if len(st.session_state.get("display_messages", [])) >= MAX_MESSAGES_PER_SESSION:
        st.warning(
            f"This chat has reached its message limit for one session. "
            f"Please contact {contact} directly, or start a new order."
        )

    # Stage 2: on the immediate rerun, the user's message is already visible.
    # Now show the cake and request the assistant response exactly once.
    if st.session_state.get("awaiting_assistant", False):
        thinking_slot.markdown(
            '<div class="pw-cake-loader" aria-label="Assistant is responding">'
            '<div class="pw-cake-dots"><span></span><span></span><span></span></div>'
            '<div class="pw-whole-cake">'
            '<div class="pw-cake-top"><i class="pw-cherry ch1"></i><i class="pw-cherry ch2"></i><i class="pw-cherry ch3"></i></div>'
            '<div class="pw-cake-icing"></div>'
            '<div class="pw-cake-body"><i class="pw-cake-eye left"></i><i class="pw-cake-eye right"></i><i class="pw-cake-smile"></i></div>'
            '<div class="pw-cake-plate"></div></div></div>',
            unsafe_allow_html=True
        )

        try:
            response = co.chat(model="command-r-plus-08-2024", messages=st.session_state.messages)
            bot_reply = response.message.content[0].text
        except Exception:
            thinking_slot.empty()
            st.session_state.awaiting_assistant = False
            st.session_state.display_messages.append({
                "role": "assistant",
                "content": "Sorry, I'm having trouble responding right now. Please try again in a moment."
            })
            st.rerun()

        thinking_slot.empty()
        order_match = re.search(r"ORDER_SUMMARY:\s*(\{.*\})", bot_reply, re.DOTALL)
        display_reply = bot_reply

        if order_match:
            display_reply = bot_reply[:order_match.start()].strip()
            try:
                parsed_order = json.loads(order_match.group(1))

                if parsed_order.get("status") == "confirmed" and get_missing_order_fields(parsed_order):
                    parsed_order["status"] = "in_progress"

                notice_check = check_advance_notice(
                    parsed_order.get("requested_datetime_iso"), advance_notice
                )
                notice_warning = None
                if (
                    parsed_order.get("status") == "confirmed"
                    and notice_check.get("checked")
                    and not notice_check.get("ok")
                ):
                    parsed_order["status"] = "in_progress"
                    notice_warning = (
                        f"It's only about {notice_check['actual_hours']:.1f} hours from now, "
                        f"and we need {notice_check['required_hours']:.0f} hours' notice. "
                        f"Could you choose a later time, or confirm you'd still like to proceed?"
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
                            st.session_state.order_number,
                        )
                        st.session_state.order_email_sent = True
                    except Exception:
                        pass

                    st.session_state.orders_this_session = (
                        st.session_state.get("orders_this_session", 0) + 1
                    )
                    display_reply += (
                        f"\n\nOrder #{st.session_state.order_number} is confirmed. "
                        f"We'll be in touch shortly."
                    )
                elif notice_warning:
                    display_reply += f"\n\n{notice_warning}"

            except json.JSONDecodeError:
                pass

        st.session_state.messages.append({"role": "assistant", "content": bot_reply})
        st.session_state.display_messages.append(
            {"role": "assistant", "content": display_reply}
        )
        st.session_state.awaiting_assistant = False
        st.rerun()

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


def owner_login_gate(title, caption):
    """Shared Supabase Auth login for bakery owners."""
    if current_owner_id():
        st.markdown(
            '<div class="owner-login-shell">'
            '<div class="owner-login-brand">LOAF</div>'
            f'<div class="owner-login-title">{html.escape(title)}</div>'
            f'<div class="owner-login-copy">{html.escape(caption)}</div>'
            '</div>',
            unsafe_allow_html=True
        )
        st.caption(f"Signed in as {st.session_state.get('owner_email', 'bakery owner')}")
        if st.button("Sign out", key=f"signout_{title}"):
            auth_sign_out()
            st.rerun()
        return True

    st.markdown(
        '<div class="owner-login-shell">'
        '<div class="owner-login-brand">LOAF</div>'
        '<div class="owner-login-title">Bakery owner login</div>'
        '<div class="owner-login-copy">Sign in to manage your bakery.</div>'
        '<div class="owner-login-marker"></div>'
        '</div>',
        unsafe_allow_html=True
    )

    with st.form(f"owner_login_{title}"):
        email = st.text_input("Email", placeholder="you@bakery.com")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        submitted = st.form_submit_button("Sign in", use_container_width=True)

    st.markdown(
        '<div class="owner-login-help">Use the owner account linked to your Loaf bakery.</div>',
        unsafe_allow_html=True
    )

    if not submitted:
        return False

    user = auth_sign_in(email, password)
    if not user:
        st.error("Incorrect email or password.")
        return False

    st.rerun()


def quick_update_view():
    if not owner_login_gate(
        "Quick Stock Update",
        "Sign in securely to update today's availability."
    ):
        return

    owner_id = current_owner_id()

    # Prefer the slug in the URL. If absent, show only bakeries owned by this account.
    clean_slug = None
    if slug_from_url:
        clean_slug, slug_error = normalize_and_validate_slug(slug_from_url)
        if slug_error:
            st.error(slug_error)
            return
        business = get_owned_business(clean_slug)
        if not business:
            st.error("This bakery is not linked to your owner account.")
            return
    else:
        try:
            owned = (
                supabase.table("businesses")
                .select("slug,business_name,menu,sold_out_items")
                .eq("owner_id", owner_id)
                .execute()
            ).data or []
        except Exception:
            owned = []

        if not owned:
            st.error("No bakery is linked to this owner account yet.")
            return

        labels = {
            f"{row.get('business_name') or row.get('slug')} ({row.get('slug')})": row
            for row in owned
        }
        selected = st.selectbox("Bakery", list(labels.keys()))
        business = labels[selected]
        clean_slug = business["slug"]

    menu_items = business.get("menu") or []
    if not menu_items:
        st.info("This business doesn't have any menu items yet.")
        return

    current_sold_out = [
        n.strip()
        for n in (business.get("sold_out_items") or "").split(",")
        if n.strip()
    ]

    st.write("Check anything that's sold out right now:")
    newly_sold_out = []
    for item in menu_items:
        item_name = item.get("Item", "")
        if not item_name:
            continue
        if st.checkbox(
            item_name,
            value=item_name in current_sold_out,
            key=f"soldout_{clean_slug}_{item_name}"
        ):
            newly_sold_out.append(item_name)

    if st.button("Update availability"):
        try:
            result = (
                supabase.table("businesses")
                .update({"sold_out_items": ", ".join(newly_sold_out)})
                .eq("slug", clean_slug)
                .eq("owner_id", owner_id)
                .execute()
            )
        except Exception:
            st.error("Something went wrong updating this. Please try again.")
        else:
            if not result.data:
                st.error("Update was not permitted for this owner account.")
            else:
                st.success("Updated. Your customer page now reflects today's availability.")


def owner_view():
    if not owner_login_gate(
        "Loaf Owner",
        "Sign in securely to manage the bakery linked to your Loaf account."
    ):
        return

    owner_id = current_owner_id()

    try:
        owned_rows = (
            supabase.table("businesses")
            .select("*")
            .eq("owner_id", owner_id)
            .execute()
        ).data or []
    except Exception:
        owned_rows = []

    if not owned_rows:
        st.warning(
            "No bakery is linked to this account yet. "
            "For now, link an owner_id in Supabase before using this page."
        )
        return

    if len(owned_rows) == 1:
        existing_business = owned_rows[0]
    else:
        choices = {
            f"{row.get('business_name') or row.get('slug')} ({row.get('slug')})": row
            for row in owned_rows
        }
        selected = st.selectbox("Bakery", list(choices.keys()))
        existing_business = choices[selected]

    clean_slug = existing_business["slug"]
    st.subheader(existing_business.get("business_name") or clean_slug)
    st.caption(f"Bakery link: {clean_slug}")

    existing_menu = existing_business.get("menu") or []
    menu_df = pd.DataFrame(existing_menu) if existing_menu else pd.DataFrame(
        {"Item": [""], "Price": [0], "Ingredients": [""]}
    )
    # Keep the editor focused on business data, not duplicated photo URLs.
    editor_cols = [c for c in ["Item", "Price", "Ingredients"] if c in menu_df.columns]
    if editor_cols:
        menu_df = menu_df[editor_cols]
    menu = st.data_editor(menu_df, num_rows="dynamic")

    business_name = st.text_input(
        "Business name",
        value=str(existing_business.get("business_name") or "")
    )
    contact = st.text_input(
        "Contact email",
        value=str(existing_business.get("contact_email") or "")
    )
    address = st.text_input(
        "Business address",
        value=str(existing_business.get("address") or "")
    )

    fulfillment_values = ["Pickup only", "Delivery only", "Both pickup and delivery"]
    current_fulfillment = existing_business.get("fulfillment_options")
    fulfillment_index = (
        fulfillment_values.index(current_fulfillment)
        if current_fulfillment in fulfillment_values
        else 0
    )
    fulfillment_options = st.selectbox(
        "Fulfillment options offered",
        fulfillment_values,
        index=fulfillment_index
    )
    delivery_info = st.text_area(
        "Delivery / pickup info",
        value=str(existing_business.get("delivery_info") or "")
    )
    faq_info = st.text_area(
        "FAQ / common questions",
        value=str(existing_business.get("faq_info") or "")
    )
    business_hours = st.text_input(
        "Business hours",
        value=str(existing_business.get("business_hours") or "")
    )
    advance_notice = st.text_input(
        "Advance notice required for custom orders",
        value=str(existing_business.get("advance_notice") or "")
    )
    sold_out_items = st.text_input(
        "Out of stock today (comma separated)",
        value=str(existing_business.get("sold_out_items") or "")
    )
    social_link = st.text_input(
        "Instagram / website link",
        value=str(existing_business.get("social_link") or "")
    )
    menu_photos = st.file_uploader(
        "Replace/add product photos (optional, same order as menu items)",
        accept_multiple_files=True,
        type=["png", "jpg", "jpeg"]
    )

    if st.button("Save Bakery"):
        at_position = contact.find("@")
        dot_position = contact.find(".")
        if at_position == -1 or dot_position < at_position:
            st.error("Please enter a valid email.")
            return

        if menu_photos:
            menu_photo_urls = upload_menu_photos(clean_slug, menu_photos)
        else:
            menu_photo_urls = existing_business.get("menu_photo_urls") or []

        menu_records = menu.to_dict(orient="records")
        old_menu = existing_business.get("menu") or []
        for idx, item in enumerate(menu_records):
            if idx < len(menu_photo_urls):
                item["PhotoURL"] = menu_photo_urls[idx]
            elif idx < len(old_menu) and old_menu[idx].get("PhotoURL"):
                item["PhotoURL"] = old_menu[idx].get("PhotoURL")

        business_data = {
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
        }

        try:
            result = (
                supabase.table("businesses")
                .update(business_data)
                .eq("slug", clean_slug)
                .eq("owner_id", owner_id)
                .execute()
            )
        except Exception:
            st.error("Something went wrong saving your bakery. Please try again.")
        else:
            if not result.data:
                st.error("Save was not permitted for this owner account.")
            else:
                st.success("Saved.")
                st.code(f"https://bakery-bot.streamlit.app/?slug={clean_slug}")
                st.caption("Quick stock update:")
                st.code(
                    f"https://bakery-bot.streamlit.app/?mode=quickupdate&slug={clean_slug}"
                )


# Restore the signed-in owner's Supabase JWT before any owner-side database request.
if st.session_state.get("owner_access_token"):
    restore_owner_auth_session()

if mode == "owner":
    owner_view()
elif mode == "quickupdate":
    quick_update_view()
else:
    customer_view()
