#!/bin/bash
echo ""
echo "  ==================================="
echo "   ArchiveMind — Démarrage"
echo "  ==================================="
echo ""

# Vérifie Python
if ! command -v python3 &> /dev/null; then
    echo "  [ERREUR] python3 non trouvé."
    exit 1
fi

# Vérifie Ollama
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "  [!] Ollama non détecté. Lance 'ollama serve' dans un autre terminal."
fi

echo "  Démarrage → http://localhost:5000"

# Ouvre le navigateur (Mac)
if [[ "$OSTYPE" == "darwin"* ]]; then
    sleep 1 && open http://localhost:5000 &
else
    sleep 1 && xdg-open http://localhost:5000 &
fi

python3 app.py
