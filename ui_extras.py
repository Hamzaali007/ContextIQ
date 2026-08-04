import streamlit as st

def inject_flashcard_css():
    """Call once alongside inject_css()- adds styling for the flashcard deck 
     and follow-up question chips without touching the existing CSS block. """
    css = """
    <style>
    .flashcard {
        background: var(--surface);
        border: 1px solid var(--line);
        border-left: 3px solid var(--gold);
        border-radius: 4px 14px 14px 14px;
        padding: 1.4rem 1.3rem;
        min-height: 140px;
        display: flex;
        align-items: center;
        justify-content: center;
        text-align: center;
        margin-bottom: .6rem;
        box-shadow: 0 1px 3px rgba(0,0,0,.2);
    }
    .flashcard-label {
        font-family: 'IBM Plex Mono', monospace;
        font-size: .68rem;
        letter-spacing: 1.2px;
        text-transform: uppercase;
        color: var(--ink-soft) !important;
        margin-bottom: .5rem;
        display: block;
    }
    .flashcard-content {
        font-size: 1.02rem;
        color: var(--ink) !important;
        line-height: 1.5;
    }
    .flashcard-progress {
        font-family: 'IBM Plex Mono', monospace;
        font-size: .75rem;
        color: var(--ink-soft) !important;
        text-align: center;
        margin-bottom: .5rem;
    }
    .flashcard-page {
        font-size: .72rem;
        color: var(--ink-soft) !important;
        margin-top: .5rem;
    }
 
    .followup-chip button {
        background: var(--surface-alt) !important;
        border: 1px solid var(--line) !important;
        color: var(--pine) !important;
        font-size: .8rem !important;
        border-radius: 20px !important;
        padding: .35rem .9rem !important;
    }
    .followup-chip button:hover {
        border-color: var(--pine) !important;
        background: var(--banner-bg) !important;
    }
    </style>
    """
    st.markdown(css,unsafe_allow_html=True)



def render_flashcard_deck(cards:list[dict],msg:dict):
    if "card_index" not in msg:
        msg["card_index"] = 0

    if "revealed" not in msg:
        msg["revealed"] = False

    total = len(cards)
    idx = msg["card_index"]
    card = cards[idx]
    st.markdown(f'<div class="flashcard-progress">Card {idx+1} of {total}</div>',unsafe_allow_html=True)

    label = "ANSWER" if msg["revealed"] else "QUESTION"
    content = card["back"] if msg["revealed"] else card["front"]
    page_note = f'<div class="flashcard-page">Page {card["page"]}</div>' if msg["revealed"] and card.get("page") else ""

    st.markdown(
        f'<div class="flashcard"><div><span class="flashcard-label">{label}</span>'
        f'<div class="flashcard-content">{content}</div> {page_note}</div></div>',
        unsafe_allow_html=True,
    )
    c1,c2,c3 = st.columns([1,1,1])
    with c1:
        if st.button("← Prev", key=f"{msg['id']}_prev", disabled=(idx == 0), use_container_width=True):
            msg["card_index"] -= 1
            msg["revealed"] = False
            st.rerun()

    with c2:
        flip_label = "Show Question" if msg["revealed"] else "Flip/Show Answer"
        if st.button(flip_label, key=f"{msg['id']}_flip", use_container_width=True, type="primary"):
            msg["revealed"] = not msg["revealed"]
            st.rerun()

    with c3:
        if st.button("Next →", key=f"{msg['id']}_next", disabled=(idx == total - 1), use_container_width=True):
            msg["card_index"] += 1
            msg["revealed"] = False
            st.rerun()



def render_follow_up_chips(follow_ups:list[str],msg_id:str) -> str |None:

    if not follow_ups:
        return None
    clicked = None
    st.markdown('<div style="margin-top:.4rem;">', unsafe_allow_html=True)
    cols =st.columns(len(follow_ups))
    for i,(col,q) in enumerate (zip(cols,follow_ups)):
        with col:
            st.markdown('<div class="followup-chip">', unsafe_allow_html=True)
            if st.button(q, key=f"followup_{msg_id}_{i}", use_container_width=True):
                clicked = q
            st.markdown('</div>',unsafe_allow_html=True)

    st.markdown('</div>',unsafe_allow_html=True)

    return clicked


