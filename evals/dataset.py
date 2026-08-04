
QA_EVAL_CASES =[
    {
        "question":"What is the cell membrane made of?",
        "expected_facts": ["phospholid bilayer","proteins","fluid mosaic model"],
        "expected_page" :1,
        "source": "sample_textbook.pdf",
    },
    {
        "question" : "What dos the nucleolus produce?",
        "expected_facts":["ribosomes"],
        "expected_page":1,
        "source": "sample_textbook.pdf",
    },
    {
        "question": "How many ATP does glycolysis produce net?",
        "expected_facts":["2 ATP","net gain of 2"],
        "expected_page":2,
        "source":"sample_textbook.pdf"

    },
    {
        "question":"What is required as the final electron acceptor in the electron transport chain?",
        "expected_facts":["oxygen"],
        "expected_page":2,
        "source":"sample_textbook.pdf",
    },
    {
        "question":"What is the difference between mitosis and meiosis?",
        "expected_facts":["two genetically identical","four genetically distinct","half the chromosome"],
        "expected_page":3,
        "source":"sample_textbook.pdf",
    },
    {
        "question":"What is the capital of France?",
        "expected_facts":["couldn't find","not found","dont'have"],
        "expected_page":None,
        "source":"sample_textbook.pdf",
        "is_negative_case":True,
    },


]