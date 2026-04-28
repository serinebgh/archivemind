"""
ingest.py — Indexe tous les PDF du dossier dans ChromaDB
Usage : python ingest.py
        python ingest.py --reset   (reindexe tout depuis zéro)
"""

import os
import sys
import argparse
import hashlib
import json
import fitz  # PyMuPDF
import chromadb
from chromadb.utils import embedding_functions
from tqdm import tqdm
from config import PDF_FOLDER, CHUNK_SIZE, CHUNK_OVERLAP, CHROMA_DB_PATH, EMBEDDING_MODEL

# ─── EMBEDDING LOCAL VIA OLLAMA ────────────────────────────────────────────────
ollama_ef = embedding_functions.OllamaEmbeddingFunction(
    url="http://localhost:11434/api/embeddings",
    model_name=EMBEDDING_MODEL,
    timeout=300,
)
def get_chroma_collection(reset=False):
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    if reset:
        try:
            client.delete_collection("archivemind")
            print("Collection réinitialisée.")
        except Exception:
            pass
    collection = client.get_or_create_collection(
        name="archivemind",
        embedding_function=ollama_ef,
        metadata={"hnsw:space": "cosine"},
    )
    return collection

def file_hash(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks

def extract_pages(pdf_path):
    """Retourne une liste de (page_num, texte)"""
    pages = []
    try:
        doc = fitz.open(pdf_path)
        for i, page in enumerate(doc):
            text = page.get_text("text").strip()
            if text:
                pages.append((i + 1, text))
        doc.close()
    except Exception as e:
        print(f"  [!] Erreur lecture {pdf_path}: {e}")
    return pages

def get_all_pdfs(folder):
    pdfs = []
    for root, _, files in os.walk(folder):
        for f in files:
            if f.lower().endswith(".pdf"):
                pdfs.append(os.path.join(root, f))
    return sorted(pdfs)

def load_index_registry(registry_path):
    if os.path.exists(registry_path):
        with open(registry_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_index_registry(registry, registry_path):
    with open(registry_path, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2)

def ingest(reset=False):
    if not os.path.isdir(PDF_FOLDER):
        print(f"[ERREUR] Dossier introuvable : {PDF_FOLDER}")
        print("Vérifie le chemin dans config.py")
        sys.exit(1)

    registry_path = os.path.join(CHROMA_DB_PATH, "registry.json")
    collection = get_chroma_collection(reset=reset)

    if reset:
        registry = {}
    else:
        registry = load_index_registry(registry_path)

    pdfs = get_all_pdfs(PDF_FOLDER)
    if not pdfs:
        print(f"Aucun PDF trouvé dans : {PDF_FOLDER}")
        return

    print(f"\n{len(pdfs)} PDF(s) trouvé(s)\n")

    new_count = 0
    skip_count = 0

    for pdf_path in tqdm(pdfs, desc="Indexation"):
        h = file_hash(pdf_path)
        if registry.get(pdf_path) == h:
            skip_count += 1
            continue

        pages = extract_pages(pdf_path)
        rel_path = os.path.relpath(pdf_path, PDF_FOLDER)

        doc_ids = []
        doc_texts = []
        doc_metas = []

        for page_num, page_text in pages:
            chunks = chunk_text(page_text)
            for c_idx, chunk in enumerate(chunks):
                if not chunk.strip():
                    continue
                uid = hashlib.md5(f"{pdf_path}:{page_num}:{c_idx}".encode()).hexdigest()
                doc_ids.append(uid)
                doc_texts.append(chunk)
                doc_metas.append({
                    "source": rel_path,
                    "full_path": pdf_path,
                    "page": page_num,
                    "chunk": c_idx,
                    "filename": os.path.basename(pdf_path),
                })

        if doc_ids:
            # ChromaDB limite les upserts à 5000 à la fois
            batch_size = 500
            for i in range(0, len(doc_ids), batch_size):
                collection.upsert(
                    ids=doc_ids[i:i+batch_size],
                    documents=doc_texts[i:i+batch_size],
                    metadatas=doc_metas[i:i+batch_size],
                )

        registry[pdf_path] = h
        new_count += 1

    save_index_registry(registry, registry_path)

    print(f"\n✓ Indexation terminée")
    print(f"  Nouveaux/modifiés : {new_count}")
    print(f"  Déjà indexés      : {skip_count}")
    print(f"  Total dans la base : {collection.count()} passages")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="Réindexe tout depuis zéro")
    args = parser.parse_args()
    ingest(reset=args.reset)
