"""
app.py — Serveur local ArchiveMind
Lance avec : python app.py
Puis ouvre : http://localhost:5000
"""

import os
import re
import json
import chromadb
import requests
from flask import Flask, request, jsonify, render_template, Response, stream_with_context
from chromadb.utils import embedding_functions
from config import (
    CHROMA_DB_PATH, EMBEDDING_MODEL, OLLAMA_MODEL,
    TOP_K_RESULTS, SERVER_PORT, PDF_FOLDER
)

app = Flask(__name__)

# ─── INIT CHROMADB ─────────────────────────────────────────────────────────────
ollama_ef = embedding_functions.OllamaEmbeddingFunction(
    url="http://localhost:11434/api/embeddings",
    model_name=EMBEDDING_MODEL,
)

def get_collection():
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    return client.get_or_create_collection(
        name="archivemind",
        embedding_function=ollama_ef,
        metadata={"hnsw:space": "cosine"},
    )

# ─── RAG : RECHERCHE DANS LES PDF ─────────────────────────────────────────────
def search_documents(query, n_results=TOP_K_RESULTS):
    try:
        collection = get_collection()
        if collection.count() == 0:
            return []
        results = collection.query(
            query_texts=[query],
            n_results=min(n_results, collection.count()),
            include=["documents", "metadatas", "distances"],
        )
        passages = []
        if results["documents"] and results["documents"][0]:
            for doc, meta, dist in zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
            ):
                passages.append({
                    "text": doc,
                    "source": meta.get("source", "?"),
                    "full_path": meta.get("full_path", ""),
                    "filename": meta.get("filename", "?"),
                    "page": meta.get("page", 0),
                    "score": round(1 - dist, 3),
                })
        return passages
    except Exception as e:
        print(f"[search error] {e}")
        return []

def build_prompt(query, passages):
    context_parts = []
    for i, p in enumerate(passages, 1):
        context_parts.append(
            f"[Source {i} — {p['filename']}, page {p['page']}]\n{p['text']}"
        )
    context = "\n\n".join(context_parts)

    prompt = f"""Tu es un assistant qui répond UNIQUEMENT à partir des documents fournis.
Si la réponse ne se trouve pas dans les extraits ci-dessous, dis-le clairement.
Ne génère jamais d'information qui ne vient pas des documents.

EXTRAITS DES DOCUMENTS :
{context}

QUESTION : {query}

RÉPONSE (cite toujours le fichier et la page) :"""
    return prompt

def query_ollama_stream(prompt):
    """Appelle Ollama en streaming et yield les tokens."""
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": True,
        "options": {
            "temperature": 0.1,
            "num_ctx": 4096,
        }
    }
    try:
        with requests.post(url, json=payload, stream=True, timeout=120) as r:
            r.raise_for_status()
            for line in r.iter_lines():
                if line:
                    data = json.loads(line)
                    token = data.get("response", "")
                    if token:
                        yield token
                    if data.get("done"):
                        break
    except requests.exceptions.ConnectionError:
        yield "\n[ERREUR] Ollama n'est pas lancé. Lance `ollama serve` dans un terminal."
    except Exception as e:
        yield f"\n[ERREUR] {e}"

# ─── ROUTES ────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/status")
def status():
    try:
        collection = get_collection()
        count = collection.count()
        ollama_ok = False
        try:
            r = requests.get("http://localhost:11434/api/tags", timeout=3)
            ollama_ok = r.status_code == 200
        except Exception:
            pass
        return jsonify({
            "indexed_passages": count,
            "pdf_folder": PDF_FOLDER,
            "ollama_ok": ollama_ok,
            "model": OLLAMA_MODEL,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.json
    query = (data.get("query") or "").strip()
    if not query:
        return jsonify({"error": "Question vide"}), 400

    passages = search_documents(query)

    if not passages:
        def no_docs():
            yield "data: " + json.dumps({
                "token": "Aucun document indexé. Lance d'abord `python ingest.py`.",
                "sources": [],
                "done": True
            }) + "\n\n"
        return Response(stream_with_context(no_docs()), mimetype="text/event-stream")

    prompt = build_prompt(query, passages)

    sources = []
    seen = set()
    for p in passages:
        key = (p["filename"], p["page"])
        if key not in seen:
            seen.add(key)
            sources.append({
                "filename": p["filename"],
                "source": p["source"],
                "full_path": p["full_path"],
                "page": p["page"],
                "score": p["score"],
            })

    def generate():
        # D'abord envoie les sources
        yield "data: " + json.dumps({"sources": sources, "token": "", "done": False}) + "\n\n"
        # Puis stream la réponse
        for token in query_ollama_stream(prompt):
            yield "data: " + json.dumps({"token": token, "done": False}) + "\n\n"
        yield "data: " + json.dumps({"token": "", "done": True}) + "\n\n"

    return Response(stream_with_context(generate()), mimetype="text/event-stream")

@app.route("/api/open_pdf", methods=["POST"])
def open_pdf():
    """Ouvre le PDF à la bonne page dans le lecteur par défaut du système."""
    data = request.json
    full_path = data.get("full_path", "")
    page = data.get("page", 1)

    if not full_path or not os.path.exists(full_path):
        return jsonify({"error": "Fichier introuvable"}), 404

    import subprocess, platform
    system = platform.system()
    try:
        if system == "Windows":
            os.startfile(full_path)
        elif system == "Darwin":
            subprocess.Popen(["open", full_path])
        else:
            subprocess.Popen(["xdg-open", full_path])
        return jsonify({"ok": True, "path": full_path, "page": page})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/list_pdfs")
def list_pdfs():
    try:
        collection = get_collection()
        results = collection.get(include=["metadatas"])
        seen = {}
        for meta in results["metadatas"]:
            fn = meta.get("filename", "?")
            if fn not in seen:
                seen[fn] = {
                    "filename": fn,
                    "source": meta.get("source", "?"),
                    "full_path": meta.get("full_path", ""),
                }
        return jsonify({"pdfs": list(seen.values())})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    print(f"\n  ArchiveMind démarré → http://localhost:{SERVER_PORT}\n")
    app.run(host="127.0.0.1", port=SERVER_PORT, debug=False, threaded=True)
