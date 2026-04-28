import os

# ─── CONFIGURATION ─────────────────────────────────────────────────────────────
# Mets ici le chemin vers ton dossier de PDF
PDF_FOLDER = r"C:\Users\serin\OneDrive\Desktop\cours\E3e"  # Windows
# PDF_FOLDER = "/home/tonnom/archives"               # Linux/Mac

# Modèle Ollama à utiliser (doit être téléchargé via `ollama pull <nom>`)
# Options recommandées selon ta RAM :
#   - 4 Go RAM  → "phi3:mini"
#   - 8 Go RAM  → "mistral" ou "llama3.2"
#   - 16+ Go    → "mistral-nemo" ou "llama3.1:8b"
OLLAMA_MODEL = "mistral"

# Modèle d'embeddings (pour l'indexation — léger, rapide)
EMBEDDING_MODEL = "nomic-embed-text"

# Taille des chunks de texte (en caractères)
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100

# Nombre de passages à récupérer par requête
TOP_K_RESULTS = 5

# Port du serveur local
SERVER_PORT = 5000

# Base de données vectorielle (dossier local)
CHROMA_DB_PATH = os.path.join(os.path.dirname(__file__), "chroma_db")
