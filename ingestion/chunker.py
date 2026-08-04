from langchain_text_splitters import RecursiveCharacterTextSplitter

def chunk_text(text,chunk_size =1000,chunk_overlap=200):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size= chunk_size,
        chunk_overlap=chunk_overlap,
        separators = ["\n\n", "\n", " ", ""],
        length_function = len
    )

    chunks = splitter.split_text(text)
    return chunks



def chunk_pages(pages, chunk_size=1000, chunk_overlap=200):
    """pages: list of {"page": int, "text": str}
    returns: list of {"page": int, "chunk_id": int, "text": str}
    """
    all_chunks = []
    for page in pages:
        page_chunks = chunk_text(page["text"], chunk_size, chunk_overlap)
        for i, chunk in enumerate(page_chunks):
            all_chunks.append({
                "page": page["page"],
                "chunk_id": i,
                "text": chunk
            })
    return all_chunks