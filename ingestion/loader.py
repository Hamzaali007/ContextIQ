import pdfplumber

def extract_pdf(pdf_path):
    """Extract text (and tables) per page.
    Returns: list of dicts -> [{"page": 1, "text": "..."}, ...]
    """
    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""

            table_text = ""
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    row_text = " | ".join(str(cell) if cell else "" for cell in row)
                    table_text += row_text + "\n"

            pages.append({"page": page_num, "text": text + "\n" + table_text})

    return pages