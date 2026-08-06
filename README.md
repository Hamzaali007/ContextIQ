# ContextIQ
ContextIQ is a study assistant that reads a textbook PDF and lets you actually work with it, instead of just searching it.Upload a chapter, ask it questions, get quizzed, pull definitions,make flashcards, or generate a printable practice test along with an answer key.
I built this project for HackClub StarDance challenge. I wanted to create an app that will be useful specially for students.So I thought this was the best choice.

# What does it do?
 
Ask Questions works like you'd expect from a RAG app, but I tried to make the grounding visible instead of just trusting it. Every answer streams in and comes with the actual retrieved passages attached in a collapsible panel, so you can check for yourself whether the citation is real. It also remembers the last few exchanges, so follow-up questions work without you having to repeat context, and it suggests a few natural next questions after each answer.

Quiz Me only generates multiple-choice and true/false questions. I went back and forth on this originally; it also generated short-answer and essay questions, but there's no reliable way to auto-grade free text against a model answer without another LLM call in the loop, and I didn't want the quiz to just be wrong sometimes. If you want short-answer or essay-style questions, that's what the PDF test mode is for, where a human (you) grades it.

Definitions can pull every definable term out of a page range, or you can just ask for one specific term and get only that, instead of the whole chapter's glossary dumped on you.

Flashcards work the same way  by page range or by topic,  but they're not limited to formal definitions. A card can be a fact, a number, a process, anything worth memorizing.

PDF Test generation lets you pick exactly which question types you want and how many of each say, 4 multiple choice, 3 true/false, 4 short answer  plus a difficulty level and an optional custom title. It outputs two separate PDFs: the test itself and a separate answer key with explanations.


# Stack
I used Streamlit for the UI as it was easier to use, though I also used HTML and CSS to beautify the UI.PyMuPDF was used for parsing.Langchain was used for recursive text splitter. Gemini was used for embeddings.Groq running Llama 3.3 70B for generation,NeMo Guardrails for input/output safety, and ReportLab for the PDF test generation.


# How to Run this?

You'll need python 3.12, a free tier Qdrant Cloud cluster, and API keys for Groq and Google AI Studio (Gemini)

```
git clone https://github.com/Hamzaali007/ContextIQ
cd contextiq
uv sync
```

Drop a .env file in the project root:
```
GEMINI_API_KEY = YOUR_KEY
QDRANT_CLUSTER_ENDPOINT = ENDPOINT
QDRANT_API_KEY = YOUR KEY
GROQ_API_KEY = YOUR KEY
GROQ_FALLBACK_API_KEY = YOUR KEY
```
Then you have to run the setup scripts once and start the app:
```
python scripts/create_indexes.py
python samplepdf.py
streamlit run app.py
or
python -m streamlit run app.py
```
# Using it:

Upload a PDF from the sidebar, or click the sample textbook button if you just want to try it without hunting for a file. Pick a mode from the row of buttons at the top. For anything chapter-scoped (quiz, definitions, flashcards, PDF test), there's a page-range slider, or for definitions and flashcards you can switch to topic mode instead. You can also just type naturally in the chat — "quiz me," "define X," "flashcards on X,"  and it'll point you to the right controls if something needs a page range first.


# A few honest limitations

Retrieval is page-range based rather than chapter-aware, since there's no reliable, format-agnostic way to detect chapter headings across arbitrary PDFs. Very large page ranges get capped before hitting the model, since Groq's free-tier token limits are easy to blow past on a long chapter; you'll get a note if that happens. There's no persistent accounts system, so everything is scoped to your browser session; close the tab and start fresh elsewhere, and your uploaded books won't follow you
