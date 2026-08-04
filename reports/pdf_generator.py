import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet , ParagraphStyle
from reportlab.lib.units import inch

def _get_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="QuestionText", fontSize=11, spaceAfter=6, leading=15
    ))

    styles.add(ParagraphStyle(
        name="OptionText", fontSize=10, leftIndent=20, spaceAfter=3, leading=13
    ))

    styles.add(ParagraphStyle(
        name="AnswerLine", fontSize=10, leftIndent=20, spaceAfter=14, leading=13,
        textColor=colors.HexColor("#999999"),
    ))

    return styles


def _answer_lines(styles, num_lines: int) -> list:
    """Ruled blank lines for students to write short/long answers on the test paper."""
    rule = "_" * 78
    return [Paragraph(rule, styles["AnswerLine"]) for _ in range(num_lines)]

def generate_test_pdf(quiz_data:dict, title:str,output_path:str) -> str:
    """
    Renders quiz_data["questions"] into a printable test paper PDF (no answers).
    Returns the output file path.
    """
    styles = _get_styles()
    doc = SimpleDocTemplate(output_path,pagesize=letter,)
    story = []
    story.append(Paragraph(title,styles["Title"]))
    generated_str = datetime.now().strftime("%B %d %Y")
    story.append(Paragraph(f"Generated: {generated_str}", styles["Normal"]))
    story.append(Spacer(1,20))
    story.append(Paragraph("Name:___________________      Date: _______________",styles["Normal"]))
    story.append(Spacer(1,20))

    for i,q in enumerate(quiz_data["questions"],start=1):
        story.append(Paragraph(f"{i}. {q['question']}", styles["QuestionText"]))

        qtype = q.get("type")
        if qtype in ("multiple_choice", "true_false") and q.get("options"):
            for opt in q["options"]:
                story.append(Paragraph(opt,styles["OptionText"]))
            story.append(Spacer(1, 10))
        elif qtype == "long_answer":
            # Essay-style question — give several ruled lines to write on.
            story.extend(_answer_lines(styles, 7))
        elif qtype in ("short_answer", "definition"):
            # Brief written response — a couple of ruled lines is enough.
            story.extend(_answer_lines(styles, 2))
        else:
            story.append(Spacer(1,12))



    doc.build(story)
    return output_path


def _format_answer_display(q: dict) -> str:
    """For multiple_choice, show the full option text next to the letter
    (e.g. 'B. 40 hours') instead of just the bare letter, so the answer key
    is readable without cross-referencing the test paper."""
    qtype = q.get("type")
    correct = q.get("correct_answer", "")
    if qtype == "multiple_choice" and q.get("options"):
        target_letter = str(correct).strip()[:1].upper()
        for opt in q["options"]:
            if str(opt).strip()[:1].upper() == target_letter:
                return opt
    return str(correct)


def generate_answer_key_pdf(quiz_data:dict, title:str, output_path:str) ->str:
    """
    Renders quiz_data['questions'] into an answer key PDF (correct answers + explanations).
    Returns the output file path.
    """

    styles = _get_styles()
    doc = SimpleDocTemplate(output_path,pagesize=letter,topMargin=0.75*inch,bottomMargin=0.75*inch,leftMargin=0.75*inch,rightMargin=0.75*inch)
    story = []

    story.append(Paragraph(f"{title} - Answer Key", styles["Title"]))
    story.append(Spacer(1,20))

    for i,q in enumerate(quiz_data["questions"],start=1):
        story.append(Paragraph(f"{i}. {q['question']}", styles["QuestionText"]))
        story.append(Paragraph(f"<b>Answer:</b> {_format_answer_display(q)}", styles["OptionText"]))
        if q.get("explanation"):
            story.append(Paragraph(f"<b>Explanation:</b> {q['explanation']}",styles["OptionText"]))

        story.append(Spacer(1,10))

    
    doc.build(story)

    return output_path



def generate_test_and_key(quiz_data:dict,source_name:str,output_dir:str = "generated_tests",custom_title:str | None = None) ->dict:
    if "questions" not in quiz_data or not quiz_data["questions"]:
        raise ValueError(f"Cannot generate PDF: invalid quiz data. Got: {quiz_data}")

    os.makedirs(output_dir,exist_ok=True)
    safe_name = os.path.splitext(source_name)[0].replace(" ","_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    title = custom_title.strip() if custom_title and custom_title.strip() else f"Test- {os.path.splitext(source_name)[0]}"
    test_path = os.path.join(output_dir,f"{safe_name}_test_{timestamp}.pdf")
    key_path  = os.path.join(output_dir,f"{safe_name}_Answerkey_{timestamp}.pdf")

    generate_test_pdf(quiz_data,title,test_path)
    generate_answer_key_pdf(quiz_data,title,key_path)

    return {"test_pdf":test_path, "answer_key_pdf":key_path}