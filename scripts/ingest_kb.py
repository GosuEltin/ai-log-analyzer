from pathlib import Path
import json
import re
from typing import List, Dict

from pypdf import PdfReader
import chromadb
from sentence_transformers import SentenceTransformer

SOURCE_DIR = Path("data/kb/source")
PROCESSED_DIR = Path("data/kb/processed")
VECTOR_DIR = Path("data/vectorstore/chroma_db")

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150

EMBED_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
COLLECTION_NAME = "apache_kb"


def ensure_dirs():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    VECTOR_DIR.mkdir(parents=True, exist_ok=True)


def clean_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"\s+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def read_pdf(file_path: Path) -> List[Dict]:
    reader = PdfReader(str(file_path))
    docs = []

    for page_num, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        text = clean_text(text)
        if text:
            docs.append({
                "text": text,
                "metadata": {
                    "source": file_path.name,
                    "doc_type": "apache_official_docs",
                    "page_hint": page_num,
                    "section": "",
                    "topic": "apache_httpd"
                }
            })
    return docs


def read_text_file(file_path: Path) -> List[Dict]:
    text = file_path.read_text(encoding="utf-8", errors="ignore")
    text = clean_text(text)
    if not text:
        return []

    return [{
        "text": text,
        "metadata": {
            "source": file_path.name,
            "doc_type": "runbook" if file_path.suffix.lower() == ".md" else "text_note",
            "page_hint": None,
            "section": "",
            "topic": file_path.stem
        }
    }]


def split_by_paragraphs(text: str) -> List[str]:
    parts = [p.strip() for p in text.split("\n\n") if p.strip()]
    return parts


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    paragraphs = split_by_paragraphs(text)
    chunks = []
    current = ""

    for para in paragraphs:
        if len(current) + len(para) + 2 <= chunk_size:
            current = f"{current}\n\n{para}".strip()
        else:
            if current:
                chunks.append(current)
            if len(para) <= chunk_size:
                current = para
            else:
                start = 0
                while start < len(para):
                    end = min(start + chunk_size, len(para))
                    piece = para[start:end].strip()
                    if piece:
                        chunks.append(piece)
                    if end == len(para):
                        break
                    start = max(end - overlap, start + 1)
                current = ""

    if current:
        chunks.append(current)

    return chunks


def build_chunks() -> List[Dict]:
    raw_docs = []

    for file_path in SOURCE_DIR.glob("*"):
        suffix = file_path.suffix.lower()
        if suffix == ".pdf":
            raw_docs.extend(read_pdf(file_path))
        elif suffix in {".md", ".txt"}:
            raw_docs.extend(read_text_file(file_path))

    chunked_docs = []
    counter = 0

    for doc in raw_docs:
        chunks = chunk_text(doc["text"])
        for idx, chunk in enumerate(chunks):
            counter += 1
            chunked_docs.append({
                "id": f"chunk-{counter:06d}",
                "text": chunk,
                "metadata": {
                    **doc["metadata"],
                    "chunk_index": idx,
                    "chunk_id": f"chunk-{counter:06d}",
                }
            })

    return chunked_docs


def save_chunks_jsonl(chunks: List[Dict]):
    out_path = PROCESSED_DIR / "apache_docs_chunks.jsonl"
    with out_path.open("w", encoding="utf-8") as f:
        for item in chunks:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    print(f"Saved chunks to {out_path}")


def ingest_to_chroma(chunks: List[Dict]):
    client = chromadb.PersistentClient(path=str(VECTOR_DIR))
    collection = client.get_or_create_collection(name=COLLECTION_NAME)

    embed_model = SentenceTransformer(EMBED_MODEL_NAME)

    ids = [x["id"] for x in chunks]
    docs = [x["text"] for x in chunks]
    metas = [x["metadata"] for x in chunks]

    embeddings = embed_model.encode(docs, show_progress_bar=True).tolist()

    # nếu chạy lại nhiều lần, xóa collection cũ để đỡ trùng
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass

    collection = client.get_or_create_collection(name=COLLECTION_NAME)
    collection.upsert(
        ids=ids,
        documents=docs,
        metadatas=metas,
        embeddings=embeddings,
    )

    print(f"Ingested {len(ids)} chunks into collection '{COLLECTION_NAME}'")


def main():
    ensure_dirs()
    chunks = build_chunks()
    save_chunks_jsonl(chunks)
    ingest_to_chroma(chunks)


if __name__ == "__main__":
    main()