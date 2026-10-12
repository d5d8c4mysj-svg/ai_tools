import streamlit as st
import cohere
import pandas as pd
import json
import re
import requests
import html
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

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


/* Native Streamlit chat composer, styled to match Loaf */
[data-testid="stChatInput"]{
  border:1px solid var(--line) !important;
  border-radius:0 !important;
  background:var(--cream) !important;
  box-shadow:none !important;
}
[data-testid="stChatInput"] textarea{
  font-family:"Archivo",sans-serif !important;
  color:var(--ink) !important;
  background:transparent !important;
}
[data-testid="stChatInput"] button{
  background:#7A2E35 !important;
  color:#fff !important;
  border-radius:0 !important;
}


/* Inline Loaf composer */
[data-testid="stForm"]{
  border:0 !important;
}
[data-testid="stForm"] [data-testid="stTextInput"] input{
  min-height:48px !important;
}


/* Customer chat composer: unmistakably interactive */
div[data-testid="stForm"]:has(input[placeholder*="Ask "]) {
  border:0 !important;
  padding:0 !important;
  margin-top:14px !important;
  background:transparent !important;
}
div[data-testid="stForm"]:has(input[placeholder*="Ask "]) input {
  height:52px !important;
  padding:0 16px !important;
  background:#FFFDF8 !important;
  border:1.5px solid #7A2E35 !important;
  border-radius:8px !important;
  font-size:15px !important;
  color:#3A2928 !important;
  box-shadow:none !important;
}
div[data-testid="stForm"]:has(input[placeholder*="Ask "]) input::placeholder {
  color:#807875 !important;
  opacity:1 !important;
}
div[data-testid="stForm"]:has(input[placeholder*="Ask "]) [data-testid="stFormSubmitButton"] button {
  height:52px !important;
  min-height:52px !important;
  width:100% !important;
  border:0 !important;
  border-radius:8px !important;
  background:#7A2E35 !important;
  color:white !important;
  font-size:18px !important;
  font-weight:700 !important;
}
@media(max-width:768px){
  div[data-testid="stForm"]:has(input[placeholder*="Ask "]) input {
    height:48px !important;
  }
  div[data-testid="stForm"]:has(input[placeholder*="Ask "]) [data-testid="stFormSubmitButton"] button {
    height:48px !important;
    min-height:48px !important;
  }
}


/* Final customer composer: clean, light, minimal */
div[data-testid="stForm"]:has(input[placeholder*="Ask "]) {
  border:0 !important;
  padding:0 !important;
  margin-top:14px !important;
  background:transparent !important;
}
div[data-testid="stForm"]:has(input[placeholder*="Ask "]) input {
  height:50px !important;
  padding:0 16px !important;
  background:#FFFDF8 !important;
  border:1px solid #D8CEC5 !important;
  border-radius:10px !important;
  font-size:15px !important;
  color:#3A2928 !important;
  box-shadow:none !important;
}
div[data-testid="stForm"]:has(input[placeholder*="Ask "]) input:focus {
  border-color:#B8AAA0 !important;
  box-shadow:none !important;
}
div[data-testid="stForm"]:has(input[placeholder*="Ask "]) input::placeholder {
  color:#8B8580 !important;
  opacity:1 !important;
}
div[data-testid="stForm"]:has(input[placeholder*="Ask "]) [data-testid="stFormSubmitButton"] button {
  height:50px !important;
  min-height:50px !important;
  width:100% !important;
  border:0 !important;
  border-radius:10px !important;
  background:#7A2E35 !important;
  color:#FFF !important;
  font-size:17px !important;
  font-weight:600 !important;
  box-shadow:none !important;
}


/* ===== LOAF OWNER ORDER DASHBOARD ===== */
.owner-order-time{
  font-size:14px;
  color:#756D68;
  margin:-2px 0 14px;
}
div[data-testid="stVerticalBlockBorderWrapper"]{
  border:1px solid #E3DED8 !important;
  border-radius:14px !important;
  background:#FFFFFF !important;
  box-shadow:0 4px 18px rgba(34,31,29,.035) !important;
}
div[data-testid="stVerticalBlockBorderWrapper"] h4{
  margin-top:0 !important;
}
div[data-testid="stExpander"]{
  border:1px solid #E3DED8 !important;
  border-radius:12px !important;
  background:#FFFFFF !important;
}
div[data-testid="stExpander"] details summary{
  font-weight:600 !important;
}


/* ===== OWNER PORTAL IS THEME-INDEPENDENT ===== */
body:has(.owner-portal-marker) .stApp{
  background:#F7F7F5 !important;
}
body:has(.owner-portal-marker) .block-container{
  max-width:980px !important;
}
body:has(.owner-portal-marker) h1,
body:has(.owner-portal-marker) h2,
body:has(.owner-portal-marker) h3,
body:has(.owner-portal-marker) h4,
body:has(.owner-portal-marker) p,
body:has(.owner-portal-marker) label,
body:has(.owner-portal-marker) span{
  font-family:"Arial",sans-serif !important;
  font-style:normal !important;
}
body:has(.owner-portal-marker) h1,
body:has(.owner-portal-marker) h2,
body:has(.owner-portal-marker) h3,
body:has(.owner-portal-marker) h4{
  color:#202020 !important;
}
body:has(.owner-portal-marker) [data-testid="stVerticalBlockBorderWrapper"],
body:has(.owner-portal-marker) [data-testid="stExpander"]{
  background:#FFFFFF !important;
  border-color:#E1E1DE !important;
}
body:has(.owner-portal-marker) button{
  border-radius:8px !important;
}
body:has(.owner-portal-marker) [data-testid="stButton"] button{
  background:#222222 !important;
  color:#FFFFFF !important;
  border:1px solid #222222 !important;
}
body:has(.owner-portal-marker) input,
body:has(.owner-portal-marker) textarea,
body:has(.owner-portal-marker) [data-baseweb="select"] > div{
  background:#FFFFFF !important;
  color:#222222 !important;
  border-color:#DADAD7 !important;
}


/* ===== V23 OWNER DASHBOARD ===== */
body:has(.owner-portal-marker) .block-container{
  max-width:960px !important;
  padding-top:36px !important;
}
.owner-dashboard-head{margin:8px 0 26px;}
.owner-dashboard-head h1{font-size:32px !important;margin:3px 0 4px !important;}
.owner-dashboard-head p{margin:0;color:#6F6F6B;}
.owner-kicker{font-size:12px;font-weight:800;letter-spacing:.14em;color:#555;}
body:has(.owner-portal-marker) [data-testid="stMetric"]{
  background:#FFF !important;border:1px solid #E3E3DF !important;
  border-radius:12px !important;padding:16px 18px !important;
}
.status-pill{display:inline-block;float:right;padding:5px 9px;border-radius:999px;font-size:11px;font-weight:800;letter-spacing:.06em;}
.status-pill.pending{background:#F1EEE7;color:#665E51;}
.history-row{display:flex;justify-content:space-between;gap:20px;padding:16px 2px;border-bottom:1px solid #E8E8E4;}
.history-row span{font-size:13px;color:#777773;}
.history-right{text-align:right;white-space:nowrap;}
body:has(.owner-portal-marker) h2{font-size:21px !important;margin-top:30px !important;}
body:has(.owner-portal-marker) [data-testid="stVerticalBlockBorderWrapper"]{
  padding:4px !important;margin-bottom:12px !important;
}


/* ===== V24 OWNER CLEANUP ===== */
body:has(.owner-portal-marker) .block-container{
  padding-top:28px !important;
}
.owner-dashboard-head{
  margin:0 0 22px !important;
}
.owner-dashboard-head h1{
  margin:5px 0 5px !important;
}
body:has(.owner-portal-marker) [data-testid="stMetric"]{
  min-height:108px;
}
body:has(.owner-portal-marker) h3{
  margin-top:26px !important;
  font-size:17px !important;
}
body:has(.owner-portal-marker) hr{
  margin:28px 0 !important;
}


/* Owner form focus */
body:has(.owner-portal-marker) input:focus,
body:has(.owner-portal-marker) textarea:focus{
  border-color:#BDBDB8 !important;
  box-shadow:0 0 0 1px #BDBDB8 !important;
  outline:none !important;
}

/* ===== V39 DEFINITIVE FILE UPLOADER FIX ===== */
body:has(.owner-portal-marker) [data-testid="stFileUploader"] *::before,
body:has(.owner-portal-marker) [data-testid="stFileUploader"] *::after{
  content:none !important;
}
body:has(.owner-portal-marker) [data-testid="stFileUploader"] button{
  font-size:0 !important;
  width:auto !important;
  min-width:88px !important;
  padding:9px 14px !important;
  background:#FFFFFF !important;
  border:1px solid #D8D8D4 !important;
  border-radius:8px !important;
}
body:has(.owner-portal-marker) [data-testid="stFileUploader"] button::after{
  content:"Upload" !important;
  display:inline !important;
  font-size:14px !important;
  font-family:Arial,sans-serif !important;
  font-style:normal !important;
  font-weight:400 !important;
  color:#222222 !important;
}
body:has(.owner-portal-marker) [data-testid="stFileUploader"] button *{
  display:none !important;
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


def is_custom_order(order):
    return str(order.get("order_type") or "retail").lower() == "custom"

def compute_order_total(order, menu):
    prices = {str(m.get("Item") or "").strip().lower(): m.get("Price") for m in (menu or [])}
    total = 0
    for it in order.get("items") or []:
        try:
            total += float(prices.get(str(it.get("item") or "").strip().lower())) * float(it.get("quantity") or 0)
        except (TypeError, ValueError):
            pass
    return total


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
    if order.get("fulfillment") == "delivery" and not order.get("delivery_address"):
        missing.append("delivery address")
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


def mask_contact(value):
    value = str(value or "")
    if "@" in value:
        name, domain = value.split("@", 1)
        return (name[:2] + "***@" + domain) if name else "***@" + domain
    digits = re.sub(r"\D", "", value)
    if len(digits) >= 4:
        return "••••••" + digits[-4:]
    return "••••"

def extract_custom_date(text):
    """Return a date if the text names one (today, tomorrow, a weekday), else None."""
    s = re.sub(r"\s+", " ", str(text or "").lower()).strip()
    now = datetime.now(ZoneInfo("Asia/Kolkata"))
    if "day after tomorrow" in s:
        return (now + timedelta(days=2)).date()
    if "tomorrow" in s:
        return (now + timedelta(days=1)).date()
    if "today" in s:
        return now.date()
    weekdays = {"monday":0,"tuesday":1,"wednesday":2,"thursday":3,"friday":4,"saturday":5,"sunday":6}
    for name, num in weekdays.items():
        if re.search(rf"\b{name}\b", s):
            delta = (num - now.weekday()) % 7
            if delta == 0 and "next " in s:
                delta = 7
            return (now + timedelta(days=delta)).date()
    return None


def extract_custom_time(text):
    """Return (hour, minute) in 24-hour time if the text has a clock time, else None."""
    s = str(text or "").lower()
    m = re.search(r"\b(1[0-2]|0?[1-9])(?::([0-5]\d))?\s*(am|pm)\b", s)
    if m:
        return int(m.group(1)) % 12 + (12 if m.group(3) == "pm" else 0), int(m.group(2) or 0)
    m24 = re.search(r"\b([01]?\d|2[0-3]):([0-5]\d)\b", s)
    if m24:
        return int(m24.group(1)), int(m24.group(2))
    return None


def custom_missing_slots(order):
    """Return missing custom-request fields independent of conversational order."""
    missing = []
    items = order.get("items") or []
    first = items[0] if items else {}
    if not first.get("item"):
        missing.append("item")
    if not first.get("quantity"):
        missing.append("quantity")
    if not order.get("requested_datetime_iso"):
        missing.append("datetime")
    if order.get("fulfillment") not in ("pickup", "delivery"):
        missing.append("fulfillment")
    if order.get("fulfillment") == "delivery" and not order.get("delivery_address"):
        missing.append("address")
    if not order.get("customer_name") or not order.get("customer_contact"):
        missing.append("identity")
    return missing

def custom_next_question(order):
    missing = custom_missing_slots(order)
    if not missing:
        first=(order.get("items") or [{}])[0]
        lines = [
            "Send this custom request?",
            f"- {first.get('quantity',1)} × {first.get('item','Custom item')}",
            f"- {str(order.get('fulfillment') or '').title()}",
            f"- {order.get('requested_datetime')}",
        ]
        if order.get("delivery_address"):
            lines.append(f"- Delivery: {order.get('delivery_address')}")
        lines.append(f"- Contact: {mask_contact(order.get('customer_contact'))}")
        lines.append("")
        lines.append("The bakery will contact you to finalize the details, price and payment.")
        return "\n".join(lines), "confirm"
    nxt=missing[0]
    questions={
        "quantity":"How many would you like?",
        "datetime":"What date and time would you like it?",
        "fulfillment":"Would you like pickup or delivery?",
        "address":"What's the delivery address?",
        "identity":"What's your name and contact number or email?",
    }
    return questions.get(nxt,"Could you tell me a little more?"), nxt

def delivery_address_allowed(address, business):
    """Conservative MVP delivery validation using owner-configured city + areas."""
    address_norm = re.sub(r"\s+", " ", str(address or "").lower()).strip()
    city = str(business.get("delivery_city") or "").lower().strip()
    areas = [str(x).lower().strip() for x in (business.get("delivery_areas") or []) if str(x).strip()]
    if not city or not areas:
        return None  # owner has not configured enough information; do not guess
    city_ok = city in address_norm
    area_ok = any(area in address_norm for area in areas)
    if area_ok and (city_ok or city not in address_norm):
        # Locality match is enough when user omits the city; configured area belongs to configured city.
        return True
    if city and any(token in address_norm for token in [city]):
        return False
    # Address may explicitly name another city or may simply be ambiguous.
    return False

def menu_item_names(menu):
    return [str(x.get("Item") or "").strip() for x in (menu or []) if x.get("Item")]

def detect_requested_product(text, menu):
    """
    Known menu items are matched deterministically.
    Unknown-item extraction is left to Cohere; no hard-coded food catalogue.
    """
    s = str(text or "").lower().strip()
    for name in menu_item_names(menu):
        nl = name.lower()
        if nl in s:
            return name, True
        # tolerate simple singular/plural wording for known menu items
        if nl.rstrip("s") and nl.rstrip("s") in s:
            return name, True
    return None, None


def custom_request_prompt(item_name, business_name):
    return (
        f"{item_name} isn't on the current menu. "
        f"I can send it to {business_name} as a custom request instead. "
        "Would you like me to?"
    )

def has_explicit_time(text):
    """True only when the customer's text contains a clock-like time."""
    s = str(text or "").lower()
    return bool(re.search(r"\b(?:[01]?\d|2[0-3])(?::[0-5]\d)?\s*(?:am|pm)\b", s)
                or re.search(r"\b(?:[01]?\d|2[0-3]):[0-5]\d\b", s))

def recover_name_contact(text, order):
    """Recover obvious 'Name + phone/email' input if model extraction misses it."""
    s = str(text or "").strip()
    if not s:
        return order
    email = re.search(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", s, re.I)
    phone = re.search(r"(?<!\d)(?:\+?\d[\d\s-]{7,}\d)(?!\d)", s)
    contact_match = email or phone
    if contact_match and not order.get("customer_contact"):
        order["customer_contact"] = re.sub(r"[\s-]", "", contact_match.group(0)) if phone else contact_match.group(0)
    if contact_match and not order.get("customer_name"):
        before = s[:contact_match.start()].strip(" ,:-")
        before = re.sub(r"(?i)^(?:my name is|i am|i'm|name is)\s+", "", before).strip()
        if before and len(before) <= 80:
            order["customer_name"] = before
    return order

def deterministic_checkout_reply(order):
    """Python owns checkout progression after Cohere extracts structured state."""
    missing = get_missing_order_fields(order)

    if "fulfillment method" in missing:
        return "Would you like pickup or delivery?", False

    if "requested date/time" in missing:
        human_date = str(order.get("requested_datetime") or "").strip()
        if human_date and not order.get("requested_datetime_iso"):
            return f"What time would you like {human_date.lower()}?", False
        return "What date and time would you like?", False

    if "delivery address" in missing:
        return "What's the delivery address?", False

    # Ask name + contact together whenever either is missing.
    if "customer name" in missing or "customer contact" in missing:
        return "What's your name and contact number or email?", False

    # All required fields exist. Python forces one final confirmation prompt.
    items = order.get("items") or []
    item_lines = []
    for item in items:
        qty = item.get("quantity", 1)
        name = item.get("item", "Item")
        item_lines.append(f"- {qty}x {name}")

    when = order.get("requested_datetime") or "Requested time"
    fulfillment = str(order.get("fulfillment") or "").title()
    contact = mask_contact(order.get("customer_contact"))

    summary = "Confirm this order?\n" + "\n".join(item_lines)
    summary += f"\n- {fulfillment}\n- {when}\n- Contact: {contact}"
    return summary, True


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
            .select("id,slug,business_name,address,fulfillment_options,delivery_info,delivery_city,delivery_areas,faq_info,business_hours,advance_notice,sold_out_items,social_link,menu,menu_photo_urls")
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


def send_new_order_notification(business_name, owner_email, order_number, order, final_total):
    """Send a bakery notification through Resend after the secure DB insert succeeds."""
    api_key = st.secrets.get("RESEND_API_KEY")
    if not api_key or not owner_email:
        return False

    items = order.get("items") or []
    item_lines = []
    for item in items:
        line = f"{item.get('quantity', 1)} x {item.get('item', 'Item')}"
        if item.get("customizations"):
            line += f" ({item.get('customizations')})"
        item_lines.append(line)

    fulfillment = str(order.get("fulfillment") or "").title()
    when = order.get("requested_datetime") or "Not specified"
    customer_name = order.get("customer_name") or "Not provided"

    text_body = (
        f"New Loaf order for {business_name}\n\n"
        + "\n".join(item_lines)
        + f"\n\n{fulfillment} · {when}"
        + f"\nTotal: ₹{final_total}"
        + f"\nCustomer: {customer_name}"
        + "\n\nOpen your Loaf owner dashboard to review and accept or decline the order."
    )

    # Resend's onboarding sender works for initial testing. Once Loaf has a verified
    # sending domain, replace this with orders@yourdomain.
    payload = {
        "from": "Loaf Orders <onboarding@resend.dev>",
        "to": [owner_email],
        "subject": f"New Loaf order · {order_number}",
        "text": text_body,
    }
    try:
        response = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=10,
        )
        return response.ok
    except Exception:
        return False


def send_custom_request_notification(business_name, owner_email, request_number, order):
    api_key = st.secrets.get("RESEND_API_KEY")
    if not api_key or not owner_email:
        return False
    first = (order.get("items") or [{}])[0]
    body = (
        f"New custom request for {business_name}\n\n"
        f"{first.get('quantity',1)} x {first.get('item','Custom item')}\n"
        f"{str(order.get('fulfillment') or '').title()} · {order.get('requested_datetime')}\n"
        f"Customer: {order.get('customer_name')}\n\n"
        "Availability and price have not been confirmed. Open Loaf to review the request."
    )
    try:
        r=requests.post(
            "https://api.resend.com/emails",
            headers={"Authorization":f"Bearer {api_key}","Content-Type":"application/json"},
            json={
                "from":"Loaf Requests <onboarding@resend.dev>",
                "to":[owner_email],
                "subject":f"New Loaf custom request · {request_number}",
                "text":body,
            },
            timeout=10,
        )
        return r.ok
    except Exception:
        return False


def with_ist(value):
    """ISO string with an explicit offset. The model sends local times without one."""
    dt = datetime.fromisoformat(str(value))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ZoneInfo("Asia/Kolkata"))
    return dt.isoformat()


def submit_protected_custom_request(slug, order):
    items = order.get("items") or []
    first = items[0] if items else {}
    requested_iso = order.get("requested_datetime_iso")
    if not requested_iso:
        raise ValueError("A valid requested date/time is required.")
    params = {
        "p_bakery_slug": slug,
        "p_requested_item": first.get("item"),
        "p_quantity": int(first.get("quantity") or 1),
        "p_fulfillment": order.get("fulfillment"),
        "p_requested_datetime": with_ist(requested_iso),
        "p_customer_name": order.get("customer_name"),
        "p_customer_contact": order.get("customer_contact"),
        "p_delivery_address": order.get("delivery_address") if order.get("fulfillment") == "delivery" else None,
        "p_customer_notes": first.get("customizations") or None,
    }
    result = supabase.rpc("submit_loaf_custom_request", params).execute()
    if not result.data:
        raise ValueError("The custom request could not be saved.")
    return result.data


def submit_protected_order(slug, order):
    """Submit through protected RPC; customers never insert into orders directly."""
    requested_iso = order.get("requested_datetime_iso")
    if not requested_iso:
        raise ValueError("A valid requested date/time is required.")
    params = {
        "p_bakery_slug": slug,
        "p_items": order.get("items") or [],
        "p_fulfillment": order.get("fulfillment"),
        "p_requested_datetime": with_ist(requested_iso),
        "p_customer_name": order.get("customer_name"),
        "p_customer_contact": order.get("customer_contact"),
        "p_delivery_address": order.get("delivery_address") if order.get("fulfillment") == "delivery" else None,
        "p_order_type": order.get("order_type") or "retail",
    }
    result = supabase.rpc("submit_loaf_order", params).execute()
    if not result.data:
        raise ValueError("The order could not be saved.")
    return result.data


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
    menu = business.get("menu") or []

    display_business_name = short_business_name(business_name)
    safe_business_name = html.escape(str(business_name))
    safe_display_name = html.escape(display_business_name)

    if "messages" not in st.session_state:
        current_time_str = datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%A, %Y-%m-%d %I:%M %p")

        if fulfillment_options == "Pickup only":
            fulfillment_instructions = f"""This business offers PICKUP ONLY -- do not offer, mention, or ask about delivery under any circumstances. Do NOT ask the customer for a delivery address. Pickup happens at the business address: {address}."""
        elif fulfillment_options == "Delivery only":
            fulfillment_instructions = f"""This business offers DELIVERY ONLY -- do not offer or mention pickup. Ask the customer for their delivery address."""
        else:
            fulfillment_instructions = f"""This business offers BOTH pickup and delivery. Ask the customer which they'd prefer. If pickup, no address is needed (pickup is at {address}). If delivery, ask for their delivery address."""

        prompt = f"""You are the customer-facing bakery assistant for {business_name}.

SOURCE OF TRUTH
- Menu: {menu}
- Address: {address}
- Fulfillment: {fulfillment_options}
- Delivery info: {delivery_info}
- FAQ: {faq_info}
- Business hours: {business_hours}
- Sold out today: {sold_out_items if sold_out_items else "none"}
- Social link: {social_link if social_link else "not provided"}
- Current India date/time: {current_time_str}

CONVERSATION
- Reply to every customer message. Never return a blank reply.
- Match English, Hindi, or Hinglish naturally.
- Keep replies short and ask only one useful next question.
- Answer menu, ingredient, recommendation, hours and business questions only from the supplied data.
- Never invent prices, availability, policies, ingredients, delivery coverage, dates, or times.

CUSTOM / OFF-MENU REQUESTS
- If a requested item, variation, or modification is not clearly offered by the menu (for example sugar-free brownies), say it is not on the current menu and offer to send a custom request to the bakery.
- Whenever you make that offer, append exactly this hidden line:
CUSTOM_REQUEST_OFFER: {{"item":"Exact requested item or modification"}}
- Do not promise the bakery can make it. Do not quote a price. Do not say you will personally follow up.
- After the customer accepts a custom request, Python handles the rest of that flow. Do not create ORDER_SUMMARY for off-menu/custom requests.

NORMAL MENU ORDERS
- Only use ORDER_SUMMARY for actual on-menu retail/bulk orders.
- Standard menu products remain retail even if their name contains Cake, Cheesecake or Cupcake.
- Ask only for missing operational details. Do not ask about customizations unless the customer requests one.
- Required fields: items/quantities, pickup or delivery, exact date/time, delivery address when needed, customer name and contact.
- Never invent an exact time from a vague date/daypart.
- Do not set status=confirmed until the customer explicitly confirms the final summary.
- The application/database validates prices and saves orders; do not claim an order is accepted by the bakery.

For an active normal order, append this machine-readable block at the END of the reply:
ORDER_SUMMARY: {{"items":[{{"item":"name","quantity":1,"customizations":""}}],"fulfillment":"pickup or delivery or unspecified","order_type":"retail or bulk","requested_datetime":"human-readable date/time or empty string","requested_datetime_iso":"exact ISO timestamp or empty string","estimated_total":0,"customer_name":"name or empty string","customer_contact":"phone/email or empty string","status":"in_progress or confirmed"}}
Do not append ORDER_SUMMARY when there is no normal menu order in progress."""

        st.session_state.messages = [{"role": "system", "content": prompt}]
        st.session_state.display_messages = []
        st.session_state.current_order = None
        st.session_state.order_email_sent = False
        st.session_state.order_saved = False
        st.session_state.order_number = None
        st.session_state.pending_custom_item = None
        st.session_state.custom_request_stage = None
        st.session_state.orders_this_session = 0
        st.session_state.awaiting_assistant = False
        st.session_state.pending_user_text = None

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

    # Clear, full-width chat composer with a visible send button.
    with st.form("chat_form", clear_on_submit=True):
        chat_col, send_col = st.columns([12, 1], gap="small")
        with chat_col:
            user_input = st.text_input(
                "Message",
                placeholder=f"Ask {display_business_name} anything...",
                label_visibility="collapsed",
                key=f"chat_text_{slug_from_url or 'bakery'}"
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
            st.session_state.pending_user_text = clean_user_input

            # Consolidated custom-request handoff. Once a customer accepts an
            # off-menu request, Python owns the flow end-to-end. Cohere is no longer
            # allowed to replace or lose custom-request state between turns.
            current_custom = st.session_state.get("current_order") or {}
            custom_stage = st.session_state.get("custom_request_stage")
            if current_custom.get("order_type") == "custom_request" and custom_stage:
                low = clean_user_input.lower().strip()
                first = (current_custom.get("items") or [{}])[0]
                reply = None

                # Customer can cancel at any stage.
                if re.search(r"\b(cancel|nevermind|never mind|stop)\b", low):
                    st.session_state.current_order = None
                    st.session_state.custom_request_stage = None
                    reply = "No problem. I haven't sent the custom request."

                elif custom_stage == "quantity":
                    m = re.search(r"\b(\d{1,3})\b", low)
                    if m and 1 <= int(m.group(1)) <= 100:
                        first["quantity"] = int(m.group(1))
                        current_custom["items"][0] = first
                        st.session_state.custom_request_stage = "datetime"
                        reply = "Got it. What date and time would you need it?"
                    else:
                        reply = "How many would you like? Please give me an approximate quantity."

                elif custom_stage == "datetime":
                    # Date and time are independent slots. Either can arrive first.
                    # Also remember fulfilment if the customer volunteers it early.
                    if re.search(r"\b(deliver|delivered|delivery)\b", low):
                        current_custom["fulfillment"] = "delivery"
                    elif re.search(r"\b(pickup|pick up|collect)\b", low):
                        current_custom["fulfillment"] = "pickup"

                    found_date = extract_custom_date(clean_user_input)
                    found_time = extract_custom_time(clean_user_input)

                    if found_date:
                        current_custom["requested_date_iso"] = found_date.isoformat()
                    if found_time:
                        current_custom["requested_time_hour"] = int(found_time[0])
                        current_custom["requested_time_minute"] = int(found_time[1])

                    saved_date = current_custom.get("requested_date_iso")
                    saved_hour = current_custom.get("requested_time_hour")
                    saved_minute = current_custom.get("requested_time_minute")

                    if saved_date and saved_hour is not None:
                        day = datetime.fromisoformat(saved_date).date()
                        dt = datetime(
                            day.year, day.month, day.day,
                            int(saved_hour), int(saved_minute or 0),
                            tzinfo=ZoneInfo("Asia/Kolkata")
                        )
                        current_custom["requested_datetime"] = dt.strftime("%A, %d %b at %-I:%M %p")
                        current_custom["requested_datetime_iso"] = dt.isoformat()

                        if current_custom.get("fulfillment") == "delivery":
                            st.session_state.custom_request_stage = "address"
                            reply = "Got it. What's the delivery address?"
                        elif current_custom.get("fulfillment") == "pickup":
                            st.session_state.custom_request_stage = "identity"
                            reply = "Got it. What's your name and contact number or email?"
                        else:
                            st.session_state.custom_request_stage = "fulfillment"
                            reply = "Got it. Would you like pickup or delivery?"
                    elif saved_date:
                        reply = "What exact time would you like?"
                    elif saved_hour is not None:
                        reply = "Got it. What date would you need it?"
                    else:
                        reply = "Please tell me the date and time you need it."

                elif custom_stage == "fulfillment":
                    if re.search(r"\b(deliver|delivered|delivery)\b", low):
                        current_custom["fulfillment"] = "delivery"
                        st.session_state.custom_request_stage = "address"
                        reply = "Sure. What's the delivery address?"
                    elif re.search(r"\b(pickup|pick up|collect)\b", low):
                        current_custom["fulfillment"] = "pickup"
                        current_custom["delivery_address"] = None
                        st.session_state.custom_request_stage = "identity"
                        reply = "Sure. What's your name and contact number or email?"
                    else:
                        reply = "Would you like pickup or delivery?"

                elif custom_stage == "address":
                    eligibility = delivery_address_allowed(clean_user_input, business)
                    if eligibility is True:
                        current_custom["delivery_address"] = clean_user_input.strip()
                        st.session_state.custom_request_stage = "identity"
                        reply = "Thanks. What's your name and contact number or email?"
                    elif eligibility is False:
                        city = business.get("delivery_city") or "the configured delivery city"
                        areas = ", ".join(business.get("delivery_areas") or [])
                        reply = f"Sorry, delivery is currently available only in {city}" + (f" for these areas: {areas}." if areas else ".") + " You can choose pickup instead or give another delivery address."
                    else:
                        reply = "I can't confirm that delivery area yet. You can choose pickup instead."

                elif custom_stage == "identity":
                    # Accept name and contact together OR across two turns.
                    before_name = current_custom.get("customer_name")
                    current_custom = recover_name_contact(clean_user_input, current_custom)
                    if not current_custom.get("customer_name") and not re.search(r"@|\d{8,}", low):
                        candidate = re.sub(r"(?i)^(?:my name is|i am|i'm|name is)\s+", "", clean_user_input).strip(" ,.-")
                        if 1 <= len(candidate) <= 80:
                            current_custom["customer_name"] = candidate
                    if current_custom.get("customer_name") and not current_custom.get("customer_contact"):
                        reply = f"Thanks, {current_custom['customer_name']}. What's your contact number or email?"
                    elif current_custom.get("customer_contact") and not current_custom.get("customer_name"):
                        reply = "Thanks. What's your name?"
                    elif current_custom.get("customer_name") and current_custom.get("customer_contact"):
                        st.session_state.custom_request_stage = "confirm"
                        reply, _ = custom_next_question(current_custom)
                    else:
                        reply = "What's your name and contact number or email?"

                elif custom_stage == "confirm":
                    if re.search(r"\b(yes|yeah|yep|yup|confirm|send|sure|ok|okay)\b", low):
                        try:
                            saved = submit_protected_custom_request(business["slug"], current_custom)
                            request_number = saved.get("request_number")
                            st.session_state.order_saved = True
                            st.session_state.order_number = request_number
                            current_custom["status"] = "confirmed"
                            st.session_state.custom_request_stage = None
                            notification_email = st.secrets.get("ORDER_NOTIFICATION_EMAIL")
                            send_custom_request_notification(business_name, notification_email, request_number, current_custom)
                            reply = f"Custom request sent! #{request_number}\n\nThe bakery will contact you to discuss the details, final price and payment."
                        except Exception:
                            reply = "I couldn't send the request just yet. Please try confirming again."
                    elif re.search(r"\b(no|nope|nah)\b", low):
                        reply = "No problem. I haven't sent it. Tell me what you'd like to change."
                        st.session_state.custom_request_stage = "quantity"
                    else:
                        reply = "Would you like me to send this custom request to the bakery?"

                st.session_state.current_order = current_custom
                if reply:
                    st.session_state.display_messages.append({"role":"assistant","content":reply})
                    st.session_state.messages.append({"role":"assistant","content":reply})
                    st.rerun()

            # Resolve a pending off-menu offer deterministically.
            pending_custom = st.session_state.get("pending_custom_item")
            if pending_custom:
                if re.search(r"(?i)\b(yes|yeah|yep|yup|sure|okay|ok|please|do it)\b", clean_user_input):
                    reply = f"Sure. How many {pending_custom} would you like?"
                    st.session_state.custom_request_stage = "quantity"
                    st.session_state.current_order = {
                        "items": [{"item": pending_custom, "quantity": None, "customizations": ""}],
                        "order_type": "custom_request",
                        "requested_datetime": None,
                        "requested_datetime_iso": None,
                        "fulfillment": None,
                        "customer_name": None,
                        "customer_contact": None,
                        "delivery_address": None,
                        "status": "in_progress",
                    }
                    st.session_state.pending_custom_item = None
                    st.session_state.display_messages.append({"role":"assistant","content":reply})
                    st.session_state.messages.append({"role":"assistant","content":reply})
                    st.rerun()
                if re.search(r"(?i)\b(no|nope|nah|cancel|never mind|nevermind)\b", clean_user_input):
                    reply = "No problem. What else would you like?"
                    st.session_state.pending_custom_item = None
                    st.session_state.display_messages.append({"role":"assistant","content":reply})
                    st.session_state.messages.append({"role":"assistant","content":reply})
                    st.rerun()

            requested_item, is_menu_item = detect_requested_product(clean_user_input, menu)
            if requested_item and is_menu_item is False:
                st.session_state.pending_custom_item = requested_item
                reply = custom_request_prompt(requested_item, business_name)
                st.session_state.display_messages.append({"role":"assistant","content":reply})
                st.session_state.messages.append({"role":"assistant","content":reply})
                st.rerun()

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
    order_label = (f"Your custom request ({order_count} item{'s' if order_count != 1 else ''})" if order and order.get("order_type") == "custom_request" else f"Your order ({order_count} item{'s' if order_count != 1 else ''})")
    with st.expander(order_label, expanded=bool(order_count)):
        if order_count:
            for item in order["items"]:
                st.markdown(f"**{item.get('quantity', 1)} × {item.get('item', 'Unknown')}**")
                if item.get("customizations"):
                    st.caption(item["customizations"])
            st.divider()
            st.write(f"**Requested for:** {order.get('requested_datetime', 'not specified')}")
            if order.get("order_type") != "custom_request":
                st.write(f"**Estimated total:** {order.get('estimated_total', 'N/A')}")
            st.write(f"**Fulfillment:** {order.get('fulfillment', 'unspecified')}")
            if order.get("order_type") == "custom_request":
                if order.get("status") == "confirmed":
                    st.success(f"Custom request #{st.session_state.get('order_number')} sent")
                else:
                    st.info("Custom request in progress")
            elif order.get("status") == "confirmed":
                st.success(f"Order #{st.session_state.get('order_number')} received")
            else:
                st.info("Order in progress")
        else:
            st.markdown('<div class="order-empty">Your items will show up here as you order.</div>', unsafe_allow_html=True)

        if order_count > 0:
            if st.button("Start new order", key="top_start_new_order"):
                for key in ["messages", "display_messages", "current_order", "order_email_sent", "order_saved", "order_number", "awaiting_assistant", "pending_user_text", "pending_custom_item", "custom_request_stage"]:
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
        clean_user_input = str(st.session_state.get("pending_user_text") or "").strip()
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
            st.session_state.pending_user_text = None
            st.session_state.display_messages.append({
                "role": "assistant",
                "content": "Sorry, I'm having trouble responding right now. Please try again in a moment."
            })
            st.rerun()

        thinking_slot.empty()
        order_match = re.search(r"ORDER_SUMMARY:\s*(\{.*\})", bot_reply, re.DOTALL)
        display_reply = bot_reply

        # Persist an AI-created custom-request offer so the next "yes/yup" is
        # handled by Python instead of becoming an untracked conversational turn.
        offer_match = re.search(r'CUSTOM_REQUEST_OFFER:\s*(\{.*?\})', bot_reply or "", re.S)
        if offer_match:
            try:
                offer_data = json.loads(offer_match.group(1))
                offered_item = str(offer_data.get("item") or "").strip()
                if offered_item:
                    st.session_state.pending_custom_item = offered_item
            except Exception:
                pass
            display_reply = re.sub(
                r'\n?CUSTOM_REQUEST_OFFER:\s*\{.*?\}\s*',
                '',
                display_reply,
                flags=re.S,
            ).strip()

        # Guardrail: standard menu conversations must not surface custom-order
        # advance-notice commentary even if the model slips.
        retail_notice_patterns = [
            r"(?i)(?:okay,?\s*)?(?:so\s+)?that'?s\s+\d+\s*hours?(?:\s+and\s+\d+\s*minutes?)?\s+from\s+now\.?\s*",
            r"(?i)\b\d+\s*hours?(?:\s+and\s+\d+\s*minutes?)?\s+from\s+now\b[.!]?\s*",
            r"(?i)(?:for\s+tomorrow,?\s*)?that'?s\s+\d+(?:\.\d+)?\s*hours?'?\s+notice\.?\s*",
            r"(?i)\b\d+(?:\.\d+)?\s*hours?'?\s+notice\b[.!]?\s*",
            r"(?i)\badvance\s+notice\b[.!]?\s*",
        ]
        if not order_match or '"order_type": "custom"' not in order_match.group(1):
            for pattern in retail_notice_patterns:
                display_reply = re.sub(pattern, "", display_reply).strip()


        if order_match:
            display_reply = bot_reply[:order_match.start()].strip()
            try:
                parsed_order = json.loads(order_match.group(1))
                # Custom/off-menu requests are owned exclusively by the Python state machine.
                # Ignore any accidental custom summary emitted by the model.
                if parsed_order.get("order_type") in ("custom", "custom_request"):
                    raise json.JSONDecodeError("custom flow owned by Python", order_match.group(1), 0)
                parsed_order = recover_name_contact(clean_user_input, parsed_order)
                if not parsed_order.get("estimated_total"):
                    parsed_order["estimated_total"] = compute_order_total(parsed_order, menu)

                # Never let a relative date such as "tomorrow" silently acquire an
                # invented clock time. If this turn supplied no explicit time and the
                # prior order still had no exact time, keep datetime incomplete.
                previous_order = st.session_state.get("current_order") or {}
                if (
                    not has_explicit_time(clean_user_input)
                    and not previous_order.get("requested_datetime_iso")
                    and re.search(r"(?i)\b(today|tomorrow|day after tomorrow|monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b", clean_user_input)
                ):
                    parsed_order["requested_datetime_iso"] = None

                if parsed_order.get("status") == "confirmed" and get_missing_order_fields(parsed_order):
                    parsed_order["status"] = "in_progress"

                notice_check = (
                    check_advance_notice(parsed_order.get("requested_datetime_iso"), advance_notice)
                    if is_custom_order(parsed_order)
                    else {"checked": False}
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

                # ORDER_SUMMARY is only for normal menu orders.
                state_reply, ready_for_confirmation = deterministic_checkout_reply(parsed_order)
                if parsed_order.get("status") != "confirmed":
                    display_reply = state_reply

                if (
                    parsed_order.get("status") == "confirmed"
                    and not st.session_state.get("order_saved", False)
                ):
                    try:
                        saved = submit_protected_order(business["slug"], parsed_order)
                    except Exception:
                        parsed_order["status"] = "in_progress"
                        st.session_state.current_order = parsed_order
                        display_reply = (
                            "I couldn't securely save that order yet. "
                            "Please check the item, date/time, and delivery details and try again."
                        )
                    else:
                        notification_email = st.secrets.get("ORDER_NOTIFICATION_EMAIL")
                        parsed_order["status"] = "confirmed"
                        st.session_state.current_order = parsed_order
                        st.session_state.order_saved = True

                        db_order_number = saved.get("order_number")
                        db_total = saved.get("total")
                        parsed_order["estimated_total"] = db_total
                        st.session_state.order_number = db_order_number
                        st.session_state.orders_this_session = st.session_state.get("orders_this_session", 0) + 1
                        send_new_order_notification(
                            business_name, notification_email, db_order_number, parsed_order, db_total
                        )
                        display_reply = (
                            f"Order received! #{db_order_number}\n\n"
                            f"Final total: ₹{db_total}. "
                            "The bakery will review and accept or decline it."
                        )
                elif parsed_order.get("status") == "confirmed" and st.session_state.get("order_saved"):
                    # The model re-sends the saved order on later turns (for example after
                    # "thanks"). Only treat it as a new order when the contents differ.
                    same_order = (
                        previous_order.get("items") == parsed_order.get("items")
                        and previous_order.get("requested_datetime_iso") == parsed_order.get("requested_datetime_iso")
                    )
                    if not same_order:
                        st.session_state.current_order = previous_order or None
                        display_reply = "That order has already been received. Open Your order and tap Start new order to place another."
                elif notice_warning:
                    display_reply += f"\n\n{notice_warning}"

            except json.JSONDecodeError:
                pass

        st.session_state.messages.append({"role": "assistant", "content": bot_reply})
        # Safety recovery if the AI offered a custom request but omitted the marker.
        if (
            not st.session_state.get("pending_custom_item")
            and re.search(r"(?i)custom request", str(display_reply or ""))
        ):
            m = re.search(
                r"(?i)(?:don't have|do not have)\s+(?:an?\s+)?(.+?)\s+(?:on|in)\s+(?:the\s+)?(?:current\s+)?menu",
                str(display_reply),
            )
            if m:
                st.session_state.pending_custom_item = m.group(1).strip(" .?!")

        # Never render an empty assistant bubble.
        if not str(display_reply).strip():
            latest_text = str(clean_user_input or "").lower()
            if re.search(r"\b(can|could|would)\s+(?:u|you|the bakery)\s+(?:make|do)\b", latest_text):
                display_reply = (
                    "It isn't on the current menu, but I can help you send it as a custom "
                    "request to the bakery. Would you like to do that?"
                )
            else:
                current = st.session_state.get("current_order") or {}
                if current:
                    display_reply, _ = deterministic_checkout_reply(current)
                else:
                    display_reply = (
                        "I didn't quite catch that. You can ask about the menu, ingredients, "
                        "recommendations, opening hours, pickup or delivery, or place an order."
                    )

        if not str(display_reply or "").strip():
            display_reply = (
                "I didn't quite catch that. You can ask me about the menu, ingredients, "
                "recommendations, pickup or delivery, opening hours, or place an order."
            )

        st.session_state.display_messages.append(
            {"role": "assistant", "content": display_reply}
        )
        st.session_state.awaiting_assistant = False
        st.session_state.pending_user_text = None
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


def display_order_id(order):
    """Short human-facing order number; database IDs remain internal."""
    try:
        return f"#{1000 + int(order.get('id', 0))}"
    except Exception:
        return "#----"

def format_owner_order_time(value):
    if not value:
        return "Time not specified"
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        dt = dt.astimezone(ZoneInfo("Asia/Kolkata"))
        return dt.strftime("%a, %d %b · %I:%M %p").replace(" 0", " ")
    except Exception:
        return str(value)

def owner_view():
    st.markdown('<div class="owner-portal-marker"></div>', unsafe_allow_html=True)
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

    # ----- Loaf owner dashboard -----
    try:
        owner_orders = (
            supabase.table("orders")
            .select("id,created_at,order_number,items,estimated_total,fulfillment,requested_datetime,customer_name,customer_contact,delivery_address,status")
            .eq("bakery_id", existing_business["id"])
            .order("created_at", desc=True)
            .limit(50)
            .execute()
        ).data or []
    except Exception:
        owner_orders = []

    try:
        owner_custom_requests = (
            supabase.table("custom_requests")
            .select("id,created_at,request_number,requested_item,quantity,fulfillment,requested_datetime,customer_name,customer_contact,delivery_address,customer_notes,status")
            .eq("bakery_id", existing_business["id"])
            .order("created_at", desc=True)
            .limit(50)
            .execute()
        ).data or []
    except Exception:
        owner_custom_requests = []

    pending_custom_requests = [r for r in owner_custom_requests if r.get("status") == "pending"]
    custom_history = [r for r in owner_custom_requests if r.get("status") != "pending"]

    pending_orders = [o for o in owner_orders if o.get("status") == "pending"]
    accepted_orders = [o for o in owner_orders if o.get("status") == "accepted"]
    history_orders = [o for o in owner_orders if o.get("status") != "pending"]
    today_total = sum(float(o.get("estimated_total") or 0) for o in accepted_orders)

    head_left, head_right = st.columns([5, 1])
    with head_left:
        st.markdown(
            f"""
            <div class="owner-dashboard-head">
              <div class="owner-kicker">LOAF</div>
              <h1>{html.escape(existing_business.get("business_name") or clean_slug)}</h1>
              <p>Manage incoming orders and your bakery details.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
    with head_right:
        st.write("")
        st.write("")
        if st.button("Sign out", key="owner_dashboard_signout", use_container_width=True):
            auth_sign_out()
            st.rerun()

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("New orders", len(pending_orders))
    with m2:
        st.metric("Custom requests", len(pending_custom_requests))
    with m3:
        st.metric("Accepted", len(accepted_orders))
    with m4:
        st.metric("Accepted value", f"₹{today_total:,.0f}")

    st.markdown("## New orders")
    if not pending_orders:
        st.info("You're all caught up. No new orders.")
    else:
        for o in pending_orders:
            with st.container(border=True):
                top1, top2 = st.columns([4, 1])
                with top1:
                    st.markdown(f"### Order {display_order_id(o)}")
                with top2:
                    st.markdown('<div class="status-pill pending">PENDING</div>', unsafe_allow_html=True)

                st.markdown(
                    f"**{str(o.get('fulfillment') or '').title()} · "
                    f"{format_owner_order_time(o.get('requested_datetime'))}**"
                )

                for item in o.get("items") or []:
                    st.write(f"{item.get('quantity',1)} × {item.get('item','Item')}")
                    if item.get("customizations"):
                        st.caption(f"Note: {item.get('customizations')}")

                st.markdown(f"**Total: ₹{float(o.get('estimated_total') or 0):,.0f}**")
                st.caption(f"{o.get('customer_name')} · {o.get('customer_contact')}")
                if o.get("delivery_address"):
                    st.caption(f"Delivery: {o.get('delivery_address')}")

                ac, dc = st.columns([1,1])
                with ac:
                    if st.button("Accept", key=f"accept_order_{o['id']}", use_container_width=True, type="primary"):
                        try:
                            result=(supabase.table("orders").update({"status":"accepted"}).eq("id",o["id"]).execute())
                            if result.data: st.rerun()
                            else: st.error("Could not update this order.")
                        except Exception:
                            st.error("Could not update this order.")
                with dc:
                    if st.button("Decline", key=f"decline_order_{o['id']}", use_container_width=True):
                        try:
                            result=(supabase.table("orders").update({"status":"declined"}).eq("id",o["id"]).execute())
                            if result.data: st.rerun()
                            else: st.error("Could not update this order.")
                        except Exception:
                            st.error("Could not update this order.")

    st.markdown("## Custom requests")
    if not pending_custom_requests:
        st.caption("No new custom requests.")
    else:
        for r in pending_custom_requests:
            with st.container(border=True):
                c1, c2 = st.columns([4,1])
                with c1:
                    st.markdown(f"### Custom request #{1000 + int(r.get('id',0))}")
                with c2:
                    st.markdown('<div class="status-pill pending">PENDING</div>', unsafe_allow_html=True)
                st.markdown(f"**{r.get('quantity',1)} × {r.get('requested_item','Custom item')}**")
                st.write(
                    f"{str(r.get('fulfillment') or '').title()} · "
                    f"{format_owner_order_time(r.get('requested_datetime'))}"
                )
                st.caption(f"{r.get('customer_name')} · {r.get('customer_contact')}")
                if r.get("customer_notes"):
                    st.caption(f"Notes: {r.get('customer_notes')}")
                if r.get("delivery_address"):
                    st.caption(f"Delivery: {r.get('delivery_address')}")
                st.caption("Price and availability are not confirmed.")
                contact_value = str(r.get("customer_contact") or "")
                digits = re.sub(r"\D", "", contact_value)
                if len(digits) >= 10:
                    from urllib.parse import quote
                    bakery_label = str(existing_business.get("business_name") or "the bakery")
                    msg = (
                        f"Hi {r.get('customer_name') or ''}, this is {bakery_label} "
                        f"regarding your Loaf custom request #{1000 + int(r.get('id',0))} "
                        f"for {r.get('requested_item','your custom request')}."
                    )
                    whatsapp_url = f"https://wa.me/{digits}?text={quote(msg)}"
                    st.link_button(
                        "Contact customer on WhatsApp",
                        whatsapp_url,
                        use_container_width=True
                    )
                elif "@" in contact_value:
                    st.markdown(f"**Customer email:** {html.escape(contact_value)}")
                else:
                    st.caption("No WhatsApp-ready phone number was provided.")

                a1, a2 = st.columns(2)
                with a1:
                    if st.button("Mark confirmed", key=f"confirm_custom_{r['id']}", use_container_width=True, type="primary"):
                        try:
                            result = supabase.table("custom_requests").update({"status":"accepted"}).eq("id", r["id"]).execute()
                            if result.data:
                                st.rerun()
                            else:
                                st.error("Could not update this request.")
                        except Exception:
                            st.error("Could not update this request.")
                with a2:
                    if st.button("Decline", key=f"decline_custom_{r['id']}", use_container_width=True):
                        try:
                            result = supabase.table("custom_requests").update({"status":"declined"}).eq("id", r["id"]).execute()
                            if result.data:
                                st.rerun()
                            else:
                                st.error("Could not update this request.")
                        except Exception:
                            st.error("Could not update this request.")

    if custom_history:
        st.markdown("## Custom request history")
        for r in custom_history[:15]:
            status = str(r.get("status") or "").title()
            with st.container(border=True):
                h1, h2 = st.columns([4, 1])
                with h1:
                    st.markdown(f"**Custom request #{1000 + int(r.get('id', 0))}**")
                    st.write(f"{r.get('quantity', 1)} × {r.get('requested_item', 'Custom item')}")
                    st.caption(
                        f"{r.get('customer_name') or ''} · "
                        f"{format_owner_order_time(r.get('requested_datetime'))}"
                    )
                    if r.get("customer_contact"):
                        st.caption(f"Contact: {r.get('customer_contact')}")
                    if r.get("delivery_address"):
                        st.caption(f"Delivery: {r.get('delivery_address')}")
                    if r.get("customer_notes"):
                        st.caption(f"Notes: {r.get('customer_notes')}")
                with h2:
                    st.markdown(f"**{status}**")

    if history_orders:
        st.markdown("## Order history")
        for o in history_orders[:15]:
            status=str(o.get("status") or "").title()
            st.markdown(
                f"""
                <div class="history-row">
                  <div><strong>Order {display_order_id(o)}</strong><br>
                  <span>{html.escape(str(o.get('customer_name') or ''))} · {html.escape(format_owner_order_time(o.get('requested_datetime')))}</span></div>
                  <div class="history-right"><strong>₹{float(o.get('estimated_total') or 0):,.0f}</strong><br>
                  <span>{html.escape(status)}</span></div>
                </div>
                """,
                unsafe_allow_html=True
            )

    st.divider()
    st.markdown("## Bakery settings")
    st.caption("Update what customers see and what Loaf uses while taking orders.")

    st.markdown("### Menu")
    existing_menu = existing_business.get("menu") or []
    menu_df = pd.DataFrame(existing_menu) if existing_menu else pd.DataFrame(
        {"Item": [""], "Price": [0], "Ingredients": [""]}
    )
    # Keep the editor focused on business data, not duplicated photo URLs.
    editor_cols = [c for c in ["Item", "Price", "Ingredients"] if c in menu_df.columns]
    if editor_cols:
        menu_df = menu_df[editor_cols]
    menu = st.data_editor(menu_df, num_rows="dynamic")

    st.markdown("### Business details")
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

    st.markdown("### Fulfilment & availability")
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
    delivery_city = st.text_input(
        "Delivery city",
        value=str(existing_business.get("delivery_city") or ""),
        placeholder="e.g. Dehradun"
    )
    delivery_areas = st.text_input(
        "Delivery areas (comma separated)",
        value=", ".join(existing_business.get("delivery_areas") or []),
        placeholder="e.g. Prem Nagar, Kandoli, Bidholi, UPES"
    )
    st.caption("Loaf will only accept delivery addresses in this city and these listed areas.")

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
                    "delivery_city": delivery_city.strip() or None,
                    "delivery_areas": [x.strip() for x in delivery_areas.split(",") if x.strip()],
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
