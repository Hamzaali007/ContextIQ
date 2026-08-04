import os
import tempfile
import streamlit as st
from vectorstore import search_by_page_range
from config import settings  
from ingestion import extract_pdf, chunk_pages
from vectorstore import upsert_chunks, list_sources as _list_sources_raw, delete_source
from guardrails import (
    guarded_answer_stream,
    guarded_quiz,
    guarded_definitions_by_range,
    guarded_definitions_by_topic,
    guarded_flashcards_by_range,
    guarded_flashcards_by_topic
)
from reports import generate_test_and_key
from llm.qa import generate_follow_up_questions
import ui
from ui_extras import inject_flashcard_css, render_flashcard_deck,render_follow_up_chips

st.set_page_config(page_title="ContextIQ", page_icon="icons\\AI.png", layout="wide", initial_sidebar_state="expanded")


@st.cache_data(ttl=30, show_spinner=False)
def list_sources():
    """
    Cached wrapper around the real Qdrant list_sources() call.
    Without this, every single button click (any rerun) triggers a fresh
    Qdrant network round-trip — this was the main cause of multi-second
    delays on every interaction. Call list_sources.clear() right after any
    upload/delete so the change shows up immediately instead of waiting for TTL.
    """
    return _list_sources_raw()

@st.cache_data(ttl=300, show_spinner=False)
def get_page_count(source: str) -> int:
    """Determine a book's real page count from what's stored in Qdrant —
    used when a book was selected from the sidebar rather than just
    uploaded, since total_pages session state only gets set during upload."""
    chunks = search_by_page_range(source=source, start_page=1, end_page=100000)
    if not chunks:
        return 50
    return max(c["page"] for c in chunks if c.get("page"))


ui.inject_css()
inject_flashcard_css()


if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_source" not in st.session_state:
    st.session_state.current_source = None
if "total_pages" not in st.session_state:
    st.session_state.total_pages = {}
if "tests" not in st.session_state:
    st.session_state.tests = []
if "quiz_counter" not in st.session_state:
    st.session_state.quiz_counter = 0
if "flashcard_counter" not in st.session_state:
    st.session_state.flashcard_counter = 0
if "mode" not in st.session_state:
    st.session_state.mode = "qa"
if "show_about" not in st.session_state:
    st.session_state.show_about = False
if "quiz_history" not in st.session_state:
    st.session_state.quiz_history = []
if "is_processing" not in st.session_state:
    st.session_state.is_processing = False

# ---- Sidebar :
with st.sidebar:
    ui.render_brand()

    if st.button("ℹ️ About / How it works", use_container_width=True):
        st.session_state.show_about = not st.session_state.show_about
        st.rerun()

    st.markdown('<div class="side-label">Your textbook</div>', unsafe_allow_html=True)
    st.caption("💡 To try this out, use a small PDF — longer PDFs take more time to embed.")
    uploaded = st.file_uploader("Upload a PDF", type=["pdf"], label_visibility="collapsed", key="uploader")

    if uploaded is not None:
        already_ingested = uploaded.name in list_sources()
        if not already_ingested:
            progress = st.progress(0, text="Extracting text...")
            large_doc_notice = st.empty()
            try:
                temp_path = os.path.join(tempfile.gettempdir(), uploaded.name)
                with open(temp_path, "wb") as f:
                    f.write(uploaded.getbuffer())

                pages = extract_pdf(temp_path)
                progress.progress(15, text=f"Extracted {len(pages)} pages. Splitting into chunks...")

                chunks = chunk_pages(pages)
                progress.progress(30, text=f"Created {len(chunks)} chunks.")

                # LARGE_DOC_CHUNK_THRESHOLD: above this, warn the user up front
                # so they don't think the app has frozen during embedding.
                LARGE_DOC_CHUNK_THRESHOLD = 50
                if len(chunks) > LARGE_DOC_CHUNK_THRESHOLD:
                    large_doc_notice.warning(
                        "📚 This is a large document (**%d chunks**). "
                        "Large documents may take 1-3 minutes to process depending on the "
                        "number of pages and chunks — feel free to keep this tab open."
                        % len(chunks)
                    )

                def _on_embed_progress(done, total, status):
                    pct = 30 + int((done / total) * 60) if total else 30
                    if status:
                        progress.progress(pct, text=status)
                    else:
                        progress.progress(pct, text=f"Generating embeddings... ({done}/{total} chunks)")

                upsert_chunks(chunks, source=uploaded.name, on_progress=_on_embed_progress)
                progress.progress(95, text="Storing vectors in Qdrant...")
                progress.progress(100, text="Document ready!")

                st.session_state.total_pages[uploaded.name] = len(pages)
                st.session_state.current_source = uploaded.name
                os.remove(temp_path)
                list_sources.clear()
            except Exception as e:
                progress.empty()
                large_doc_notice.empty()
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                    st.error(
                        "Embedding service is busy and retries were exhausted. "
                        "Please wait a minute and try uploading again."
                    )
                else:
                    st.error(f"Couldn't process this PDF: {e}")
                st.stop()
            st.rerun()
        else:
            st.session_state.current_source = uploaded.name

    sample_path = "assets/sample_textbook.pdf"
    if "sample_textbook.pdf" not in list_sources() and os.path.exists(sample_path):
        if st.button("✨ Try a sample textbook", use_container_width=True):
            progress = st.progress(0, text="Extracting text...")
            try:
                pages = extract_pdf(sample_path)
                progress.progress(15, text="Splitting document into chunks...")
                chunks = chunk_pages(pages)
                progress.progress(30, text=f"Created {len(chunks)} chunks.")

                def _on_embed_progress(done, total, status):
                    pct = 30 + int((done / total) * 60) if total else 30
                    if status:
                        progress.progress(pct, text=status)
                    else:
                        progress.progress(pct, text=f"Generating embeddings... ({done}/{total} chunks)")

                upsert_chunks(chunks, source="sample_textbook.pdf", on_progress=_on_embed_progress)
                progress.progress(95, text="Storing vectors in Qdrant...")
                progress.progress(100, text="Document ready!")
                st.session_state.total_pages["sample_textbook.pdf"] = len(pages)
                st.session_state.current_source = "sample_textbook.pdf"
                list_sources.clear()
            except Exception as e:
                progress.empty()
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                    st.error("Embedding service is busy and retries were exhausted. Please try again shortly.")
                else:
                    st.error(f"Couldn't load the sample textbook: {e}")
                st.stop()
            st.rerun()

    sources = list_sources()
    if sources:
        for f in sources:
            ui.render_file_pill(f, active=(f == st.session_state.current_source))

        if st.session_state.current_source not in sources:
            st.session_state.current_source = sources[-1]

        selected = st.selectbox("Switch textbook", sources,
                                 index=sources.index(st.session_state.current_source),
                                 label_visibility="collapsed")
        if selected != st.session_state.current_source:
            st.session_state.current_source = selected
            st.rerun()

        if st.button("🗑 Remove this textbook", use_container_width=True):
            delete_source(st.session_state.current_source)
            st.session_state.current_source = None
            list_sources.clear()
            st.rerun()
    else:
        ui.render_empty_hint(
            "No textbook yet — upload a PDF to start asking questions, building quizzes, "
            "and generating tests from it."
        )

    st.markdown('<div class="side-label">Practice tests</div>', unsafe_allow_html=True)
    if st.session_state.tests:
        for t in st.session_state.tests:
            with open(t["test_pdf"], "rb") as f:
                st.download_button(
                    label=f"📄 {t['name']} (test)",
                    data=f.read(),
                    file_name=os.path.basename(t["test_pdf"]),
                    mime="application/pdf",
                    key=f"dl_test_{t['name']}",
                    use_container_width=True,
                )
            with open(t["answer_key_pdf"], "rb") as f:
                st.download_button(
                    label=f"🔑 {t['name']} (answer key)",
                    data=f.read(),
                    file_name=os.path.basename(t["answer_key_pdf"]),
                    mime="application/pdf",
                    key=f"dl_key_{t['name']}",
                    use_container_width=True,
                )
    else:
        ui.render_empty_hint('Ask ContextIQ to "make a practice test" and it will appear here as a downloadable PDF.')

    st.markdown('<div class="side-label">Quiz history</div>', unsafe_allow_html=True)
    ui.render_quiz_history(st.session_state.quiz_history)

    st.markdown("<div style='height:1.2rem'></div>", unsafe_allow_html=True)
    if st.session_state.messages:
        if st.button("＋ New chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()


#Helperr function
def detect_intent(text: str, fallback: str) -> str:
    lowered = text.lower()
    if any(w in lowered for w in ["pdf", "download", "printable test", "practice test"]):
        return "pdf_test"
    if any(w in lowered for w in [
        "quiz me", "test me", "quiz on", "take a quiz",
        "quiz about", "quiz from", "give me a quiz", "make a quiz",
        "create a quiz", "start a quiz", "quiz this", "quiz chapter",
        "ask me questions", "test my knowledge", "check my understanding",
        "give me questions", "make me a quiz", "generate a quiz",
        "can you quiz", "want a quiz", "do a quiz", "run a quiz",
    ]):
        return "quiz"
    if any(w in lowered for w in ["define", "definition", "key terms", "glossary"]):
        return "definitions"
    if any(w in lowered for w in ["flashcard","flash card","flashcards","flash cards"]):
        return "flashcards"
    return fallback


def build_chat_history() -> list[dict]:
    history = []
    pending_q = None
    for msg in st.session_state.messages:
        if msg["type"] != "text":
            continue
        if msg["role"] == "user":
            pending_q = msg["content"]
        elif msg["role"] == "assistant" and pending_q:
            history.append({"question": pending_q, "answer": msg["content"]})
            pending_q = None
    return history[-3:]


def handle_qa_stream(prompt: str, source: str, placeholder=None):
    try:
        chat_history = build_chat_history()
        sources, generator, post_check = guarded_answer_stream(prompt, source, chat_history=chat_history)
        if placeholder is None:
            full_text, placeholder = ui.render_assistant_stream(generator)
        else:
            full_text = ui.render_assistant_stream_into_placeholder(placeholder, generator)

        if post_check:
            check_result = post_check()
            if not check_result["allowed"]:
                full_text = check_result["message"]
                placeholder.markdown(f'<div class="bubble-assistant">{full_text}</div>', unsafe_allow_html=True)
                sources = []

        citation = None
        if sources:
            pages = ", ".join(str(s["page"]) for s in sources[:3])
            citation = f"Source: page(s) {pages}"
            placeholder.markdown(
                f'<div class="bubble-assistant">{full_text}'
                f'<span class="cite">{citation}</span></div>',
                unsafe_allow_html=True,
            )

        if sources:
            ui.render_sources(sources)

        follow_ups = generate_follow_up_questions(prompt,full_text) if sources else []

        st.session_state.messages.append(
            {"role":"assistant","type":"text","content":full_text,"citation":citation,"sources":sources,"follow_ups":follow_ups}
        )
    except Exception as e:
        if placeholder:
            placeholder.markdown(
                '<div class="bubble-assistant">Sorry, I ran into an error answering that. Please try again.</div>',
                unsafe_allow_html=True,
            )
        else:
            st.error(f"Something went wrong generating that answer: {e}")
        st.session_state.messages.append(
            {"role": "assistant", "type": "text", "content": "Sorry, I ran into an error answering that. Please try again."}
        )


def handle_quiz(source: str, start: int, end: int, num_questions: int = 6):
    try:
        # Quiz Me mode is auto-graded, so it's restricted to multiple-choice and
        # true/false only — no short/long answer questions mixed in.But for generation of pdf test user can choose any option or all options
        quiz_data = guarded_quiz(source, start, end, num_questions=num_questions, question_types=["multiple_choice", "true_false"])
        if "error" in quiz_data:
            st.session_state.messages.append({"role": "assistant", "type": "text", "content": quiz_data["error"]})
            return
        st.session_state.quiz_counter += 1
        qid = f"quiz_{st.session_state.quiz_counter}"
        st.session_state.messages.append(
            {"role": "assistant", "type": "quiz", "id": qid, "questions": quiz_data["questions"], "submitted": False}
        )
    except Exception as e:
        st.session_state.messages.append(
            {"role": "assistant", "type": "text", "content": f"Couldn't generate a quiz right now: {e}"}
        )


def handle_definitions(prompt: str, source: str, start: int | None, end: int | None, use_range: bool):
    try:
        if use_range and start and end:
            result = guarded_definitions_by_range(source, start, end)
        else:
            result = guarded_definitions_by_topic(source, prompt)

        if "error" in result:
            text = result["error"]
        else:
            lines = [f"**{d['term']}** (p.{d['page']}) — {d['definition']}" for d in result["definitions"]]
            text = "\n\n".join(lines)
        st.session_state.messages.append({"role": "assistant", "type": "text", "content": text})
    except Exception as e:
        st.session_state.messages.append(
            {"role": "assistant", "type": "text", "content": f"Couldn't extract definitions right now: {e}"}
        )

def handle_flashcards(prompt:str,source:str,start:int | None , end:int |None , use_range:bool,topic:str | None, num_cards:int |None):
    try:
        if use_range and start and end :
            result = guarded_flashcards_by_range(source,start,end,num_cards=num_cards)
        else:
            result = guarded_flashcards_by_topic(source, topic or prompt,num_cards=num_cards)

        if "error" in result:
            st.session_state.messages.append({"role":"assistant","type":"text","content":result["error"]})
            return

        st.session_state.flashcard_counter +=1
        fid = f"flashcards_{st.session_state.flashcard_counter}"
        st.session_state.messages.append(
            {"role":"assistant","type":"flashcards","id":fid,"cards":result["flashcards"]}

        )
    except Exception as e:
        st.session_state.messages.append(
            {"role":"assistant","type":"text","content":f"Couldn't generate flashcards right now: {e}"}
        )



def handle_pdf_test(
    source: str,
    start: int,
    end: int,
    num_questions: int = 8,
    test_title: str | None = None,
    question_types: list[str] | None = None,
    difficulty: str | None = None,
):
    try:
        quiz_data = guarded_quiz(
            source, start, end,
            num_questions=num_questions,
            question_types=question_types,
            difficulty=difficulty,
        )
        if "error" in quiz_data:
            st.session_state.messages.append({"role": "assistant", "type": "text", "content": quiz_data["error"]})
            return

        files = generate_test_and_key(quiz_data, source_name=source, custom_title=test_title)
        test_name = test_title.strip() if test_title and test_title.strip() else f"{os.path.splitext(source)[0]} (p.{start}-{end})"
        st.session_state.tests.append({"name": test_name, "test_pdf": files["test_pdf"], "answer_key_pdf": files["answer_key_pdf"]})
        st.session_state.messages.append(
            {
                "role": "assistant",
                "type": "text",
                "content": f"I've put together **{test_name}** and added it to *Practice tests* in the sidebar — download it there.",
            }
        )
    except Exception as e:
        st.session_state.messages.append(
            {"role": "assistant", "type": "text", "content": f"Couldn't generate the PDF test right now: {e}"}
        )


# ---- Main content:
if st.session_state.show_about:
    ui.render_about()
    if st.button("← Back"):
        st.session_state.show_about = False
        st.rerun()
    st.stop()

if not st.session_state.current_source:
    ui.render_greeting()
    st.info("👈 Upload a textbook PDF from the sidebar to get started.")
    st.stop()

# Mode buttons
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    if st.button("💬 Ask Questions",use_container_width=True,type="primary" if st.session_state.mode == "quiz" else "secondary"):
        st.session_state.mode = "qa"

with col2:
    if st.button("📝 Quiz Me",use_container_width=True,type="primary" if st.session_state.mode == "quiz" else "secondary"):
        st.session_state.mode = "quiz"

with col3:
    if st.button("📖 Definitions",use_container_width=True, type="primary" if st.session_state.mode == "definitions" else "secondary"):
        st.session_state.mode = "definitions"

with col4:
    if st.button("🗂️ Flashcards",use_container_width=True,type="primary" if st.session_state.mode == "flashcards" else "secondary"):
        st.session_state.mode = "flashcards"

with col5:
    if st.button("📄 Generate PDF Test", use_container_width=True,type="primary" if st.session_state.mode == "pdf_test" else "secondary"):
        st.session_state.mode = "pdf_test"
if st.session_state.current_source not in st.session_state.total_pages:
    st.session_state.total_pages[st.session_state.current_source] = get_page_count(st.session_state.current_source)
max_pages = st.session_state.total_pages[st.session_state.current_source]
page_range = None
num_questions = 8
test_title = None
question_types_selected = None
difficulty_selected = None
action_button_clicked = None
action_prompt = None
flashcard_source_mode = None
flashcard_topic = None
num_cards = None

PDF_TYPE_LABELS = {
    "Multiple Choice": "multiple_choice",
    "True/False": "true_false",
    "Short Answer": "short_answer",
    "Long Answer": "long_answer",
}

if st.session_state.mode == "quiz":
    st.markdown("##### 📝 Generate Practice Quiz")
    st.caption("Quizzes are multiple-choice / true-false and auto-graded. Need short-answer or essay-style questions? Use 📄 Generate PDF Test.")
    c1, c2, c3 = st.columns([3, 1, 1])
    with c1:
        page_range = st.slider("Select page range for quiz", min_value=1, max_value=max(max_pages, 1), value=(1, min(5, max_pages)))
    with c2:
        num_questions = st.number_input("Questions", min_value=3, max_value=25, value=6, step=1)
    with c3:
        st.markdown("<div style='height: 1.7rem;'></div>", unsafe_allow_html=True)
        if st.button("⚡ Generate Quiz Now", type="primary", use_container_width=True, disabled=st.session_state.is_processing):
            action_button_clicked = "quiz"
            action_prompt = f"Generate a quiz for pages {page_range[0]}-{page_range[1]}"

elif st.session_state.mode == "pdf_test":
    st.markdown("##### 📄 Generate Printable Practice Test (PDF)")
    c1, c2 = st.columns([3, 1])
    with c1:
        page_range = st.slider("Select page range for test", min_value=1, max_value=max(max_pages, 1), value=(1, min(5, max_pages)))
    with c2:
        num_questions = st.number_input("Questions", min_value=5, max_value=30, value=8, step=1)

    c3, c4 = st.columns([2, 1])
    with c3:
        type_labels_selected = st.multiselect(
            "Question types to include",
            options=list(PDF_TYPE_LABELS.keys()),
            default=["Multiple Choice", "Short Answer"],
        )
    with c4:
        difficulty_label = st.selectbox("Difficulty", options=["Easy", "Medium", "Hard"], index=1)

    question_types_selected = [PDF_TYPE_LABELS[t] for t in type_labels_selected] if type_labels_selected else None
    difficulty_selected = difficulty_label.lower()

    test_title = st.text_input("Test title (optional)", placeholder=f"e.g. {os.path.splitext(st.session_state.current_source)[0]} — Chapter Test")
    if st.button("⚡ Generate PDF Test Now", type="primary", use_container_width=True, disabled=st.session_state.is_processing):
        if not type_labels_selected:
            st.warning("Pick at least one question type before generating the test.")
        else:
            action_button_clicked = "pdf_test"
            action_prompt = f"Generate a printable practice test (PDF) for pages {page_range[0]}-{page_range[1]}"

elif st.session_state.mode == "definitions":
    st.markdown("##### 📖 Extract Key Terms & Definitions")
    st.caption("Use the page slider to pull every definable term from a chapter, or just type a specific term in the chat box below (e.g. \"define osmosis\").")
    c1, c2 = st.columns([3, 1])
    with c1:
        page_range = st.slider("Select page range for definitions", min_value=1, max_value=max(max_pages, 1), value=(1, min(5, max_pages)))
    with c2:
        st.markdown("<div style='height: 1.7rem;'></div>", unsafe_allow_html=True)
        if st.button("⚡ Extract Definitions Now", type="primary", use_container_width=True, disabled=st.session_state.is_processing):
            action_button_clicked = "definitions"
            action_prompt = f"Extract key terms and definitions for pages {page_range[0]}-{page_range[1]}"

elif st.session_state.mode == "flashcards":
    st.markdown("##### 🗂️ Generate Flashcards")
    st.caption("Pulls key facts, numbers, and concepts as flip-cards-not only formal definitions.")
    flashcard_source_mode = st.radio(
        "Source", options=["By page range","By topic"],horizontal=True
    )
    c1,c2 = st.columns([3,1])
    if flashcard_source_mode == "By page range":
        with c1:
            page_range = st.slider("Seelect page range for flashcards",min_value=1,max_value = max(max_pages,1),value=(1,min(5,max_pages)))
        with c2:
            num_cards = st.number_input("Cards",min_value=3,max_value=20, value=8,step=1)
    else:
        with c1:
            flashcard_topic = st.text_input("Topic",placeholder="e.g. cellular respiration")
        with c2:
            num_cards = st.number_input("Cards",min_value=3,max_value=20,value=8,step=1)

    if st.button("⚡ Generate Flashcards Now",type="primary",use_container_width=True,disabled=st.session_state.is_processing):
        if flashcard_source_mode == "By topic" and not (flashcard_topic and flashcard_topic.strip()):
            st.warning("Enter a topic first.")
        else:
            action_button_clicked = "flashcards"
            if flashcard_source_mode == "By page range":
                assert page_range is not None
                action_prompt = f"Generate flashcards for pages {page_range[0]}-{page_range[1]}"
            else:
                action_prompt = f"Generate flashcards about {flashcard_topic}"

            
st.divider()

chat_container = st.container()

with chat_container:
    if not st.session_state.messages:
        ui.render_greeting()
    else:
        for i, msg in enumerate(st.session_state.messages):
            if msg["type"] == "text":
                if msg["role"] == "user":
                    ui.render_user_bubble(msg["content"])
                else:
                    ui.render_assistant_bubble(msg["content"], citation=msg.get("citation"))
                    if msg.get("sources"):
                        ui.render_sources(msg["sources"])
                    if msg.get("follow_ups"):
                        clicked = render_follow_up_chips(msg["follow_ups"], str(i))
                        if clicked:
                            st.session_state.pending_chip_prompt = clicked
                            st.rerun()

            elif msg["type"] == "flashcards":
                with st.chat_message("assistant", avatar="🪶"):
                    render_flashcard_deck(msg["cards"], msg)

            elif msg["type"] == "quiz":
                with st.chat_message("assistant", avatar="🪶"):
                    results = msg.get("results") if msg["submitted"] else None

                    if not msg["submitted"]:
                        with st.form(key=f"form_{msg['id']}"):
                            answers = ui.render_quiz_card(msg["questions"], msg["id"], msg["submitted"], results)
                            submitted_now = st.form_submit_button("Submit quiz", type="primary")

                        if submitted_now:
                            results = {}
                            correct_count = 0
                            for i, q in enumerate(msg["questions"]):
                                user_ans = answers.get(i)
                                correct = q.get("correct_answer", "")
                                is_correct = False
                                if q.get("type") in ("multiple_choice", "true_false"):
                                    is_correct = bool(user_ans) and user_ans.strip().startswith(str(correct).strip()[:1])
                                results[i] = {"user_answer": user_ans, "correct": is_correct}
                                if is_correct:
                                    correct_count += 1
                            msg["submitted"] = True
                            msg["results"] = results
                            msg["score"] = correct_count

                            from datetime import datetime
                            st.session_state.quiz_history.append({
                                "book": st.session_state.current_source,
                                "score": correct_count,
                                "total": len(msg["questions"]),
                                "date": datetime.now().strftime("%b %d, %H:%M"),
                            })
                            st.rerun()
                    else:
                        ui.render_quiz_card(msg["questions"], msg["id"], msg["submitted"], results)
                        total = len(msg["questions"])
                        ui.render_result_banner(f"You scored {msg['score']} / {total} on auto-graded items.")
    if st.session_state.messages:
        ui.render_auto_scroll()
st.markdown("<div style='height:5.5rem'></div>", unsafe_allow_html=True)

typed = st.chat_input(
    "Ask a question, or say 'quiz me' / 'define X' / 'flashcards no X'/ 'generate a pdf test'",
    disabled= st.session_state.is_processing,
)
pending_chip = st.session_state.pop("pending_chip_prompt",None)
prompt_to_process = typed or action_prompt or pending_chip


if prompt_to_process and not st.session_state.is_processing:
    st.session_state.is_processing = True

    with chat_container:
        ui.render_user_bubble(prompt_to_process)
        thinking_placeholder = ui.render_thinking_start()

    st.session_state.messages.append({"role": "user", "type": "text", "content": prompt_to_process})

    source = st.session_state.current_source
    if action_button_clicked:
        intent = action_button_clicked
    else:
        intent = detect_intent(prompt_to_process, st.session_state.mode)

    start, end = page_range if page_range else (1, st.session_state.total_pages.get(source, 5))

    needs_rerun = True

    if intent == "qa":
        handle_qa_stream(prompt_to_process, source, placeholder=thinking_placeholder)
        needs_rerun = False
    elif intent == "quiz":
        if action_button_clicked == "quiz":
            handle_quiz(source, start, end, num_questions=num_questions)
        else:
            if thinking_placeholder:
                thinking_placeholder.markdown(
                    '<div class="bubble-assistant">To take a quiz, switch to '
                    '<b>📝 Quiz Me</b> mode above, choose your page range and question count, '
                    'then click <b>⚡ Generate Quiz Now</b>.</div>',
                    unsafe_allow_html=True,
                )
            st.session_state.messages.append(
                {"role": "assistant", "type": "text",
                 "content": "To take a quiz, switch to **📝 Quiz Me** mode above, choose your page range and question count, then click **⚡ Generate Quiz Now**."}
            )
            needs_rerun = False
    elif intent == "definitions":
        use_range = (action_button_clicked == "definitions")
        handle_definitions(prompt_to_process, source, start, end, use_range=use_range)
    elif intent == "flashcards":
        if action_button_clicked == "flashcards":
            use_range = (flashcard_source_mode == "By page range")
            handle_flashcards(prompt_to_process,source,start,end,use_range=use_range,topic=flashcard_topic,num_cards=num_cards)
        else:
            if thinking_placeholder:
                thinking_placeholder.markdown(
                    '<div class="bubble-assistant">To make flashcards, switch to'
                    '<b>🗂️ Flashcards</b> mode above, pick a page range or topic,'
                    'then click <b>⚡ Generate Flashcards Now</b>.</div>',
                    unsafe_allow_html=True,
                )
            st.session_state.messages.append(
                {"role":"assistant","type":"text",
                 "content":"To make flashcards, switch to **🗂️ Flashcards** mode above, pick a page range or topic, then click ****⚡ Generate Flashcards Now**."}

            )
            needs_rerun = False
    elif intent == "pdf_test":
        handle_pdf_test(
            source, start, end,
            num_questions=num_questions,
            test_title=test_title,
            question_types=question_types_selected,
            difficulty=difficulty_selected,
        )

    st.session_state.is_processing = False
    if needs_rerun:
        st.rerun()