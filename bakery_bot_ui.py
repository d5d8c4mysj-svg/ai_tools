LOAF_CSS = """
<style>
/* Loaf theme overrides. Loaded after the original style block, so these win. */
:root {
    --periwinkle:#A9B4DA;
    --cream:#FFF4EA;
    --paper:#FFFAF5;
    --olive:#B0B53F;
    --pink:#E5A3B8;
    --pink-soft:#F3CFDA;
    --red:#A52A2D;
    --ink:#2E1E1E;
    --muted:#6B5754;
    --line:#2E1E1E;
}

/* No hover animation, no transitions anywhere */
*, *::before, *::after { transition:none !important; }

/* Removed: sparkle icons */
.stApp::before, .stApp::after, .pw-spark { display:none !important; }

/* Square corners everywhere. The scalloped sheet edge stays. */
.block-container, .pw-strip, .pw-label, .assistant-intro, .chat-bubble,
.product-card-shell, .product-card-photo, .product-card-photo.placeholder,
.script-note, .stButton > button, [data-testid="stExpander"] details,
[data-testid="stExpander"] img, [data-testid="stForm"],
[data-testid="stFormSubmitButton"] button, .stImage img { border-radius:0 !important; }

/* Flat gingham in a stronger pink */
.pw-gingham, .product-card-photo.placeholder {
    background-color:var(--pink-soft) !important;
    background-image:
        linear-gradient(rgba(229,163,184,.9) 50%, transparent 50%),
        linear-gradient(90deg, rgba(229,163,184,.9) 50%, transparent 50%) !important;
}

/* Header label: flat, hard border, no shadow */
.pw-label { border:2px solid var(--ink); box-shadow:none; }
.pw-strip { border-radius:0 !important; }
.pw-rule i { background:var(--ink); height:1.5px; }

/* Removed: coloured left stripe on the assistant card */
.assistant-intro {
    border:2px solid var(--ink) !important;
    border-left:2px solid var(--ink) !important;
    background:var(--paper);
}

/* Chat: square, outlined, one colour per speaker */
.chat-row.assistant .chat-bubble { background:var(--pink-soft); border:1.5px solid var(--ink); }
.chat-row.user .chat-bubble { background:var(--red); border:1.5px solid var(--ink); color:var(--cream); }

/* Composer: a rectangle, not a pill */
[data-testid="stForm"] { border:2px solid var(--ink) !important; background:#fff !important; padding:6px !important; }
[data-testid="stForm"]:focus-within { box-shadow:none; outline:2px solid var(--red); }
[data-testid="stFormSubmitButton"] button { background:var(--red) !important; border:0 !important; }
[data-testid="stFormSubmitButton"] button:hover { background:var(--red) !important; }

/* Product cards: flat, outlined, with a folder tab (from the reference) */
.product-card-shell {
    position:relative;
    overflow:visible;
    margin-top:16px;
    background:var(--paper);
    border:2px solid var(--ink);
    box-shadow:none;
}
.product-card-shell::before {
    content:"";
    position:absolute;
    top:-16px;
    left:14px;
    width:70px;
    height:14px;
    background:var(--olive);
    border:2px solid var(--ink);
    border-bottom:0;
}
.product-card-media { padding:8px; }
.product-card-photo { border:1.5px solid var(--ink); }

/* Small tag */
.script-note { background:var(--olive); border:1.5px solid var(--ink); }

/* Buttons and expanders: flat, no hover change */
.stButton > button { background:var(--red); border:2px solid var(--ink); color:var(--cream); }
.stButton > button:hover { background:var(--red); border-color:var(--ink); color:var(--cream); }
[data-testid="stExpander"] details { background:var(--paper) !important; border:2px solid var(--ink) !important; }
[data-testid="stExpander"] summary:hover { background:transparent !important; }

/* Mobile */
@media (max-width:768px) {
    .product-card-shell::before { width:54px; }
}
</style>
"""
