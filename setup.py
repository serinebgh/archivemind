"""
setup.py — Installe toutes les dépendances Python de ArchiveMind
Usage : python setup.py
"""
import subprocess
import sys
import os

PACKAGES = [
    "flask",
    "flask-cors",
    "pymupdf",           # fitz — parsing PDF
    "chromadb",          # base vectorielle locale
    "requests",
    "tqdm",
    "sentence-transformers",  # fallback embeddings si Ollama absent
]

def run(cmd):
    print(f"  → {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=False)
    return result.returncode == 0

def main():
    print("\n═══════════════════════════════════════")
    print("  ArchiveMind — Installation")
    print("═══════════════════════════════════════\n")

    pip = [sys.executable, "-m", "pip", "install", "--upgrade"]

    print("[1/3] Mise à jour de pip…")
    run(pip + ["pip"])

    print("\n[2/3] Installation des dépendances Python…")
    ok = run(pip + PACKAGES)
    if not ok:
        print("[ERREUR] L'installation a échoué. Vérifie ta connexion.")
        sys.exit(1)

    print("\n[3/3] Vérification Ollama…")
    import requests as req
    try:
        r = req.get("http://localhost:11434/api/tags", timeout=3)
        if r.status_code == 200:
            print("  Ollama est déjà actif ✓")
        else:
            raise Exception()
    except Exception:
        print("  Ollama non détecté.")
        print("  → Télécharge-le sur https://ollama.com")
        print("  → Lance : ollama serve")
        print("  → Puis  : ollama pull mistral")
        print("  → Puis  : ollama pull nomic-embed-text")

    print("\n═══════════════════════════════════════")
    print("  Installation terminée !")
    print("\n  Prochaines étapes :")
    print("  1. Edite config.py → mets le chemin de tes PDF")
    print("  2. python ingest.py   (indexation)")
    print("  3. python app.py      (démarre l'interface)")
    print("     Ouvre http://localhost:5000")
    print("═══════════════════════════════════════\n")

if __name__ == "__main__":
    main()
