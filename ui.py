"""
ContextIQ — UI layer.
"""

import streamlit as st
import streamlit.components.v1 as components

# ---------- Dark theme:
DARK = {
    "bg": "#161A17",
    "surface": "#1E2420",
    "surface-alt": "#20261F",
    "ink": "#EDEEE8",
    "ink-soft": "#9BA39A",
    "pine": "#4E9C86",
    "pine-dark": "#3B7E6C",
    "gold": "#D9AE55",
    "line": "#323A32",
    "banner-bg": "#1D2B25",
    "banner-line": "#2E463C",
}


def inject_css():
    """Injects dark-mode"""
    t = DARK
    css = f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600;9..144,700&family=Inter:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap');

    :root{{
        --bg:{t['bg']};
        --surface:{t['surface']};
        --surface-alt:{t['surface-alt']};
        --ink:{t['ink']};
        --ink-soft:{t['ink-soft']};
        --pine:{t['pine']};
        --pine-dark:{t['pine-dark']};
        --gold:{t['gold']};
        --line:{t['line']};
        --banner-bg:{t['banner-bg']};
        --banner-line:{t['banner-line']};
    }}

    .stApp,
    div[data-testid="stAppViewContainer"],
    div[data-testid="stAppViewBlockContainer"],
    div[data-testid="stMain"],
    .block-container,
    section.main,
    .main {{
        background: var(--bg) !important;
    }}

    /* ---- Global text color ---- */
    html, body, [class*="css"],
    .stMarkdown, .stMarkdown p, .stMarkdown li, .stMarkdown span,
    .stText, p, span, label, li, h1, h2, h3, h4, h5, h6,
    div[data-testid="stChatInput"] textarea,
    div[data-testid="stSelectbox"] div,
    div[data-testid="stSelectbox"] span,
    div[data-testid="stSelectbox"] svg,
    div[data-testid="stFileUploader"] span,
    div[data-testid="stFileUploader"] button,
    div[data-testid="stFileUploader"] small,
    div[data-testid="stToggle"] label,
    div[data-testid="stExpander"] summary,
    div[data-testid="stExpander"] summary span,
    .stRadio label, .stTextInput input,
    .stSlider label, .stAlert p,
    .stCheckbox label,
    div[data-baseweb="select"] span,
    div[data-baseweb="input"] input {{
        color: var(--ink) !important;
    }}

    /* ---- Font reset ---- */
    html, body, [class*="css"],
    .stMarkdown, .stMarkdown p, .stMarkdown li,
    .stText, p, label, li, h1, h2, h3, h4, h5, h6,
    div[data-testid="stChatInput"] textarea,
    div[data-testid="stSelectbox"] div,
    div[data-testid="stFileUploader"] button,
    div[data-testid="stFileUploader"] small,
    div[data-testid="stToggle"] label,
    div[data-testid="stExpander"] summary,
    .stRadio label, .stTextInput input,
    .stSlider label, .stAlert p,
    .stCheckbox label,
    div[data-baseweb="input"] input {{
        font-family: 'Inter', sans-serif;
    }}

    /* Safeguard for Material Symbols */
    span[data-testid="stIconMaterial"],
    [class*="material-symbols"] {{
        font-family: 'Material Symbols Rounded' !important;
    }}

    /* ---- Hide Streamlit chrome ---- */
    #MainMenu, footer {{
        visibility: hidden;
    }}
    header[data-testid="stHeader"] {{
        background: transparent !important;
    }}
    div[data-testid="stToolbar"] {{
    visibility: visible !important;
    }}
    div[data-testid="stDecoration"] {{
        display: none;
    }}

    /* ---- Sidebar ---- */
    section[data-testid="stSidebar"],
    div[data-testid="stSidebar"] {{
        background: var(--surface-alt) !important;
        border-right: 1px solid var(--line) !important;
    }}
    section[data-testid="stSidebar"] .block-container,
    div[data-testid="stSidebar"] .block-container {{
        padding-top: 1.6rem;
    }}
    section[data-testid="stSidebar"] *,
    div[data-testid="stSidebar"] * {{
        color: var(--ink) !important;
    }}
    section[data-testid="stSidebar"] .side-label,
    div[data-testid="stSidebar"] .side-label {{
        color: var(--ink-soft) !important;
    }}

    /* ---- Brand ---- */
    .brand {{
        display: flex;
        align-items: center;
        gap: .55rem;
        margin-bottom: .15rem;
    }}
    .brand-mark {{
        width: 34px; height: 34px; border-radius: 9px;
        background: linear-gradient(155deg, var(--pine), var(--pine-dark));
        display: flex; align-items: center; justify-content: center;
        color: #F6F5F0 !important; font-family: 'Fraunces', serif; font-weight: 600; font-size: 1.05rem;
        box-shadow: 0 2px 6px rgba(32,66,58,.25);
    }}
    .brand-name {{
        font-family: 'Fraunces', serif; font-weight: 600; font-size: 1.28rem;
        color: var(--ink) !important;
    }}
    .brand-tag {{
        font-size: .72rem; color: var(--ink-soft) !important;
        margin: 0 0 1.3rem 44px; letter-spacing: .4px; text-transform: uppercase;
    }}

    .side-label {{
        font-family: 'IBM Plex Mono', monospace; font-size: .68rem;
        letter-spacing: 1.2px; text-transform: uppercase;
        color: var(--ink-soft) !important; margin: 1.35rem 0 .55rem 2px;
    }}

    /* ---- File pills ---- */
    .file-pill {{
        display: flex; align-items: center; gap: .5rem;
        background: var(--surface); border: 1px solid var(--line); border-radius: 9px;
        padding: .5rem .65rem; margin-bottom: .4rem; font-size: .83rem;
    }}
    .file-pill.active {{
        border-color: var(--pine);
    }}
    .file-pill .dot {{
        width: 7px; height: 7px; border-radius: 50%;
        background: var(--pine); flex-shrink: 0;
    }}
    .file-pill .fname {{
        overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
        color: var(--ink) !important;
    }}

    .empty-hint {{
        font-size: .8rem; color: var(--ink-soft) !important; line-height: 1.5;
        background: var(--surface); border: 1px dashed var(--line); border-radius: 9px;
        padding: .7rem .75rem;
    }}

    /* ---- Sidebar download buttons ---- */
    section[data-testid="stSidebar"] div[data-testid="stDownloadButton"] button,
    div[data-testid="stSidebar"] div[data-testid="stDownloadButton"] button {{
        width: 100%; text-align: left;
        background: var(--surface) !important; border: 1px solid var(--line) !important;
        border-radius: 9px !important; color: var(--ink) !important;
        font-family: 'Inter', sans-serif !important; font-size: .83rem !important;
        padding: .55rem .7rem !important; box-shadow: none !important;
        display: flex; justify-content: flex-start; margin-bottom: .4rem;
    }}
    section[data-testid="stSidebar"] div[data-testid="stDownloadButton"] button:hover,
    div[data-testid="stSidebar"] div[data-testid="stDownloadButton"] button:hover {{
        border-color: var(--pine) !important; color: var(--pine-dark) !important;
    }}

    /* ---- File uploader ---- */
    section[data-testid="stSidebar"] .stFileUploader,
    div[data-testid="stSidebar"] .stFileUploader {{
        margin-bottom: .8rem;
    }}
    div[data-testid="stFileUploader"] section,
    div[data-testid="stFileUploaderDropzone"] {{
        background: var(--surface) !important;
        border: 1.5px dashed var(--pine) !important;
        border-radius: 10px !important;
        padding: 1rem .8rem !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        gap: .6rem !important;
        min-height: auto !important;
    }}
    div[data-testid="stFileUploader"] section > div,
    div[data-testid="stFileUploaderDropzone"] > div {{
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        gap: .5rem !important;
        width: 100% !important;
    }}
    div[data-testid="stFileUploader"] section *,
    div[data-testid="stFileUploaderDropzone"] * {{
        color: var(--ink) !important;
        position: static !important;
    }}
    div[data-testid="stFileUploader"] button,
    div[data-testid="stFileUploaderDropzone"] button,
    div[data-testid="stFileUploader"] [data-testid="stBaseButton-secondary"] {{
        background: var(--surface-alt) !important;
        border: 1px solid var(--line) !important;
        color: var(--pine-dark) !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
        padding: .4rem .8rem !important;
        position: static !important;
        margin-top: .3rem !important;
    }}
    div[data-testid="stFileUploader"] button:hover,
    div[data-testid="stFileUploaderDropzone"] button:hover,
    div[data-testid="stFileUploader"] [data-testid="stBaseButton-secondary"]:hover {{
        border-color: var(--pine) !important;
        color: var(--pine) !important;
        background: var(--banner-bg) !important;
    }}
    section[data-testid="stSidebar"] .stFileUploader small,
    div[data-testid="stSidebar"] .stFileUploader small {{
        display: none !important;
    }}

    /* ---- Sidebar buttons ---- */
    section[data-testid="stSidebar"] .stButton button,
    div[data-testid="stSidebar"] .stButton button {{
        background: var(--surface) !important;
        border: 1px solid var(--line) !important;
        color: var(--ink) !important;
        border-radius: 9px !important;
    }}
    section[data-testid="stSidebar"] .stButton button:hover,
    div[data-testid="stSidebar"] .stButton button:hover {{
        border-color: var(--pine) !important;
        color: var(--pine-dark) !important;
    }}

    /* ---- Sidebar selectbox ---- */
    .stSelectbox div[data-baseweb="select"] {{
        background: var(--surface) !important;
        border-color: var(--line) !important;
    }}
    .stSelectbox div[data-baseweb="select"] span {{
        color: var(--ink) !important;
    }}
    .stSelectbox svg {{
        fill: var(--ink-soft) !important;
        color: var(--ink-soft) !important;
    }}

    /* ---- Main content widgets (force dark backgrounds) ---- */
    .stTextInput input,
    .stTextArea textarea,
    .stSelectbox div[data-baseweb="select"],
    .stSlider [data-baseweb="slider"],
    .stCheckbox div,
    div[data-testid="stExpander"] {{
        background: var(--surface) !important;
        color: var(--ink) !important;
    }}

    /* ---- Chat input (critical fix) ---- */
    div[data-testid="stChatInput"] {{
        background: var(--surface) !important;
        border: 1.5px solid var(--line) !important;
        border-radius: 16px !important;
        box-shadow: 0 4px 16px rgba(0,0,0,.3) !important;
    }}
    div[data-testid="stChatInput"] textarea {{
        background: var(--surface) !important;
        color: var(--ink) !important;
        font-family: 'Inter', sans-serif !important;
        font-size: .95rem !important;
    }}
    div[data-testid="stChatInput"] textarea::placeholder {{
        color: var(--ink-soft) !important;
    }}
    div[data-testid="stChatInput"][aria-disabled="true"] {{
        opacity: 0.5;
        pointer-events: none;
    }}

    /* ---- General buttons ---- */
    .stButton button {{
        border-radius: 10px; color: var(--ink) !important;
        background: var(--surface) !important;
        border: 1px solid var(--line) !important;
    }}
    .stButton button[kind="primary"] {{
        background: var(--pine) !important;
        border: 1px solid var(--pine) !important;
        color: #F6F5F0 !important;
    }}
    .stButton button[kind="primary"]:hover {{
        background: var(--pine-dark) !important;
        border: 1px solid var(--pine-dark) !important;
        color: #F6F5F0 !important;
    }}

    /* - Slider - */
    .stSlider [data-baseweb="slider"] {{
        padding-top: .4rem;
    }}
    .stSlider label {{
        color: var(--ink) !important;
    }}

    /* - Expander - */
    div[data-testid="stExpander"] {{
        border-color: var(--line) !important;
        background: var(--surface) !important;
    }}
    div[data-testid="stExpander"] summary {{
        color: var(--ink) !important;
    }}
    div[data-testid="stExpander"] summary span {{
        color: var(--ink) !important;
    }}
    div[data-testid="stExpander"] div[data-testid="stMarkdownContainer"] {{
        color: var(--ink) !important;
    }}

    /* ---- Divider ---- */
    hr {{
        border-color: var(--line) !important;
    }}

    /* ---- Alerts ---- */
    .stAlert p {{
        color: var(--ink) !important;
    }}

    /* ---------- Remaining styles (greeting, chat bubbles, quiz, about) ---------- */
    .greet-wrap {{
        display: flex; flex-direction: column; align-items: center; justify-content: center;
        text-align: center; padding: 9vh 1rem 2rem 1rem;
    }}
    .greet-title {{
        font-family: 'Fraunces', serif; font-weight: 600; font-size: 2.5rem;
        color: var(--ink) !important; margin-bottom: .35rem; letter-spacing: -.5px;
    }}
    .greet-title .accent {{
        color: var(--pine) !important;
    }}
    .greet-sub {{
        font-size: 1rem; color: var(--ink-soft) !important;
        max-width: 440px; margin-bottom: 1.9rem; line-height: 1.55;
    }}

    div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] button {{
        background: var(--surface); border: 1px solid var(--line); border-radius: 12px;
        color: var(--ink) !important; font-size: .86rem; font-weight: 500;
        padding: .7rem .6rem; width: 100%;
        transition: all .15s ease; box-shadow: 0 1px 2px rgba(32,40,33,.03);
    }}
    div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] button:hover {{
        border-color: var(--pine); color: var(--pine-dark) !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 10px rgba(32,66,58,.1);
    }}

    div[data-testid="stChatMessage"] {{
        background: transparent; padding: .35rem 0; gap: .6rem;
    }}
    div[data-testid="stChatMessageAvatarUser"] {{
        background: var(--pine) !important;
    }}
    div[data-testid="stChatMessageAvatarAssistant"] {{
        background: var(--gold) !important;
    }}

    .bubble-user {{
        background: var(--pine); color: #FBFAF6 !important;
        padding: .7rem 1rem;
        border-radius: 14px 14px 3px 14px; font-size: .94rem; line-height: 1.55;
        max-width: 92%; margin-left: auto;
        box-shadow: 0 1px 3px rgba(32,66,58,.18);
    }}
    .bubble-user * {{
        color: #FBFAF6 !important;
    }}

    .bubble-assistant {{
        position: relative; background: var(--surface);
        border: 1px solid var(--line); border-left: 3px solid var(--pine);
        padding: .75rem 1.05rem;
        border-radius: 3px 14px 14px 14px; font-size: .94rem; line-height: 1.6;
        color: var(--ink) !important;
        box-shadow: 0 1px 3px rgba(32,40,33,.05);
    }}
    .bubble-assistant * {{
        color: var(--ink) !important;
    }}
    .bubble-assistant .cite {{
        display: block; margin-top: .5rem; font-size: .78rem;
        color: var(--ink-soft) !important;
        font-family: 'IBM Plex Mono', monospace;
    }}

    .thinking {{
        display: inline-flex; align-items: center; gap: 5px;
        color: var(--ink-soft) !important; font-size: .88rem; font-style: italic;
    }}
    .thinking .d {{
        width: 5px; height: 5px; border-radius: 50%;
        background: var(--ink-soft);
        animation: pulse 1.1s infinite ease-in-out;
    }}
    .thinking .d:nth-child(2) {{
        animation-delay: .15s;
    }}
    .thinking .d:nth-child(3) {{
        animation-delay: .3s;
    }}
    @keyframes pulse {{
        0%,80%,100% {{ opacity: .25; transform: scale(.85); }}
        40% {{ opacity: 1; transform: scale(1); }}
    }}

    .quiz-card {{
        background: var(--surface); border: 1px solid var(--line);
        border-radius: 4px 14px 14px 14px;
        padding: 0 0 .3rem 0;
        box-shadow: 0 1px 3px rgba(32,40,33,.05);
        overflow: hidden; margin-bottom: .2rem;
    }}
    .quiz-tab {{
        background: var(--pine); color: #F6F5F0 !important;
        font-family: 'IBM Plex Mono', monospace;
        font-size: .68rem; letter-spacing: 1.3px; text-transform: uppercase;
        padding: .4rem 1.05rem;
    }}
    .quiz-title {{
        font-family: 'Fraunces', serif; font-weight: 600; font-size: 1.08rem;
        padding: .75rem 1.05rem .2rem 1.05rem; color: var(--ink) !important;
    }}
    .quiz-q {{
        font-size: .92rem; font-weight: 500;
        padding: .65rem 1.05rem 0 1.05rem; color: var(--ink) !important;
    }}
    .quiz-type {{
        font-family: 'IBM Plex Mono', monospace; font-size: .66rem;
        color: var(--ink-soft) !important; text-transform: uppercase; letter-spacing: .5px;
        padding: 0 1.05rem;
    }}
    div[data-testid="stRadio"] {{
        padding: 0 .7rem 0 1.05rem;
        background: transparent !important;
    }}
    div[data-testid="stRadio"] label {{
        font-size: .88rem !important; color: var(--ink) !important;
    }}
    /* Keep the actual circle indicator visible — do NOT paint its background
       to match the surrounding surface, or it disappears entirely */
    div[data-testid="stRadio"] label > div:first-child {{
        background: transparent !important;
        border-color: var(--ink-soft) !important;
    }}
    div[data-testid="stRadio"] label[data-checked="true"] > div:first-child,
    div[data-testid="stRadio"] input:checked + div {{
        border-color: var(--pine) !important;
        background-color: var(--pine) !important;
    }}
    div[data-testid="stTextInput"] {{
        padding: 0 1.05rem;
    }}
    div[data-testid="stTextInput"] input {{
        color: var(--ink) !important; background: var(--surface) !important;
    }}

    .result-banner {{
        font-family: 'Fraunces', serif; font-size: 1rem; font-weight: 600;
        color: var(--pine-dark) !important;
        background: var(--banner-bg); border: 1px solid var(--banner-line);
        border-radius: 10px; padding: .6rem .9rem; margin-top: .3rem;
    }}
    .explain {{
        font-size: .82rem; color: var(--ink-soft) !important;
        padding: 0 1.05rem .6rem 1.05rem;
    }}

    .about-hero {{
        text-align: center; padding: 2.2rem 1rem 1.6rem 1rem;
    }}
    .about-hero .mark {{
        width: 52px; height: 52px; border-radius: 14px;
        margin: 0 auto .9rem auto;
        background: linear-gradient(155deg, var(--pine), var(--pine-dark));
        display: flex; align-items: center; justify-content: center;
        color: #F6F5F0 !important; font-family: 'Fraunces', serif; font-weight: 600; font-size: 1.5rem;
        box-shadow: 0 3px 10px rgba(32,66,58,.25);
    }}
    .about-hero h1 {{
        font-family: 'Fraunces', serif; font-weight: 600; font-size: 2rem;
        color: var(--ink) !important; margin: 0 0 .5rem 0; letter-spacing: -.5px;
    }}
    .about-hero p {{
        font-size: .98rem; color: var(--ink-soft) !important;
        max-width: 480px; margin: 0 auto; line-height: 1.6;
    }}
    .about-section-title {{
        font-family: 'IBM Plex Mono', monospace; font-size: .72rem;
        letter-spacing: 1.5px; text-transform: uppercase;
        color: var(--pine) !important; margin: 2rem 0 .9rem 0;
        display: flex; align-items: center; gap: .5rem;
    }}
    .about-section-title:before {{
        content: ""; width: 18px; height: 1px; background: var(--pine);
    }}
    .feature-grid {{
        display: grid; grid-template-columns: 1fr 1fr; gap: .8rem; margin-bottom: .5rem;
    }}
    .feature-card {{
        background: var(--surface); border: 1px solid var(--line); border-radius: 12px;
        padding: 1rem 1.1rem; box-shadow: 0 1px 3px rgba(32,40,33,.05);
    }}
    .feature-card .ficon {{
        font-size: 1.3rem; margin-bottom: .4rem;
    }}
    .feature-card h4 {{
        font-family: 'Fraunces', serif; font-weight: 600; font-size: 1rem;
        color: var(--ink) !important; margin: 0 0 .3rem 0;
    }}
    .feature-card p {{
        font-size: .85rem; color: var(--ink-soft) !important; line-height: 1.5; margin: 0;
    }}
    .step-row {{
        display: flex; gap: .9rem; margin-bottom: 1.1rem; align-items: flex-start;
    }}
    .step-num {{
        flex-shrink: 0; width: 28px; height: 28px; border-radius: 50%;
        background: var(--surface-alt); border: 1px solid var(--line);
        display: flex; align-items: center; justify-content: center;
        font-family: 'IBM Plex Mono', monospace; font-size: .8rem; font-weight: 500;
        color: var(--pine-dark) !important;
    }}
    .step-text h4 {{
        font-size: .92rem; font-weight: 600; color: var(--ink) !important;
        margin: 0 0 .15rem 0;
    }}
    .step-text p {{
        font-size: .84rem; color: var(--ink-soft) !important;
        margin: 0; line-height: 1.5;
    }}
    .tech-badges {{
        display: flex; flex-wrap: wrap; gap: .5rem; margin-top: .3rem;
    }}
    .tech-badge {{
        background: var(--surface-alt); border: 1px solid var(--line);
        border-radius: 20px; padding: .35rem .85rem;
        font-size: .78rem; color: var(--ink-soft) !important;
        font-family: 'IBM Plex Mono', monospace;
    }}
    .safety-note {{
        background: var(--banner-bg); border: 1px solid var(--banner-line);
        border-radius: 12px; padding: .9rem 1.1rem;
        font-size: .86rem; color: var(--ink) !important; line-height: 1.55;
        margin-top: .5rem;
    }}

    /* ---- Following code is for Mobile responsiveness ---- */
    @media (max-width: 640px) {{
        .block-container {{
            padding-left: .75rem !important;
            padding-right: .75rem !important;
        }}
        .greet-title {{
            font-size: 1.7rem !important;
        }}
        .greet-sub {{
            font-size: .88rem !important;
            padding: 0 .5rem;
        }}
        div[data-testid="stHorizontalBlock"] {{
            flex-wrap: wrap !important;
        }}
        div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] {{
            min-width: 46% !important;
            flex: 1 1 46% !important;
        }}
        div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] button {{
            font-size: .78rem !important;
            padding: .55rem .4rem !important;
        }}
        .bubble-user, .bubble-assistant {{
            max-width: 96% !important;
            font-size: .88rem !important;
        }}
        .feature-grid {{
            grid-template-columns: 1fr !important;
        }}
        .quiz-card {{
            font-size: .88rem !important;
        }}
        div[data-testid="stChatInput"] textarea {{
            font-size: 16px !important;
        }}
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


#--->UI rendering function:

def render_brand():
    st.markdown(
        """
        <div class="brand">
            <div class="brand-mark">IQ</div>
            <div class="brand-name">ContextIQ</div>
        </div>
        <div class="brand-tag">Study assistant</div>
        """,
        unsafe_allow_html=True,
    )


def render_file_pill(name: str, active: bool = False):
    cls = "file-pill active" if active else "file-pill"
    st.markdown(
        f'<div class="{cls}"><span class="dot"></span><span class="fname">{name}</span></div>',
        unsafe_allow_html=True,
    )


def render_empty_hint(text: str):
    st.markdown(f'<div class="empty-hint">{text}</div>', unsafe_allow_html=True)


def time_greeting() -> str:
    from datetime import datetime
    hour = datetime.now().hour
    if hour < 12:
        return "Good morning"
    if hour < 18:
        return "Good afternoon"
    return "Good evening"


def render_greeting(name: str = "there"):
    st.markdown(
        f"""
        <div class="greet-wrap">
            <div class="greet-title">{time_greeting()}, <span class="accent">{name}</span>.</div>
            <div class="greet-sub">Upload a textbook and I'll help you understand it — ask questions,
            get clear definitions, take a quiz, or generate a printable practice test.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_quick_chips() -> str | None:
    c1, c2, c3, c4 = st.columns(4)
    clicked = None
    with c1:
        if st.button("💬  Ask a question", use_container_width=True):
            clicked = "__mode_qa__"
    with c2:
        if st.button("📖  Get a definition", use_container_width=True):
            clicked = "__mode_definitions__"
    with c3:
        if st.button("📝  Take a quiz", use_container_width=True):
            clicked = "__mode_quiz__"
    with c4:
        if st.button("📄  Practice test", use_container_width=True):
            clicked = "__mode_pdf_test__"
    return clicked


def render_user_bubble(text: str):
    with st.chat_message("user", avatar="icons\user.png"):
        st.markdown(f'<div class="bubble-user">{text}</div>', unsafe_allow_html=True)


def render_assistant_bubble(text: str, citation: str | None = None):
    with st.chat_message("assistant", avatar="icons\AI.png"):
        html = f'<div class="bubble-assistant">{text}'
        if citation:
            html += f'<span class="cite">{citation}</span>'
        html += "</div>"
        st.markdown(html, unsafe_allow_html=True)


def render_thinking_start():
    with st.chat_message("assistant", avatar="icons\AI.png"):
        placeholder = st.empty()
        placeholder.markdown(
            '<div class="bubble-assistant"><span class="thinking">'
            'Thinking<span class="d"></span><span class="d"></span><span class="d"></span>'
            '</span></div>',
            unsafe_allow_html=True,
        )
        return placeholder


def render_assistant_stream_into_placeholder(placeholder, generator):
    shown = ""
    for chunk in generator:
        shown += chunk
        placeholder.markdown(f'<div class="bubble-assistant">{shown}▌</div>', unsafe_allow_html=True)
    placeholder.markdown(f'<div class="bubble-assistant">{shown.strip()}</div>', unsafe_allow_html=True)
    return shown.strip()


def render_assistant_stream(generator):
    placeholder = render_thinking_start()
    full_text = render_assistant_stream_into_placeholder(placeholder, generator)
    return full_text, placeholder


def render_sources(sources: list[dict]):
    if not sources:
        return
    with st.expander(f"📎 View source passages ({len(sources)})"):
        for s in sources:
            st.markdown(
                f"**Page {s['page']}** · relevance {s['score']:.2f}\n\n> {s.get('text', '')}"
            )
            st.markdown("---")


def render_quiz_card(questions: list[dict], qid: str, submitted: bool, results: dict | None = None):
    """
    IMPORTANT: caller must wrap this in `with st.form(key=f"form_{qid}"):`
    and use `st.form_submit_button(...)` for the submit action — this batches
    all answer selections into ONE rerun instead of one rerun per radio click,
    which is what was causing the blinking while taking a quiz.
    """
    st.markdown(
        f'<div class="quiz-card"><div class="quiz-tab">Quiz · {len(questions)} questions</div>'
        f'<div class="quiz-title">Quick check</div></div>',
        unsafe_allow_html=True,
    )

    answers = {}
    for i, q in enumerate(questions):
        qtype = q.get("type", "multiple_choice")
        st.markdown(f'<div class="quiz-q">{i + 1}. {q["question"]}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="quiz-type">{qtype.replace("_", " ")}</div>', unsafe_allow_html=True)

        key = f"{qid}_{i}"

        if qtype in ("multiple_choice", "true_false") and q.get("options"):
            answers[i] = st.radio(
                key, options=q["options"], key=key, label_visibility="collapsed",
                index=None, disabled=submitted,
            )
        elif qtype == "long_answer":
            answers[i] = st.text_area(
                key, key=key, label_visibility="collapsed",
                placeholder="Write your answer...", disabled=submitted, height=120,
            )
        else:
            answers[i] = st.text_input(
                key, key=key, label_visibility="collapsed",
                placeholder="Type your answer...", disabled=submitted,
            )

        if submitted and results:
            r = results.get(i)
            if r:
                st.markdown(
                    f'<div class="explain"><b>Correct answer:</b> {q.get("correct_answer", "")}<br>'
                    f'<b>Explanation:</b> {q.get("explanation", "")}</div>',
                    unsafe_allow_html=True,
                )

    return answers


def render_result_banner(text: str):
    st.markdown(f'<div class="result-banner">{text}</div>', unsafe_allow_html=True)


def render_quiz_history(history: list[dict]):
    if not history:
        render_empty_hint("Your quiz scores will show up here after you take one.")
        return
    for i, h in enumerate(reversed(history[-10:]), start=1):
        attempt_num = len(history) - i + 1
        st.markdown(
            f'<div class="file-pill"><span class="dot"></span>'
            f'<span class="fname">Attempt {attempt_num}: {h["score"]}/{h["total"]}</span></div>',
            unsafe_allow_html=True,
        )


def render_about():
    st.markdown(
        """
        <div class="about-hero">
            <div class="mark">Iq</div>
            <h1>About ContextIQ</h1>
            <p>ContextIQ turns any textbook PDF into an interactive study partner —
            grounded answers, quizzes, definitions, and printable practice tests,
            all pulled directly from your own material.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="about-section-title">What it does</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="feature-grid">
            <div class="feature-card">
                <div class="ficon">💬</div>
                <h4>Ask Questions</h4>
                <p>Get grounded, cited answers pulled directly from your uploaded textbook — no outside guessing.</p>
            </div>
            <div class="feature-card">
                <div class="ficon">📝</div>
                <h4>Quiz Me</h4>
                <p>Interactive quizzes with mixed question types, generated from any page range you choose.</p>
            </div>
            <div class="feature-card">
                <div class="ficon">📖</div>
                <h4>Definitions<h4>
                <p>Pull key terms and concise, in-your-own-words definitions from a chapter or a topic.</p>
            </div>
            <div class="feature-card">
                <div class="ficon">🗂️</div>
                <h4>Flashcards</h4>
                <p>Flip-card review of key facts, numbers, and concepts- not just formal definitions- by chapteror topic. </p>
            </div>
            <div class="feature-card">
                <div class="ficon">📄</div>
                <h4>PDF Test</h4>
                <p> Generate a printable test paper plus a separate answer key, ready to download.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="about-section-title">How it works</div>', unsafe_allow_html=True)
    steps = [
        ("1", "Upload", "Your PDF is parsed page by page and split into overlapping chunks."),
        ("2", "Embed & Index", "Each chunk is embedded with Gemini and stored in a Qdrant vector database."),
        ("3", "Retrieve", "When you ask something, ContextIQ finds the most relevant chunks — by meaning or by page range."),
        ("4", "Generate, safely", "An LLM answers using only that retrieved content, with input/output safety checks around every response."),
    ]
    for num, title, desc in steps:
        st.markdown(
            f"""
            <div class="step-row">
                <div class="step-num">{num}</div>
                <div class="step-text"><h4>{title}</h4><p>{desc}</p></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown('<div class="about-section-title">Built with</div>', unsafe_allow_html=True)
    badges = ["Streamlit", "Gemini Embeddings", "Qdrant", "Groq · Llama 3.3", "NeMo Guardrails", "ReportLab"]
    badges_html = "".join(f'<span class="tech-badge">{b}</span>' for b in badges)
    st.markdown(f'<div class="tech-badges">{badges_html}</div>', unsafe_allow_html=True)

    st.markdown(
        """
        <div class="safety-note">
            <b>A note on safety:</b> every question and every generated answer passes through
            a guardrails layer that blocks jailbreak attempts and off-topic or unsafe requests,
            and answers are grounded only in the content you've uploaded.
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_auto_scroll():
    """Scrolls the main content area to the bottom after new content appears."""
    components.html(
        """
        <script>
            setTimeout(function() {
                // Find the main scrollable container
                const container = window.parent.document.querySelector('[data-testid="stAppViewBlockContainer"]');
                if (container) {
                    container.scrollTop = container.scrollHeight;
                } else {
                    // Fallback: scroll the whole window
                    window.parent.scrollTo(0, document.body.scrollHeight);
                }
            }, 100);
        </script>
        """,
        height=0,
    )