

import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

OUTPUT_DIR = "assets"
OUTPUT_PATH = os.path.join(OUTPUT_DIR, "sample_textbook.pdf")

CONTENT = [
    ("Chapter 1: The Cell", [
        "All living organisms are composed of cells, the basic structural and functional unit of life. "
        "Cells were first observed by Robert Hooke in 1665, and the cell theory, formalized in the 1830s, "
        "states that all living things are made of cells, the cell is the basic unit of life, and all cells "
        "arise from pre-existing cells.",
        "There are two broad categories of cells: prokaryotic and eukaryotic. Prokaryotic cells, found in "
        "bacteria and archaea, lack a membrane-bound nucleus and most organelles. Eukaryotic cells, found in "
        "plants, animals, fungi, and protists, contain a true nucleus and a variety of specialized organelles.",
    ]),
    ("1.1 The Cell Membrane", [
        "The cell membrane, also called the plasma membrane, is a selectively permeable barrier that separates "
        "the cell's interior from its external environment. It is composed primarily of a phospholipid bilayer "
        "embedded with proteins, a structure described by the fluid mosaic model.",
        "The membrane controls what enters and exits the cell through passive transport (diffusion, osmosis) "
        "and active transport, which requires energy in the form of ATP to move substances against their "
        "concentration gradient.",
    ]),
    ("1.2 The Nucleus", [
        "The nucleus is the control center of the eukaryotic cell, housing the cell's DNA organized into "
        "chromosomes. It is surrounded by a double membrane called the nuclear envelope, which contains pores "
        "that regulate the movement of molecules between the nucleus and the cytoplasm.",
        "Within the nucleus, the nucleolus is responsible for producing ribosomes, which are later transported "
        "to the cytoplasm to carry out protein synthesis.",
    ]),
    ("Chapter 2: Cellular Respiration", [
        "Cellular respiration is the process by which cells convert nutrients, primarily glucose, into usable "
        "energy in the form of ATP (adenosine triphosphate). This process occurs mainly within the mitochondria, "
        "often called the powerhouse of the cell.",
        "Cellular respiration consists of three main stages: glycolysis, which occurs in the cytoplasm and "
        "produces a small amount of ATP; the Krebs cycle, which occurs in the mitochondrial matrix; and the "
        "electron transport chain, which produces the majority of the cell's ATP.",
    ]),
    ("2.1 Glycolysis", [
        "Glycolysis is the first stage of cellular respiration and does not require oxygen, making it an "
        "anaerobic process. During glycolysis, one molecule of glucose is broken down into two molecules of "
        "pyruvate, yielding a net gain of 2 ATP and 2 NADH molecules.",
    ]),
    ("2.2 The Electron Transport Chain", [
        "The electron transport chain is located in the inner mitochondrial membrane and consists of a series "
        "of protein complexes that pass electrons from NADH and FADH2 down an energy gradient. This process "
        "drives the production of a large majority of the cell's ATP through a process called chemiosmosis, "
        "and requires oxygen as the final electron acceptor, making it an aerobic process.",
    ]),
    ("Chapter 3: Cell Division", [
        "Cell division allows organisms to grow, repair damaged tissue, and reproduce. In eukaryotic cells, "
        "division occurs through one of two processes: mitosis, which produces two genetically identical "
        "daughter cells, or meiosis, which produces four genetically distinct gametes with half the "
        "chromosome number of the parent cell.",
        "Mitosis consists of four main phases: prophase, metaphase, anaphase, and telophase, collectively "
        "known as the mitotic phase, which is preceded by interphase, during which the cell grows and "
        "replicates its DNA.",
    ]),
]


def build_sample_pdf():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    styles = getSampleStyleSheet()
    heading_style = ParagraphStyle("Heading", parent=styles["Heading2"], spaceBefore=16, spaceAfter=8)
    body_style = ParagraphStyle("Body", parent=styles["Normal"], fontSize=11, leading=16, spaceAfter=10)

    doc = SimpleDocTemplate(OUTPUT_PATH, pagesize=letter,
                             topMargin=0.9 * inch, bottomMargin=0.9 * inch)
    story = [Paragraph("Introduction to Cell Biology", styles["Title"]), Spacer(1, 20)]

    for heading, paragraphs in CONTENT:
        story.append(Paragraph(heading, heading_style))
        for p in paragraphs:
            story.append(Paragraph(p, body_style))

    doc.build(story)
    print(f"Sample textbook created at {OUTPUT_PATH}")


if __name__ == "__main__":
    build_sample_pdf()






