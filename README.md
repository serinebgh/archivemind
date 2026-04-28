# ArchiveMind

> Moteur de recherche RAG local dans vos PDF — 100% offline, zéro fuite de données.

Pose une question en langage naturel. ArchiveMind lit tes PDF, trouve les passages pertinents et te répond avec le nom du fichier et la page exacte. Rien ne quitte ta machine.

---

## C'est quoi ?

ArchiveMind est un système **RAG** — Retrieval-Augmented Generation.

RAG = un LLM (modèle de langage) couplé à un moteur de recherche dans tes propres documents. Au lieu de répondre depuis sa mémoire d'entraînement, il **récupère d'abord les passages pertinents** dans tes PDF, puis génère une réponse à partir de ces passages uniquement.

Résultat : les réponses sont ancrées dans tes documents, citées et vérifiables — pas inventées.

## Fonctionnement

```
Ta question
    ↓
ChromaDB — recherche vectorielle dans tes PDF indexés  (Retrieval)
    ↓
Ollama (LLM local) — génère une réponse à partir des passages trouvés  (Generation)
    ↓
Réponse + sources cliquables (fichier + page)
```

Le LLM est bridé à tes documents — il ne peut pas inventer ni aller chercher ailleurs.

---

## Prérequis

| Outil | Version minimum | Lien |
|-------|----------------|------|
| Python | 3.10 | [python.org](https://python.org/downloads) |
| Ollama | dernière | [ollama.com](https://ollama.com) |
| RAM libre | 4 Go minimum | — |
| Espace disque | ~5 Go pour les modèles | — |

---

## Installation

### 1. Ollama

Télécharge et installe Ollama depuis [ollama.com](https://ollama.com).

> **Windows avec C: plein** : définis la variable d'environnement avant d'installer pour rediriger les modèles vers un autre disque :
> ```powershell
> [System.Environment]::SetEnvironmentVariable("OLLAMA_MODELS", "D:\ollama\models", "Machine")
> ```

Lance Ollama (garde ce terminal ouvert) :
```bash
ollama serve
```

Dans un second terminal, télécharge les modèles :
```bash
ollama pull mistral
ollama pull nomic-embed-text
```

**Choix du modèle selon ta RAM :**

| RAM disponible | Modèle | Vitesse |
|---------------|--------|---------|
| 4 Go | `phi3:mini` | Rapide |
| 8 Go | `mistral` ✓ | Bon équilibre |
| 16+ Go | `mistral-nemo` | Meilleure qualité |

### 2. Dépendances Python

```bash
cd archivemind
python setup.py
pip install ollama
```

### 3. Configuration

Ouvre `config.py` et renseigne le chemin de ton dossier PDF :

```python
PDF_FOLDER = r"C:\Users\TonNom\Documents\Archives"
```

Le dossier peut contenir des sous-dossiers — tous les PDF sont trouvés automatiquement.

Autres réglages disponibles :

```python
OLLAMA_MODEL = "mistral"              # modèle LLM
EMBEDDING_MODEL = "nomic-embed-text"  # modèle d'indexation
TOP_K_RESULTS = 5                     # passages récupérés par requête (↓ = plus rapide)
CHUNK_SIZE = 800                      # taille des chunks en caractères
```

### 4. Indexation

```bash
python ingest.py
```

L'indexation est incrémentale — les PDF déjà indexés sont ignorés au prochain lancement. Pour tout réindexer depuis zéro :

```bash
python ingest.py --reset
```

### 5. Lancement

```bash
python app.py
```

Ouvre ensuite **http://localhost:5000** dans ton navigateur.

**Windows** : double-clique sur `start.bat` pour tout lancer en un clic.

> ⚠️ Ollama doit toujours tourner en arrière-plan (`ollama serve`) pendant l'utilisation.

---

## Utilisation

1. Pose ta question dans le chat en langage naturel
2. ArchiveMind cherche dans tous tes PDF indexés
3. La réponse s'affiche avec les sources en vert (fichier + page)
4. Clique sur une source → le PDF s'ouvre directement à la bonne page

**Ajouter de nouveaux PDF**

1. Copie les PDF dans le dossier configuré
2. Relance `python ingest.py`
3. Relance `python app.py`

---

## Optimisation des performances

**Réponses lentes ?**

- Passe à `phi3:mini` dans `config.py` — 3x plus rapide que mistral sur CPU
- Réduis `TOP_K_RESULTS = 3` pour analyser moins de passages
- Si tu as une carte graphique Nvidia, Ollama l'utilise automatiquement (x10-x20 plus rapide)

**Vérifier si le GPU est utilisé :**
```bash
ollama ps
```

---

## Structure du projet

```
archivemind/
├── config.py          ← Configuration (chemin PDF, modèle, réglages)
├── ingest.py          ← Indexation des PDF dans ChromaDB
├── app.py             ← Serveur Flask local + API chat
├── setup.py           ← Installation automatique des dépendances
├── start.bat          ← Lancement en un clic (Windows)
├── start.sh           ← Lancement en un clic (Mac/Linux)
├── templates/
│   └── index.html     ← Interface chat
└── chroma_db/         ← Base vectorielle locale (générée automatiquement)
```

---

## Dépannage

**`ollama` non reconnu dans le terminal**
→ Ferme et rouvre le terminal après installation. Sur Windows : `& "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe" serve`

**"Aucun document indexé"**
→ Vérifie le chemin dans `config.py` et relance `python ingest.py`

**Timeout pendant l'indexation**
→ Normal sur les gros PDF — relance simplement `python ingest.py`, les fichiers déjà indexés sont ignorés

**Erreur "Espace insuffisant"**
→ Définis `OLLAMA_MODELS` vers un disque avec plus d'espace (voir section installation)

**Réponse hors sujet**
→ Le LLM répond uniquement à partir des passages récupérés — reformule ta question avec des mots clés plus précis

---

## Confidentialité

- Aucune connexion internet requise après installation
- Aucune donnée ne quitte ta machine
- Les PDF restent sur ton disque
- La base vectorielle (`chroma_db/`) est un dossier local standard
- Le modèle LLM tourne entièrement en local via Ollama

---

## Licence

MIT