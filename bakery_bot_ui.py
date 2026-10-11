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

params = st.query_params
slug_from_url = params.get("slug", "")
mode = params.get("mode", "customer")

st.set_page_config(page_title="Loaf")

# Loaf playful theme: periwinkle page, pink, lime and sky blocks, chunky outlines.
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:wght@400;600;800&family=DM+Mono:wght@400;500&display=swap');
:root { --blue:#6F86D6; --pink:#F2B8D6; --cream:#F6ECDF; --lime:#C8CE7C; --sky:#BFD6E8; --lav:#C9B8EA; --ink:#1B1B1B; --paper:#F6ECDF; }
html, body, [class*="css"] { font-family:"Bricolage Grotesque", sans-serif; }
*, *::before, *::after { transition:none !important; }
.stApp { background:var(--blue); color:var(--ink); }
.block-container { max-width:760px; padding:0 20px 3rem !important; margin:0 auto !important; background:transparent; }
#MainMenu, footer { visibility:hidden; }
header[data-testid="stHeader"], .stApp > header, [data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"],
[data-testid="stSidebar"], [data-testid="stBottom"], [data-testid="stBottomBlockContainer"] { display:none !important; height:0 !important; }
[data-testid="stVerticalBlock"] { gap:.7rem; }
*:focus-visible { outline:3px solid var(--ink); outline-offset:2px; }
.loaf-wordmark { font-weight:800; font-size:18px; }
.loaf-top { display:flex; justify-content:space-between; align-items:baseline; background:var(--lime); border:2px solid var(--ink); border-top:0; padding:8px 14px; margin:0 0 16px; font-family:"DM Mono", monospace; font-size:12px; }
.loaf-top-mark { font-family:"Bricolage Grotesque", sans-serif; font-weight:800; font-size:15px; }
.pw-strip, .pw-rule { display:none; }
.pw-gingham { position:relative; overflow:hidden; background:var(--pink); border:2px solid var(--ink); padding:30px 22px 28px; }
.pw-label { position:relative; z-index:2; max-width:72%; margin:0; padding:0; background:transparent; border:0; text-align:left; }
.bakery-name { font-weight:800; font-size:clamp(34px, 8vw, 60px); line-height:1; letter-spacing:-.02em; margin:0 0 10px; }
.bakery-subtitle { font-size:15px; line-height:1.5; margin:0; }
.t2-half { position:absolute; right:-34px; top:-14px; width:140px; height:140px; background:var(--lime); border:2px solid var(--ink); border-radius:50%; }
.t2-squig { position:absolute; right:22px; bottom:12px; width:96px; height:44px; background:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 40'><path d='M3 22 C12 2 22 38 32 20 S52 4 61 20' fill='none' stroke='%236F86D6' stroke-width='7' stroke-linecap='round'/></svg>") no-repeat center / contain; }
.assistant-intro { background:var(--cream); border:2px solid var(--ink); padding:16px 18px; margin:14px 0 6px; }
.assistant-title { font-weight:800; font-size:22px; margin-bottom:4px; }
.assistant-copy { font-size:14px; line-height:1.5; }
.chat-row { display:flex; width:100%; margin:12px 0; }
.chat-row.user { justify-content:flex-end; }
.chat-wrap { max-width:84%; }
.chat-name { font-family:"DM Mono", monospace; font-size:11px; margin:0 0 4px 6px; }
.chat-row.user .chat-name { text-align:right; margin:0 6px 4px 0; }
.chat-bubble { font-size:15px; line-height:1.55; padding:10px 15px; border:2px solid var(--ink); border-radius:18px; }
.chat-row.assistant .chat-bubble { background:var(--cream); border-bottom-left-radius:4px; }
.chat-row.user .chat-bubble { background:var(--lime); border-bottom-right-radius:4px; }
[data-testid="stChatMessage"] { display:none; }
[data-testid="stForm"] { width:100% !important; margin:16px 0 6px !important; padding:5px !important; border:2px solid var(--ink) !important; border-radius:999px !important; background:var(--cream) !important; }
[data-testid="stForm"] [data-testid="stHorizontalBlock"] { display:grid !important; grid-template-columns:minmax(0, 1fr) 44px !important; gap:6px !important; align-items:center !important; width:100% !important; }
[data-testid="stForm"] [data-testid="stColumn"], [data-testid="stForm"] [data-testid="column"] { width:auto !important; min-width:0 !important; flex:none !important; }
[data-testid="stForm"] [data-baseweb], [data-testid="stForm"] [data-testid="stTextInputRootElement"] { background:transparent !important; border:0 !important; box-shadow:none !important; }
[data-testid="stForm"] input { background:transparent !important; border:0 !important; box-shadow:none !important; height:44px !important; padding:0 16px !important; font-size:15px !important; color:var(--ink) !important; }
[data-testid="InputInstructions"], [data-testid="stInputInstructions"], .stTextInput small { display:none !important; }
[data-testid="stFormSubmitButton"] button, [data-testid="stFormSubmitButton"] button:hover { width:44px !important; min-width:44px !important; height:44px !important; padding:0 !important; border-radius:50% !important; background:var(--pink) !important; color:var(--ink) !important; border:2px solid var(--ink) !important; font-size:18px !important; }
.pw-section-head { display:flex; align-items:center; gap:12px; flex-wrap:wrap; margin:22px 0 14px; }
.popular-title { font-weight:800; font-size:28px; background:var(--cream); border:2px solid var(--ink); padding:2px 14px; }
.script-note { background:var(--pink); border:2px solid var(--ink); border-radius:999px; font-family:"DM Mono", monospace; font-size:11px; padding:2px 10px; }
.product-card-shell { background:var(--cream); border:2px solid var(--ink); margin:0 0 16px; overflow:hidden; }
.tile-1 { background:var(--sky); } .tile-2 { background:var(--lav); }
.product-card-media { padding:0; }
.product-card-photo { display:block; width:100%; aspect-ratio:1 / 1; object-fit:cover; border-bottom:2px solid var(--ink); }
.product-card-photo.placeholder { display:flex; align-items:center; justify-content:center; font-weight:800; font-size:56px; background:var(--pink); }
.product-card-copy { padding:10px 12px 14px; }
.product-card-topline { display:flex; justify-content:space-between; align-items:center; gap:8px; }
.product-card-name { font-weight:800; font-size:18px; line-height:1.15; }
.product-card-price { font-family:"DM Mono", monospace; font-size:13px; background:var(--pink); border:2px solid var(--ink); border-radius:999px; padding:1px 9px; white-space:nowrap; }
.product-card-desc { margin-top:6px; font-size:13px; line-height:1.5; }
[data-testid="stExpander"] { background:transparent !important; border:0 !important; margin-bottom:10px; }
[data-testid="stExpander"] details { background:var(--cream) !important; border:2px solid var(--ink) !important; border-radius:0 !important; }
[data-testid="stExpander"] summary { font-weight:800; font-size:16px; color:var(--ink); }
.order-empty { font-size:14px; }
.stButton > button, .stButton > button:hover { background:var(--ink); color:var(--cream); border:2px solid var(--ink); border-radius:999px; font-weight:600; padding:.4rem 1.3rem; }
.loaf-footer { text-align:center; font-family:"DM Mono", monospace; font-size:11px; margin-top:32px; }
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


@media (max-width:768px) { .block-container { padding:0 12px 2.2rem !important; } .pw-label { max-width:76%; } .t2-half { width:96px; height:96px; right:-26px; } .bakery-name { font-size:clamp(30px, 9vw, 44px); } }

/* ===== THEME 2 V2: PLAYFUL MODERN ===== */
:root{
 --ink:#25231F; --cream:#FFF8EA; --paper:#FFFDF7;
 --blue:#7189D8; --pink:#F3B7D0; --sage:#C8D18D;
 --butter:#F3D978; --sky:#C9DDF0; --muted:#716A63;
}
.stApp{background:var(--cream)!important;color:var(--ink)!important}
.block-container{max-width:900px!important;padding:0 28px 3rem!important}

/* top */
.loaf-top{
 background:transparent!important;border:0!important;
 border-bottom:1px solid rgba(37,35,31,.25)!important;
 padding:18px 0 12px!important;margin:0 0 18px!important;
}
.loaf-top-mark{
 background:var(--butter)!important;padding:4px 10px!important;
 border-radius:999px!important;font-size:15px!important;
}

/* hero */
.pw-gingham{
 position:relative!important;overflow:hidden!important;
 background:var(--paper)!important;
 border:1px solid rgba(37,35,31,.20)!important;
 padding:38px 38px 36px!important;margin:0 0 24px!important;
 box-shadow:8px 8px 0 var(--blue)!important;
}
.pw-label{max-width:68%!important}
.bakery-name{
 font-size:clamp(44px,8vw,76px)!important;line-height:.94!important;
 letter-spacing:-.045em!important;margin:0 0 16px!important;
}
.bakery-subtitle{color:var(--muted)!important;max-width:520px!important}
.t2-half{
 right:28px!important;top:28px!important;width:112px!important;height:112px!important;
 background:var(--pink)!important;border:0!important;
}
.t2-half:after{
 content:"";position:absolute;width:66px;height:66px;right:-22px;bottom:-20px;
 background:var(--sage);border-radius:18px;transform:rotate(13deg);
}
.t2-squig{right:88px!important;bottom:24px!important;width:108px!important;height:44px!important}

/* ordering area */
.assistant-intro{
 background:var(--sky)!important;border:0!important;border-radius:20px!important;
 padding:22px 24px!important;margin:10px 0 8px!important;
}
.assistant-intro:before{
 content:"ASK + ORDER";display:inline-block;margin-bottom:8px;
 font-family:"DM Mono",monospace;font-size:10px;
 background:var(--paper);padding:4px 8px;border-radius:999px;
}
.assistant-title{font-size:25px!important;letter-spacing:-.025em!important}
.assistant-copy{color:#52524D!important}

/* chat */
.chat-name{color:var(--muted)!important}
.chat-bubble{
 border:0!important;border-radius:15px!important;
 box-shadow:0 0 0 1px rgba(37,35,31,.14)!important;
 font-size:14px!important;
}
.chat-row.assistant .chat-bubble{background:var(--paper)!important}
.chat-row.user .chat-bubble{background:var(--pink)!important}

/* input */
[data-testid="stForm"]{
 background:var(--paper)!important;border:1px solid rgba(37,35,31,.22)!important;
 border-radius:16px!important;box-shadow:0 5px 18px rgba(37,35,31,.04)!important;
}
[data-testid="stForm"]:focus-within{
 border-color:var(--blue)!important;box-shadow:0 0 0 1px var(--blue)!important;
}
[data-testid="stFormSubmitButton"] button,
[data-testid="stFormSubmitButton"] button:hover{
 background:var(--blue)!important;color:white!important;border:0!important;
 border-radius:12px!important;
}

/* menu */
.pw-section-head{margin:30px 0 15px!important}
.popular-title{
 background:transparent!important;border:0!important;padding:0!important;
 font-size:34px!important;letter-spacing:-.035em!important;
}
.script-note{
 background:var(--butter)!important;border:0!important;
 border-radius:999px!important;padding:5px 10px!important;
}
.product-card-shell{
 border:0!important;border-radius:18px!important;
 background:var(--paper)!important;
 box-shadow:0 0 0 1px rgba(37,35,31,.13)!important;
 overflow:hidden!important;
}
.tile-0{background:var(--paper)!important}
.tile-1{background:#F7DCE8!important}
.tile-2{background:#E6EACD!important}
.product-card-photo{
 width:100%!important;height:255px!important;aspect-ratio:auto!important;
 object-fit:cover!important;border:0!important;
}
.product-card-copy{padding:14px 15px 16px!important}
.product-card-name{font-size:19px!important;letter-spacing:-.02em!important}
.product-card-price{
 background:transparent!important;border:0!important;border-radius:0!important;
 padding:0!important;font-size:12px!important;
}
.product-card-desc{color:#625D57!important;font-size:12px!important}

/* controls */
[data-testid="stExpander"] details{
 background:var(--paper)!important;border:1px solid rgba(37,35,31,.18)!important;
 border-radius:14px!important;
}
.stButton>button,.stButton>button:hover{
 background:var(--blue)!important;color:white!important;border:0!important;
 border-radius:12px!important;
}
.loaf-footer{color:#938A82!important}

@media(max-width:768px){
 .block-container{padding:0 16px 2.2rem!important}
 .pw-gingham{
   padding:27px 20px 76px!important;margin-top:12px!important;
   box-shadow:5px 5px 0 var(--blue)!important;
 }
 .pw-label{max-width:100%!important}
 .bakery-name{font-size:clamp(38px,12vw,54px)!important}
 .bakery-subtitle{max-width:88%!important}
 .t2-half{
   width:74px!important;height:74px!important;right:16px!important;
   top:auto!important;bottom:10px!important;
 }
 .t2-half:after{width:40px;height:40px;right:-10px;bottom:-8px;border-radius:11px}
 .t2-squig{right:72px!important;bottom:14px!important;width:78px!important;height:32px!important}
 .assistant-intro{padding:18px!important;border-radius:16px!important}
 .popular-title{font-size:29px!important}
 .product-card-photo{height:245px!important}
}


/* ===== THEME 2 FINAL REFINEMENTS ===== */

/* Match Theme 1 cream exactly */
:root{
  --cream:#FFF7E6;
  --paper:#FFFDF7;
}
.stApp{background:#FFF7E6!important}

/* Hero: remove random decorative shapes, keep purposeful blue offset */
.t2-half,.t2-squig{display:none!important}
.pw-gingham{
  background:var(--paper)!important;
  padding:38px 38px 34px!important;
  min-height:0!important;
  box-shadow:8px 8px 0 var(--blue)!important;
}
.pw-label{max-width:82%!important}

/* Make ordering block slightly lighter/shorter */
.assistant-intro{
  padding:18px 22px!important;
  background:#D7E5F2!important;
}
.assistant-intro:before{
  content:"ORDER ASSISTANT"!important;
}

/* Modern section heading */
.popular-title{
  font-size:32px!important;
  text-transform:uppercase!important;
  letter-spacing:-.025em!important;
}
.script-note{
  background:var(--butter)!important;
  text-transform:uppercase!important;
  letter-spacing:.04em!important;
}

/* Photography-led menu: no coloured card boxes */
.product-card-shell,
.tile-0,.tile-1,.tile-2{
  background:transparent!important;
  border:0!important;
  border-radius:0!important;
  box-shadow:none!important;
  overflow:visible!important;
  margin-bottom:24px!important;
}
.product-card-media{
  background:transparent!important;
  padding:0!important;
}
.product-card-photo{
  width:100%!important;
  height:270px!important;
  aspect-ratio:auto!important;
  object-fit:cover!important;
  border-radius:14px!important;
  border:0!important;
  box-shadow:0 0 0 1px rgba(37,35,31,.12)!important;
}
.product-card-photo.placeholder{
  background:var(--pink)!important;
}
.product-card-copy{
  padding:11px 2px 0!important;
  background:transparent!important;
}
.product-card-topline{
  align-items:baseline!important;
}
.product-card-name{
  font-size:18px!important;
  text-transform:uppercase!important;
  letter-spacing:-.01em!important;
}
.product-card-price{
  font-size:12px!important;
  font-weight:500!important;
  color:var(--ink)!important;
}
.product-card-desc{
  margin-top:5px!important;
  color:#706861!important;
}

/* purposeful colour accents instead of random shapes */
.pw-section-head:before{
  content:"";
  display:block;
  width:34px;
  height:8px;
  background:var(--pink);
  border-radius:999px;
  margin-right:2px;
}

/* mobile */
@media(max-width:768px){
  .pw-gingham{
    padding:28px 20px 26px!important;
    box-shadow:5px 5px 0 var(--blue)!important;
  }
  .pw-label{max-width:100%!important}
  .assistant-intro{padding:16px!important}
  .product-card-photo{height:250px!important}
  .popular-title{font-size:27px!important}
}


/* ===== THEME 2 RESPONSIVE SIZE PASS ===== */

/* Desktop: make the hero name less oversized */
.bakery-name{
  font-size:clamp(38px,6vw,62px)!important;
  line-height:.98!important;
}
.pw-gingham{
  padding:30px 34px 28px!important;
}

/* Menu photos should feel like browse cards, not giant posters */
.product-card-photo{
  height:220px!important;
  object-fit:cover!important;
  object-position:center!important;
}

/* Mobile is intentionally much more compact */
@media(max-width:768px){
  .block-container{
    padding:0 14px 2rem!important;
  }
  .loaf-top{
    padding:10px 0 9px!important;
    margin-bottom:12px!important;
  }
  .pw-gingham{
    margin:0 0 18px!important;
    padding:22px 18px 20px!important;
    box-shadow:4px 4px 0 var(--blue)!important;
  }
  .bakery-name{
    font-size:clamp(32px,9vw,42px)!important;
    line-height:1!important;
    margin-bottom:10px!important;
  }
  .bakery-subtitle{
    font-size:13px!important;
    line-height:1.45!important;
    max-width:100%!important;
  }
  .assistant-intro{
    padding:14px 16px!important;
    border-radius:14px!important;
  }
  .assistant-title{
    font-size:20px!important;
  }
  .assistant-copy{
    font-size:13px!important;
  }
  .popular-title{
    font-size:24px!important;
  }
  .pw-section-head{
    gap:8px!important;
    margin:23px 0 12px!important;
  }
  .pw-section-head:before{
    width:24px!important;
    height:6px!important;
  }
  .script-note{
    font-size:9px!important;
    padding:4px 8px!important;
  }
  .product-card-photo{
    height:190px!important;
    border-radius:12px!important;
  }
  .product-card-copy{
    padding:9px 2px 0!important;
  }
  .product-card-name{
    font-size:16px!important;
  }
  .product-card-desc{
    font-size:11px!important;
  }
}


/* ===== THEME 2 V4: FOOD-FIRST PLAYFUL MODERN ===== */

/* Remove the boxed-assignment feeling */
.loaf-top{
  border-bottom:0!important;
  padding:18px 2px 8px!important;
  margin-bottom:6px!important;
}
.loaf-top-mark{
  background:var(--butter)!important;
  border-radius:999px!important;
  padding:5px 11px!important;
}

/* Hero is open, not a card */
.pw-gingham{
  background:transparent!important;
  border:0!important;
  box-shadow:none!important;
  padding:34px 2px 26px!important;
  margin:0!important;
  overflow:visible!important;
}
.pw-label{
  max-width:70%!important;
}
.bakery-name{
  font-size:clamp(40px,6.5vw,66px)!important;
  line-height:.94!important;
  margin-bottom:13px!important;
}
.bakery-subtitle{
  max-width:500px!important;
  color:#655F59!important;
}

/* Replace decorative shapes with a bakery/photo-style colour panel */
.pw-gingham:after{
  content:"FRESH BAKES\A MADE DAILY";
  white-space:pre;
  position:absolute;
  right:4px;
  top:28px;
  width:150px;
  height:150px;
  display:flex;
  align-items:flex-end;
  justify-content:flex-start;
  box-sizing:border-box;
  padding:16px;
  background:linear-gradient(145deg,var(--pink) 0 58%,var(--butter) 58% 100%);
  border-radius:24px;
  color:var(--ink);
  font-family:"DM Mono",monospace;
  font-size:11px;
  font-weight:500;
  line-height:1.45;
  transform:rotate(3deg);
}
.t2-half,.t2-squig{display:none!important}

/* Remove information-callout panel; make ordering feel like part of page */
.assistant-intro{
  background:transparent!important;
  border:0!important;
  border-radius:0!important;
  padding:14px 2px 6px!important;
  margin:0!important;
}
.assistant-intro:before{display:none!important}
.assistant-title{
  font-size:28px!important;
  margin-bottom:5px!important;
}
.assistant-copy{
  max-width:620px!important;
  font-size:14px!important;
}

/* Input becomes the visual CTA */
[data-testid="stForm"]{
  margin:14px 0 14px!important;
  border:2px solid var(--ink)!important;
  border-radius:999px!important;
  box-shadow:none!important;
}
[data-testid="stForm"]:focus-within{
  border-color:var(--blue)!important;
}
[data-testid="stFormSubmitButton"] button,
[data-testid="stFormSubmitButton"] button:hover{
  border-radius:50%!important;
  background:var(--blue)!important;
}

/* Menu is open and photography-led */
.pw-section-head{
  margin:34px 0 16px!important;
  display:flex!important;
  align-items:baseline!important;
}
.pw-section-head:before{display:none!important}
.popular-title{
  font-size:30px!important;
  text-transform:none!important;
  letter-spacing:-.035em!important;
}
.script-note{
  background:var(--pink)!important;
  text-transform:uppercase!important;
  letter-spacing:.04em!important;
  transform:rotate(-2deg);
}
.product-card-shell,.tile-0,.tile-1,.tile-2{
  background:transparent!important;
  box-shadow:none!important;
  border:0!important;
  border-radius:0!important;
}
.product-card-photo{
  height:235px!important;
  border-radius:18px!important;
  box-shadow:none!important;
}
.product-card-copy{
  padding:10px 3px 0!important;
}
.product-card-name{
  text-transform:none!important;
  font-size:19px!important;
}
.product-card-price{
  font-size:12px!important;
}
.product-card-desc{
  font-size:12px!important;
}

/* Small intentional colour tabs on alternating images */
.tile-0 .product-card-media,
.tile-1 .product-card-media,
.tile-2 .product-card-media{position:relative}
.tile-0 .product-card-media:after,
.tile-1 .product-card-media:after,
.tile-2 .product-card-media:after{
  position:absolute;left:12px;top:12px;
  padding:5px 9px;border-radius:999px;
  font-family:"DM Mono",monospace;font-size:9px;font-weight:500;
}
.tile-0 .product-card-media:after{content:"BAKED";background:var(--butter)}
.tile-1 .product-card-media:after{content:"FAVOURITE";background:var(--pink)}
.tile-2 .product-card-media:after{content:"PICK";background:var(--sage)}

@media(max-width:768px){
  .block-container{padding:0 16px 2rem!important}
  .loaf-top{padding-top:10px!important}
  .pw-gingham{
    padding:24px 0 122px!important;
  }
  .pw-label{max-width:100%!important}
  .bakery-name{
    font-size:clamp(34px,10vw,44px)!important;
    max-width:100%!important;
  }
  .bakery-subtitle{
    max-width:100%!important;
    font-size:13px!important;
  }
  .pw-gingham:after{
    width:104px;height:94px;right:4px;top:auto;bottom:14px;
    padding:11px;border-radius:18px;font-size:9px;
  }
  .assistant-intro{
    padding:6px 0 3px!important;
  }
  .assistant-title{
    font-size:22px!important;
  }
  .assistant-copy{
    font-size:13px!important;
  }
  .popular-title{
    font-size:25px!important;
  }
  .product-card-photo{
    height:190px!important;
    border-radius:14px!important;
  }
  .product-card-name{
    font-size:16px!important;
  }
  .product-card-desc{
    font-size:11px!important;
  }
}


/* ===== THEME 2 V5: BLUE + CREAM FINAL DIRECTION ===== */
:root{
  --cream:#FFF7E6;
  --paper:#FFFDF7;
  --blue:#7189D8;
  --blue-soft:#D7E3F4;
  --pink:#F3B7D0;
  --sage:#C8D18D;
  --butter:#F3D978;
  --ink:#25231F;
  --muted:#716A63;
}
.stApp{background:var(--cream)!important}

/* Hero: open cream layout with a purposeful blue accent */
.pw-gingham{
  position:relative!important;
  background:var(--paper)!important;
  border:0!important;
  border-radius:0!important;
  padding:32px 34px 30px!important;
  margin:8px 0 22px!important;
  box-shadow:8px 8px 0 var(--blue)!important;
  overflow:visible!important;
}
.pw-gingham:after{display:none!important}
.pw-label{max-width:100%!important}
.bakery-name{
  max-width:720px!important;
  font-size:clamp(40px,6vw,62px)!important;
}
.bakery-subtitle{max-width:560px!important}

/* Blue/cream ordering area without the report-callout feeling */
.assistant-intro{
  background:var(--blue-soft)!important;
  border:0!important;
  border-radius:22px!important;
  padding:18px 22px!important;
  margin:8px 0 7px!important;
  position:relative!important;
}
.assistant-intro:before{
  display:block!important;
  content:"START YOUR ORDER"!important;
  width:max-content!important;
  margin:0 0 8px!important;
  padding:4px 9px!important;
  background:var(--paper)!important;
  border-radius:999px!important;
  font-family:"DM Mono",monospace!important;
  font-size:9px!important;
  letter-spacing:.04em!important;
}
.assistant-title{font-size:25px!important}
.assistant-copy{color:#51545B!important}

/* Chat/input keep the blue as the action colour */
.chat-row.user .chat-bubble{background:var(--pink)!important}
[data-testid="stForm"]{
  background:var(--paper)!important;
  border:1.5px solid var(--blue)!important;
  border-radius:999px!important;
}
[data-testid="stFormSubmitButton"] button,
[data-testid="stFormSubmitButton"] button:hover{
  background:var(--blue)!important;
  color:white!important;
  border:0!important;
}

/* Menu stays photography-first */
.pw-section-head{
  padding-bottom:8px!important;
  border-bottom:3px solid var(--blue)!important;
}
.popular-title{
  color:var(--ink)!important;
  font-size:30px!important;
}
.script-note{
  background:var(--pink)!important;
  color:var(--ink)!important;
  transform:none!important;
}
.product-card-shell,.tile-0,.tile-1,.tile-2{
  background:transparent!important;
  border:0!important;
  box-shadow:none!important;
}
.product-card-photo{
  height:225px!important;
  border-radius:16px!important;
}
.tile-0 .product-card-media:after{content:"BAKED TODAY"!important;background:var(--butter)!important}
.tile-1 .product-card-media:after{content:"FAVOURITE"!important;background:var(--pink)!important}
.tile-2 .product-card-media:after{content:"OUR PICK"!important;background:var(--sage)!important}

/* Small blue detail at the top, instead of random shapes */
.loaf-top{
  border-bottom:1px solid rgba(113,137,216,.45)!important;
}
.loaf-top-mark{
  background:var(--blue)!important;
  color:white!important;
}

/* Mobile */
@media(max-width:768px){
  .pw-gingham{
    padding:22px 18px 20px!important;
    margin:6px 0 17px!important;
    box-shadow:5px 5px 0 var(--blue)!important;
  }
  .bakery-name{
    font-size:clamp(32px,9vw,42px)!important;
    margin-bottom:9px!important;
  }
  .bakery-subtitle{
    font-size:13px!important;
    max-width:100%!important;
  }
  .assistant-intro{
    padding:14px 16px!important;
    border-radius:16px!important;
  }
  .assistant-title{font-size:21px!important}
  .assistant-copy{font-size:13px!important}
  .popular-title{font-size:24px!important}
  .pw-section-head{
    margin-top:25px!important;
    padding-bottom:7px!important;
  }
  .product-card-photo{
    height:185px!important;
    border-radius:13px!important;
  }
  .product-card-name{font-size:16px!important}
  .product-card-desc{font-size:11px!important}
}


/* ===== THEME 2 V6: SPLIT EDITORIAL STOREFRONT ===== */
:root{
  --cream:#FFF7E6; --paper:#FFFDF7; --blue:#7189D8;
  --blue-soft:#D7E3F4; --pink:#F3B7D0; --sage:#C8D18D;
  --butter:#F3D978; --ink:#25231F; --muted:#716A63;
}
.stApp{background:var(--cream)!important}
.block-container{max-width:980px!important}

/* top bar */
.loaf-top{
  padding:16px 0 12px!important;margin:0 0 16px!important;
  border-bottom:1px solid rgba(37,35,31,.18)!important;
}
.loaf-top-mark{
  background:var(--blue)!important;color:white!important;
  padding:5px 11px!important;border-radius:999px!important;
}

/* Hero becomes a split editorial composition */
.pw-gingham{
  display:grid!important;
  grid-template-columns:minmax(0,1.05fr) minmax(280px,.95fr)!important;
  min-height:330px!important;
  padding:0!important;margin:0 0 28px!important;
  background:var(--paper)!important;border:0!important;
  box-shadow:none!important;overflow:hidden!important;
  border-radius:24px!important;
}
.pw-label{
  max-width:none!important;padding:42px 38px!important;
  display:flex!important;flex-direction:column!important;justify-content:center!important;
  position:relative!important;
}
.pw-label:before{
  content:"FRESH BAKES • MADE DAILY";
  width:max-content;margin-bottom:18px;padding:5px 9px;
  background:var(--butter);border-radius:999px;
  font-family:"DM Mono",monospace;font-size:9px;letter-spacing:.04em;
}
.bakery-name{
  font-size:clamp(44px,6vw,68px)!important;line-height:.92!important;
  max-width:480px!important;margin-bottom:18px!important;
}
.bakery-subtitle{
  max-width:430px!important;font-size:15px!important;line-height:1.55!important;
}
.pw-gingham:after{
  display:block!important;
  content:"";
  position:static!important;
  width:auto!important;height:auto!important;
  background:
    linear-gradient(rgba(113,137,216,.08),rgba(113,137,216,.08)),
    url("https://images.unsplash.com/photo-1578985545062-69928b1d9587?auto=format&fit=crop&w=900&q=80") center/cover no-repeat!important;
  border-radius:0!important;transform:none!important;
}
.t2-half,.t2-squig{display:none!important}

/* Remove the Theme-1-like order card entirely */
.assistant-intro{
  background:transparent!important;border:0!important;border-radius:0!important;
  padding:0!important;margin:0 0 6px!important;
}
.assistant-intro:before{display:none!important}
.assistant-title{
  font-size:28px!important;margin:0 0 4px!important;
}
.assistant-title:before{
  content:"What are you craving?";
  font-size:28px;
}
.assistant-title{font-size:0!important}
.assistant-copy{
  font-size:14px!important;color:var(--muted)!important;max-width:620px!important;
}

/* chat feels like the action area */
.chat-row{margin:10px 0!important}
[data-testid="stForm"]{
  margin:13px 0 22px!important;background:var(--paper)!important;
  border:2px solid var(--blue)!important;border-radius:999px!important;
  box-shadow:none!important;
}

/* editorial menu */
.pw-section-head{
  border:0!important;margin:38px 0 18px!important;padding:0!important;
}
.popular-title{font-size:32px!important}
.script-note{background:var(--pink)!important}

/* alternating image scale creates a magazine feel */
.product-card-shell,.tile-0,.tile-1,.tile-2{
  background:transparent!important;border:0!important;box-shadow:none!important;
  border-radius:0!important;margin-bottom:30px!important;
}
.product-card-photo{
  height:300px!important;border-radius:18px!important;
  object-fit:cover!important;
}
.tile-1 .product-card-photo{height:245px!important;margin-top:42px!important}
.tile-2 .product-card-photo{height:275px!important}
.product-card-copy{padding:10px 3px 0!important}
.product-card-name{font-size:19px!important;text-transform:none!important}
.product-card-desc{font-size:12px!important}
.product-card-price{font-size:12px!important}

/* small labels remain playful */
.tile-0 .product-card-media:after,
.tile-1 .product-card-media:after,
.tile-2 .product-card-media:after{
  top:12px!important;left:12px!important;
}

/* Mobile: split hero becomes name then visual, menu stays compact */
@media(max-width:768px){
  .block-container{padding:0 14px 2rem!important}
  .pw-gingham{
    display:grid!important;
    grid-template-columns:1fr!important;
    min-height:0!important;border-radius:18px!important;
    margin-bottom:20px!important;
  }
  .pw-label{padding:25px 20px 22px!important}
  .pw-label:before{margin-bottom:13px!important}
  .bakery-name{
    font-size:clamp(34px,10vw,44px)!important;
    max-width:100%!important;margin-bottom:10px!important;
  }
  .bakery-subtitle{font-size:13px!important;max-width:100%!important}
  .pw-gingham:after{
    height:190px!important;
  }
  .assistant-title:before{font-size:22px!important}
  .assistant-copy{font-size:13px!important}
  .popular-title{font-size:25px!important}
  .product-card-photo,
  .tile-1 .product-card-photo,
  .tile-2 .product-card-photo{
    height:190px!important;margin-top:0!important;border-radius:14px!important;
  }
  .product-card-shell{margin-bottom:20px!important}
  .product-card-name{font-size:16px!important}
  .product-card-desc{font-size:11px!important}
}


/* ===== THEME 2 V7: CLEAN MODERN BLUE + CREAM ===== */
:root{
  --cream:#FFF7E6;
  --paper:#FFFCF5;
  --blue:#7189D8;
  --blue-dark:#5F78CF;
  --pink:#F3B7D0;
  --ink:#25231F;
  --muted:#716A63;
}
.stApp{background:var(--cream)!important}
.block-container{max-width:940px!important;padding:0 24px 3rem!important}

/* Simple top bar */
.loaf-top{
  padding:16px 0 12px!important;
  margin:0!important;
  border:0!important;
  background:transparent!important;
}
.loaf-top-mark{
  background:transparent!important;
  color:var(--blue-dark)!important;
  padding:0!important;
  border-radius:0!important;
  font-size:17px!important;
  letter-spacing:.06em!important;
}

/* Strong blue hero: no stock image, no stickers, no shapes */
.pw-gingham{
  display:block!important;
  min-height:0!important;
  margin:8px 0 0!important;
  padding:38px 36px 34px!important;
  background:var(--blue)!important;
  border:0!important;
  border-radius:22px 22px 0 0!important;
  box-shadow:none!important;
  overflow:hidden!important;
}
.pw-gingham:after{display:none!important}
.pw-label{
  max-width:720px!important;
  padding:0!important;
  display:block!important;
}
.pw-label:before{display:none!important}
.bakery-name{
  color:white!important;
  font-size:clamp(40px,6vw,62px)!important;
  line-height:.96!important;
  letter-spacing:-.045em!important;
  margin:0 0 12px!important;
  max-width:none!important;
}
.bakery-subtitle{
  color:rgba(255,255,255,.88)!important;
  font-size:14px!important;
  line-height:1.5!important;
  max-width:560px!important;
}

/* Hide the extra intro card so the ordering UI feels integrated */
.assistant-intro{
  background:var(--blue)!important;
  border:0!important;
  border-radius:0 0 22px 22px!important;
  padding:0 36px 22px!important;
  margin:0 0 10px!important;
}
.assistant-intro:before{display:none!important}
.assistant-title{
  color:white!important;
  font-size:0!important;
  margin:0!important;
}
.assistant-title:before{
  content:"What are you craving?";
  color:white!important;
  font-size:20px!important;
  font-weight:700!important;
}
.assistant-copy{
  display:none!important;
}

/* Keep the initial assistant greeting subtle */
.chat-row{margin:9px 0!important}
.chat-name{color:var(--muted)!important}
.chat-bubble{
  box-shadow:none!important;
  border:1px solid rgba(37,35,31,.13)!important;
  border-radius:14px!important;
}
.chat-row.assistant .chat-bubble{background:var(--paper)!important}
.chat-row.user .chat-bubble{background:var(--pink)!important}

/* Main ordering field */
[data-testid="stForm"]{
  margin:10px 0 30px!important;
  padding:5px!important;
  background:var(--paper)!important;
  border:1.5px solid var(--blue)!important;
  border-radius:16px!important;
  box-shadow:none!important;
}
[data-testid="stFormSubmitButton"] button,
[data-testid="stFormSubmitButton"] button:hover{
  background:var(--blue)!important;
  color:white!important;
  border:0!important;
  border-radius:11px!important;
}

/* Clean menu strip */
.pw-section-head{
  margin:8px 0 15px!important;
  padding:0!important;
  border:0!important;
}
.popular-title{
  font-size:29px!important;
  font-weight:800!important;
  text-transform:none!important;
  letter-spacing:-.035em!important;
}
.script-note{
  background:var(--pink)!important;
  color:var(--ink)!important;
  border:0!important;
  border-radius:999px!important;
  padding:4px 9px!important;
  transform:none!important;
}

/* Real product photos do the visual work */
.product-card-shell,.tile-0,.tile-1,.tile-2{
  background:transparent!important;
  border:0!important;
  border-radius:0!important;
  box-shadow:none!important;
  margin-bottom:24px!important;
}
.product-card-media:after{display:none!important}
.product-card-photo,
.tile-1 .product-card-photo,
.tile-2 .product-card-photo{
  display:block!important;
  width:100%!important;
  height:215px!important;
  margin:0!important;
  object-fit:cover!important;
  object-position:center!important;
  border:0!important;
  border-radius:14px!important;
  box-shadow:none!important;
}
.product-card-copy{padding:9px 2px 0!important}
.product-card-name{
  font-size:17px!important;
  font-weight:700!important;
  text-transform:none!important;
  letter-spacing:-.01em!important;
}
.product-card-price{
  font-size:12px!important;
  background:transparent!important;
  border:0!important;
  padding:0!important;
}
.product-card-desc{
  margin-top:4px!important;
  font-size:11px!important;
  line-height:1.45!important;
  color:var(--muted)!important;
}

/* Other controls */
[data-testid="stExpander"] details{
  background:var(--paper)!important;
  border:1px solid rgba(37,35,31,.14)!important;
  border-radius:12px!important;
}
.stButton>button,.stButton>button:hover{
  background:var(--blue)!important;
  color:white!important;
  border:0!important;
  border-radius:10px!important;
}

/* Mobile-first tightening */
@media(max-width:768px){
  .block-container{padding:0 14px 2rem!important}
  .loaf-top{padding:10px 0 9px!important}
  .pw-gingham{
    margin-top:4px!important;
    padding:25px 18px 20px!important;
    border-radius:17px 17px 0 0!important;
  }
  .bakery-name{
    font-size:clamp(32px,10vw,42px)!important;
    margin-bottom:9px!important;
  }
  .bakery-subtitle{
    font-size:12.5px!important;
    max-width:100%!important;
  }
  .assistant-intro{
    padding:0 18px 17px!important;
    border-radius:0 0 17px 17px!important;
  }
  .assistant-title:before{font-size:18px!important}
  [data-testid="stForm"]{margin-bottom:24px!important}
  .popular-title{font-size:24px!important}
  .script-note{font-size:9px!important}
  .product-card-photo,
  .tile-1 .product-card-photo,
  .tile-2 .product-card-photo{
    height:180px!important;
    border-radius:12px!important;
  }
  .product-card-name{font-size:15px!important}
  .product-card-desc{font-size:10.5px!important}
}


/* ===== THEME 2 V8: RETRO BOUTIQUE =====
   Palette: beige + dark green + rosy brown + midnight teal.
   Moss green intentionally excluded.
*/
:root{
  --beige:#F7F4D5;
  --paper:#FFFDF3;
  --dark-green:#0A3323;
  --rose:#D3968C;
  --teal:#105666;
  --ink:#26231F;
  --muted:#6E655D;
}
.stApp{background:var(--beige)!important;color:var(--ink)!important}
.block-container{max-width:940px!important;padding:0 24px 3rem!important}

/* Quiet navigation */
.loaf-top{
  padding:17px 0 13px!important;
  margin:0!important;
  border-bottom:1px solid rgba(10,51,35,.28)!important;
  background:transparent!important;
  color:var(--dark-green)!important;
}
.loaf-top-mark{
  background:transparent!important;
  color:var(--dark-green)!important;
  padding:0!important;
  border-radius:0!important;
  font-size:18px!important;
  letter-spacing:.08em!important;
}

/* Hero: strong editorial colour block */
.pw-gingham{
  display:block!important;
  position:relative!important;
  min-height:0!important;
  margin:20px 0 0!important;
  padding:46px 42px 52px!important;
  background:var(--rose)!important;
  border:0!important;
  border-radius:0!important;
  box-shadow:none!important;
  overflow:hidden!important;
}
.pw-gingham:before{
  content:"";
  position:absolute;
  right:-55px;top:-80px;
  width:250px;height:250px;
  border:34px solid var(--teal);
  border-radius:50%;
  opacity:.95;
}
.pw-gingham:after{
  content:"";
  display:block!important;
  position:absolute!important;
  left:0!important;right:0!important;bottom:-1px!important;
  width:100%!important;height:20px!important;
  background:
    radial-gradient(circle at 10px 0, transparent 10px, var(--beige) 11px) 0 0/20px 20px repeat-x!important;
  border:0!important;border-radius:0!important;transform:none!important;
}
.pw-label{
  position:relative!important;
  z-index:2!important;
  max-width:650px!important;
  padding:0!important;
}
.pw-label:before{
  display:block!important;
  content:"THE BAKERY EDIT"!important;
  width:max-content!important;
  margin:0 0 15px!important;
  padding:5px 9px!important;
  background:var(--beige)!important;
  color:var(--dark-green)!important;
  font-family:"DM Mono",monospace!important;
  font-size:9px!important;
  letter-spacing:.08em!important;
}
.bakery-name{
  color:var(--dark-green)!important;
  font-size:clamp(44px,6.5vw,68px)!important;
  line-height:.94!important;
  letter-spacing:-.045em!important;
  margin:0 0 14px!important;
}
.bakery-subtitle{
  color:#493C38!important;
  max-width:520px!important;
  font-size:15px!important;
  line-height:1.55!important;
}

/* Ordering zone: dark green with beige input */
.assistant-intro{
  background:var(--dark-green)!important;
  border:0!important;
  border-radius:0!important;
  padding:26px 32px 7px!important;
  margin:0!important;
}
.assistant-intro:before{display:none!important}
.assistant-title{
  color:var(--beige)!important;
  font-size:0!important;
  margin:0 0 4px!important;
}
.assistant-title:before{
  content:"What are you craving?";
  color:var(--beige)!important;
  font-size:25px!important;
  font-weight:800!important;
}
.assistant-copy{
  color:rgba(247,244,213,.78)!important;
  font-size:13px!important;
  max-width:600px!important;
}

/* Chat */
.chat-name{color:var(--muted)!important}
.chat-bubble{
  border:1px solid rgba(10,51,35,.16)!important;
  box-shadow:none!important;
  border-radius:0!important;
}
.chat-row.assistant .chat-bubble{background:var(--paper)!important}
.chat-row.user .chat-bubble{
  background:var(--rose)!important;
  color:var(--dark-green)!important;
}

/* Composer connects visually to the dark-green ordering section */
[data-testid="stForm"]{
  margin:0 0 30px!important;
  padding:7px!important;
  background:var(--dark-green)!important;
  border:0!important;
  border-radius:0!important;
  box-shadow:none!important;
}
[data-testid="stForm"] input{
  background:var(--paper)!important;
  border-radius:0!important;
  padding-left:15px!important;
}
[data-testid="stFormSubmitButton"] button,
[data-testid="stFormSubmitButton"] button:hover{
  background:var(--rose)!important;
  color:var(--dark-green)!important;
  border:0!important;
  border-radius:0!important;
}

/* Product section */
.pw-section-head{
  margin:35px 0 17px!important;
  padding:0 0 10px!important;
  border-bottom:2px solid var(--teal)!important;
}
.popular-title{
  color:var(--dark-green)!important;
  font-size:31px!important;
  font-weight:800!important;
  letter-spacing:-.035em!important;
  text-transform:none!important;
}
.script-note{
  background:var(--rose)!important;
  color:var(--dark-green)!important;
  border:0!important;
  border-radius:0!important;
  padding:4px 9px!important;
  transform:none!important;
}

/* Clean real-photo product tiles with editorial coloured captions */
.product-card-shell,.tile-0,.tile-1,.tile-2{
  background:transparent!important;
  border:0!important;
  border-radius:0!important;
  box-shadow:none!important;
  margin-bottom:24px!important;
}
.product-card-media{position:relative!important}
.product-card-media:after{display:none!important}
.product-card-photo,
.tile-1 .product-card-photo,
.tile-2 .product-card-photo{
  width:100%!important;
  height:220px!important;
  margin:0!important;
  object-fit:cover!important;
  object-position:center!important;
  border:0!important;
  border-radius:0!important;
  box-shadow:none!important;
}
.product-card-copy{
  padding:11px 12px 12px!important;
  background:var(--paper)!important;
  border-left:5px solid var(--teal)!important;
}
.tile-1 .product-card-copy{border-left-color:var(--rose)!important}
.tile-2 .product-card-copy{border-left-color:var(--dark-green)!important}
.product-card-name{
  color:var(--dark-green)!important;
  font-size:18px!important;
  font-weight:800!important;
  text-transform:none!important;
}
.product-card-price{
  color:var(--teal)!important;
  font-size:12px!important;
  background:transparent!important;
  border:0!important;
  padding:0!important;
}
.product-card-desc{
  color:var(--muted)!important;
  margin-top:5px!important;
  font-size:11px!important;
}

/* Expanders/buttons */
[data-testid="stExpander"] details{
  background:var(--paper)!important;
  border:1px solid rgba(10,51,35,.22)!important;
  border-radius:0!important;
}
.stButton>button,.stButton>button:hover{
  background:var(--dark-green)!important;
  color:var(--beige)!important;
  border:0!important;
  border-radius:0!important;
}
.loaf-footer{color:var(--muted)!important}

/* Mobile */
@media(max-width:768px){
  .block-container{padding:0 14px 2rem!important}
  .loaf-top{padding:11px 0 10px!important}
  .pw-gingham{
    margin-top:12px!important;
    padding:30px 20px 38px!important;
  }
  .pw-gingham:before{
    width:130px;height:130px;right:-55px;top:-55px;border-width:20px;
  }
  .bakery-name{
    font-size:clamp(34px,10vw,44px)!important;
    margin-bottom:10px!important;
  }
  .bakery-subtitle{font-size:13px!important;max-width:90%!important}
  .assistant-intro{padding:20px 18px 6px!important}
  .assistant-title:before{font-size:21px!important}
  .assistant-copy{font-size:12px!important}
  [data-testid="stForm"]{margin-bottom:24px!important}
  .popular-title{font-size:25px!important}
  .product-card-photo,
  .tile-1 .product-card-photo,
  .tile-2 .product-card-photo{
    height:185px!important;
  }
  .product-card-copy{padding:9px 10px 10px!important}
  .product-card-name{font-size:16px!important}
  .product-card-desc{font-size:10.5px!important}
}


/* ===== THEME 2 V9: BLUE-LED RETRO BOUTIQUE ===== */
:root{
  --beige:#F7F4D5;
  --paper:#FFFDF3;
  --green:#0A3323;
  --rose:#D3968C;
  --blue:#105666;
  --ink:#26231F;
  --muted:#6E655D;
}
.stApp{background:var(--beige)!important}

/* Blue leads; green becomes a tiny supporting accent */
.loaf-top{
  color:var(--blue)!important;
  border-bottom:1px solid rgba(16,86,102,.30)!important;
}
.loaf-top-mark{color:var(--blue)!important}

/* Rosy hero + scallop, without the decorative ring or fake editorial label */
.pw-gingham{
  background:var(--rose)!important;
  padding:36px 40px 43px!important;
}
.pw-gingham:before{display:none!important}
.pw-label:before{display:none!important}
.bakery-name{
  color:var(--blue)!important;
  margin-top:0!important;
}
.bakery-subtitle{color:#493C38!important}

/* Ordering section becomes midnight blue */
.assistant-intro{
  background:var(--blue)!important;
  padding:20px 28px 5px!important;
}
.assistant-title:before{color:var(--beige)!important}
.assistant-copy{color:rgba(247,244,213,.82)!important}

/* Greeting visually connects to the ordering section */
.chat-row.assistant{
  background:var(--blue)!important;
  margin:0!important;
  padding:3px 28px 12px!important;
  box-sizing:border-box!important;
}
.chat-row.assistant .chat-name{
  color:rgba(247,244,213,.72)!important;
}
.chat-row.assistant .chat-bubble{
  background:var(--paper)!important;
  border:0!important;
  width:max-content!important;
}
.chat-row.user .chat-bubble{
  background:var(--rose)!important;
  color:var(--ink)!important;
}

/* Composer stays inside the blue visual zone */
[data-testid="stForm"]{
  background:var(--blue)!important;
  margin:0 0 18px!important;
  padding:7px 28px 18px!important;
}
[data-testid="stForm"] input{
  background:var(--paper)!important;
}
[data-testid="stFormSubmitButton"] button,
[data-testid="stFormSubmitButton"] button:hover{
  background:var(--rose)!important;
  color:var(--blue)!important;
}

/* Pull products closer and make blue the section accent */
.pw-section-head{
  margin:20px 0 13px!important;
  padding-bottom:8px!important;
  border-bottom:2px solid var(--blue)!important;
}
.popular-title{color:var(--blue)!important}
.script-note{
  background:var(--rose)!important;
  color:var(--ink)!important;
}

/* Smaller, faster-to-browse product imagery */
.product-card-photo,
.tile-1 .product-card-photo,
.tile-2 .product-card-photo{
  height:175px!important;
  object-fit:cover!important;
  object-position:center!important;
}
.product-card-copy{
  border-left:4px solid var(--blue)!important;
  padding:9px 10px 10px!important;
}
.tile-1 .product-card-copy{border-left-color:var(--rose)!important}
.tile-2 .product-card-copy{border-left-color:var(--blue)!important}
.product-card-name{color:var(--blue)!important}
.product-card-price{color:var(--blue)!important}

/* Green only as a subtle minor detail */
[data-testid="stExpander"] summary{color:var(--green)!important}

/* Mobile */
@media(max-width:768px){
  .pw-gingham{
    padding:26px 18px 34px!important;
  }
  .bakery-name{
    font-size:clamp(33px,10vw,43px)!important;
  }
  .assistant-intro{
    padding:17px 16px 4px!important;
  }
  .chat-row.assistant{
    padding:3px 16px 10px!important;
  }
  [data-testid="stForm"]{
    padding:6px 16px 14px!important;
    margin-bottom:14px!important;
  }
  .pw-section-head{
    margin-top:16px!important;
  }
  .product-card-photo,
  .tile-1 .product-card-photo,
  .tile-2 .product-card-photo{
    height:145px!important;
  }
  .product-card-copy{
    padding:8px 8px 9px!important;
  }
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

    n_cols = 2
    deco = '<span class="t2-half"></span><span class="t2-squig"></span>'

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
Speak in a warm, polite, and helpful tone, with a bit of natural personality and warmth, like a friendly local shopkeeper, not robotic or overly formal. Never use em dashes in your replies.

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

    # Header
    st.markdown(
        '<div class="loaf-top"><span class="loaf-top-mark">LOAF</span><span>Online ordering</span></div>'
        f'<div class="pw-gingham">{deco}<div class="pw-label">'
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

    # Favourites: two per row
    visible_menu_items = [item for item in menu if item.get("Item")][:6]
    if visible_menu_items:
        st.markdown(
            '<div class="pw-rule"></div>'
            '<div class="pw-section-head"><span class="popular-title">Popular right now</span>'
            '<span class="script-note">fresh picks</span></div>',
            unsafe_allow_html=True
        )
        card_cols = st.columns(n_cols)
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

            with card_cols[idx % n_cols]:
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
            menu_cols = st.columns(n_cols)
            for display_idx, item in enumerate(remaining_menu_items):
                original_idx = display_idx + 6
                item_name = html.escape(str(item.get("Item", "")))
                ingredients = html.escape(str(item.get("Ingredients", "")))
                price_text = fmt_price(item.get("Price", ""))
                photo_url = item.get("PhotoURL") or (
                    menu_photo_urls[original_idx] if original_idx < len(menu_photo_urls) else None
                )
                with menu_cols[display_idx % n_cols]:
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
                for key in ["messages", "display_messages", "current_order", "order_email_sent", "order_number"]:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()

    if len(st.session_state.get("display_messages", [])) >= MAX_MESSAGES_PER_SESSION:
        st.warning(
            f"This chat has reached its message limit for one session. "
            f"Please contact {contact} directly, or start a new order."
        )
        user_input = None

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        st.session_state.display_messages.append({"role": "user", "content": user_input})

        try:
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
            finally:
                thinking_slot.empty()
            bot_reply = response.message.content[0].text
        except Exception:
            st.session_state.messages.pop()
            st.session_state.display_messages.pop()
            st.session_state.display_messages.append({
                "role": "assistant",
                "content": "Sorry, I'm having trouble responding right now. Please try again in a moment, or contact the business directly."
            })
            st.rerun()

        order_match = re.search(r"ORDER_SUMMARY:\s*(\{.*\})", bot_reply, re.DOTALL)
        display_reply = bot_reply
        if order_match:
            display_reply = bot_reply[:order_match.start()].strip()
            try:
                parsed_order = json.loads(order_match.group(1))

                if parsed_order.get("status") == "confirmed" and get_missing_order_fields(parsed_order):
                    parsed_order["status"] = "in_progress"

                # Backstop: verify the advance notice in real Python, not AI arithmetic.
                notice_check = check_advance_notice(parsed_order.get("requested_datetime_iso"), advance_notice)
                notice_warning = None
                if parsed_order.get("status") == "confirmed" and notice_check.get("checked") and not notice_check.get("ok"):
                    parsed_order["status"] = "in_progress"
                    notice_warning = (
                        f"Let me double check that. It's only about {notice_check['actual_hours']:.1f} hours from now, "
                        f"and we need {notice_check['required_hours']:.0f} hours' notice for this. "
                        f"Could you choose a later date or time, or confirm you'd still like to proceed?"
                    )

                st.session_state.current_order = parsed_order

                if parsed_order.get("status") == "confirmed" and not st.session_state.get("order_email_sent", False):
                    if not st.session_state.get("order_number"):
                        st.session_state.order_number = random.randint(1000, 9999)
                    try:
                        send_order_email(parsed_order, business_name, contact, st.session_state.order_number)
                        st.session_state.order_email_sent = True
                    except Exception:
                        pass
                    st.session_state.orders_this_session = st.session_state.get("orders_this_session", 0) + 1
                    display_reply += f"\n\nYour order #{st.session_state.order_number} is confirmed. We'll be in touch shortly."
                elif notice_warning:
                    display_reply += f"\n\n{notice_warning}"
            except json.JSONDecodeError:
                pass

        st.session_state.messages.append({"role": "assistant", "content": bot_reply})
        st.session_state.display_messages.append({"role": "assistant", "content": display_reply})
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


def quick_update_view():
    st.title("Quick Stock Update")
    st.caption("Mark items as sold out for today. Nothing else about your bot changes.")

    slug_input = st.text_input("Web address name", value=slug_from_url, placeholder="e.g. sweettreats")
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

    current_sold_out = [n.strip() for n in (business.get("sold_out_items") or "").split(",") if n.strip()]

    st.write("Check anything that's sold out right now:")
    newly_sold_out = []
    for item in menu_items:
        item_name = item.get("Item", "")
        if not item_name:
            continue
        if st.checkbox(item_name, value=item_name in current_sold_out, key=f"soldout_{item_name}"):
            newly_sold_out.append(item_name)

    if st.button("Update"):
        try:
            supabase.table("businesses").update(
                {"sold_out_items": ", ".join(newly_sold_out)}
            ).eq("slug", clean_slug).execute()
        except Exception:
            st.error("Something went wrong updating this. Please try again in a moment.")
        else:
            st.success("Updated. Your bot now reflects today's availability.")


def owner_view():
    st.title("Loaf")
    st.caption("Set up your bakery's ordering chatbot")

    business_name = st.text_input("Business name")
    slug = st.text_input("Web address name (letters/numbers only, no spaces)", placeholder="e.g. sweettreats")
    password = st.text_input(
        "Password (create one if this is a new bot, or enter your existing password to edit it)",
        type="password"
    )

    menu_df = pd.DataFrame({"Item": [""], "Price": [0], "Ingredients": [""]})
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
    business_hours = st.text_input("Business hours", placeholder="e.g. Tue-Sat 9am-7pm, closed Sun-Mon")
    advance_notice = st.text_input("Advance notice required for custom orders", placeholder="e.g. 48 hours")
    sold_out_items = st.text_input(
        "Out of stock today (comma separated, leave blank if none)",
        placeholder="e.g. Red velvet cake, Croissants"
    )
    menu_photos = st.file_uploader(
        "Product photos (optional, upload in the same order as your menu items)",
        accept_multiple_files=True,
        type=["png", "jpg", "jpeg"],
        help="Photo 1 is linked to menu item 1, photo 2 to menu item 2, and so on."
    )
    social_link = st.text_input("Instagram / website link (optional)", placeholder="e.g. instagram.com/yourbakery")

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
                st.success("Saved. Share this link with your customers:")
                st.code(f"https://bakery-bot.streamlit.app/?slug={clean_slug}")
                st.caption("Bookmark this link to mark items sold out during the day without opening the full form:")
                st.code(f"https://bakery-bot.streamlit.app/?mode=quickupdate&slug={clean_slug}")


if mode == "owner":
    owner_view()
elif mode == "quickupdate":
    quick_update_view()
else:
    customer_view()
