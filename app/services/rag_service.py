from typing import List
import chromadb
from sentence_transformers import SentenceTransformer
from app.services.investigation_focus import detect_focus_mode

VECTOR_DIR = "data/vectorstore/chroma_db"
COLLECTION_NAME = "apache_kb"
EMBED_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

client = chromadb.PersistentClient(path=VECTOR_DIR)
collection = client.get_or_create_collection(name=COLLECTION_NAME)
embed_model = SentenceTransformer(EMBED_MODEL_NAME)


def build_retrieval_query(
    cluster_labels: List[str],
    probable_causes: List[str],
    evidence: List[str],
    user_query: str = "",
) -> str:
    parts = []

    if user_query.strip():
        parts.append("User goal: " + user_query.strip())

    if cluster_labels:
        parts.append("Clusters: " + " | ".join(cluster_labels))

    if probable_causes:
        parts.append("Causes: " + " | ".join(probable_causes[:4]))

    if evidence:
        parts.append("Evidence: " + " | ".join(evidence[:3]))

    return " ; ".join(parts)


def _doc_type_rank(meta: dict) -> int:
    doc_type = meta.get("doc_type", "")
    if doc_type == "runbook":
        return 0
    if doc_type == "text_note":
        return 1
    if doc_type == "apache_official_docs":
        return 2
    return 3


def _is_backend_doc(meta: dict) -> bool:
    source = (meta.get("source", "") or "").lower()
    topic = (meta.get("topic", "") or "").lower()
    merged = f"{source} {topic}"
    return any(k in merged for k in [
        "mod_jk", "worker", "workers2", "ajp", "backend", "tomcat"
    ])


def _is_access_doc(meta: dict) -> bool:
    source = (meta.get("source", "") or "").lower()
    topic = (meta.get("topic", "") or "").lower()
    merged = f"{source} {topic}"
    return any(k in merged for k in [
        "forbidden", "access", "directory", "htaccess", "allowoverride", "directoryindex"
    ])


def _should_drop_doc(meta: dict, focus_mode: str) -> bool:
    if focus_mode == "backend_connectivity" and _is_access_doc(meta):
        return True
    if focus_mode == "access_control" and _is_backend_doc(meta):
        return True
    return False


def _focus_rank(meta: dict, focus_mode: str) -> int:
    if focus_mode == "backend_connectivity":
        if _is_backend_doc(meta):
            return 0
        return 10

    if focus_mode == "access_control":
        if _is_access_doc(meta):
            return 0
        return 10

    return 0


def retrieve_knowledge(
    cluster_labels: List[str],
    probable_causes: List[str],
    evidence: List[str],
    user_query: str = "",
    top_k: int = 4,
) -> List[str]:
    focus_mode = detect_focus_mode(user_query)

    query = build_retrieval_query(
        cluster_labels=cluster_labels,
        probable_causes=probable_causes,
        evidence=evidence,
        user_query=user_query,
    )

    if not query.strip():
        return []

    query_embedding = embed_model.encode([query]).tolist()[0]

    result = collection.query(
        query_embeddings=[query_embedding],
        n_results=max(top_k * 4, 12),
    )

    docs = result.get("documents", [[]])[0]
    metas = result.get("metadatas", [[]])[0]

    merged = []
    for doc, meta in zip(docs, metas):
        if _should_drop_doc(meta, focus_mode):
            continue
        merged.append((doc, meta))

    merged.sort(
        key=lambda item: (
            _focus_rank(item[1], focus_mode),
            _doc_type_rank(item[1]),
            item[1].get("source", ""),
        )
    )

    combined = []
    seen = set()

    for doc, meta in merged:
        source = meta.get("source", "unknown")
        topic = meta.get("topic", "")
        page = meta.get("page_hint", "")
        doc_type = meta.get("doc_type", "")

        key = (source, topic, str(page), doc[:120])
        if key in seen:
            continue
        seen.add(key)

        prefix = f"[source={source}"
        if doc_type:
            prefix += f", type={doc_type}"
        if topic:
            prefix += f", topic={topic}"
        if page:
            prefix += f", page={page}"
        prefix += "] "

        combined.append(prefix + doc)

        if len(combined) >= top_k:
            break

    return combined