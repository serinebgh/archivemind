# ArchiveMind

Moteur de recherche local dans vos PDF. 100% offline, aucune donnée envoyée.

## Ce que ça fait

- Tu déposes 1 ou 10 000 PDF dans un dossier
- ArchiveMind les indexe une fois
- Tu poses des questions en français naturel
- Il te répond **uniquement à partir de tes PDF**, avec le nom du fichier et la page exacte
- Tu cliques sur la source → ça ouvre le PDF à la bonne page

---

## Installation (15 minutes)

### Étape 1 — Python

Si Python n'est pas installé : https://python.org/downloads  
Version minimum : **3.10**

### Étape 2 — Ollama (moteur IA local)

1. Télécharge Ollama sur https://ollama.com
2. Installe-le
3. Dans un terminal, lance :

```
ollama serve
```

4. Dans un autre terminal, télécharge les modèles :

```
ollama pull mistral
ollama pull nomic-embed-text
```

> `mistral` = le cerveau qui répond à tes questions (~4 Go)  
> `nomic-embed-text` = transforme le texte en vecteurs (~300 Mo)

**Alternatives selon ta RAM :**
| RAM disponible | Modèle recommandé |
|---------------|-------------------|
| 4 Go          | `phi3:mini`       |
| 8 Go          | `mistral` ✓       |
| 16+ Go        | `mistral-nemo`    |

### Étape 3 — Dépendances Python

Dans le dossier `archivemind/`, lance :

```
python setup.py
```

### Étape 4 — Configuration

Ouvre `config.py` et mets le chemin de ton dossier PDF :

```python
PDF_FOLDER = r"C:\Users\TonNom\Documents\Archives"
```

Change aussi le modèle si tu en as choisi un autre :

```python
OLLAMA_MODEL = "mistral"   # ou "phi3:mini" etc.
```

### Étape 5 — Indexation

Lance l'indexation (une seule fois, ou quand tu ajoutes des PDF) :

```
python ingest.py
```

Pour les gros volumes (milliers de PDF), ça peut prendre du temps. L'avancement s'affiche en temps réel. Les PDF déjà indexés sont ignorés lors des prochains lancements.

### Étape 6 — Lancer l'interface

```
python app.py
```

Puis ouvre http://localhost:5000 dans ton navigateur.

**Ou** double-clique sur `start.bat` (Windows).

---

## Utilisation

1. Pose ta question dans le chat
2. ArchiveMind cherche dans tous tes PDF
3. Il répond avec les passages pertinents
4. Les sources apparaissent en vert avec le nom du fichier et la page
5. Clique sur une source → le PDF s'ouvre à la bonne page

**Ajouter des PDF**
1. Copie les nouveaux PDF dans ton dossier configuré
2. Relance `python ingest.py`
3. Relance `python app.py`

**Réindexer tout depuis zéro**
```
python ingest.py --reset
```

---

## Architecture

```
Tes PDF (disque local)
       ↓
   ingest.py
   PyMuPDF → extrait le texte page par page
   Découpe en chunks (800 caractères)
   Ollama nomic-embed-text → vecteurs
       ↓
   ChromaDB (dossier chroma_db/ local)
       ↓
   app.py (Flask local)
   → Reçoit ta question
   → La convertit en vecteur
   → Cherche les passages les plus proches
   → Envoie au LLM Ollama avec les passages
   → Stream la réponse
       ↓
   Interface web (localhost:5000)
```

**Aucune connexion internet requise après installation.**  
**Aucune donnée ne quitte ta machine.**

---

## Dépannage

**"Ollama non détecté"**  
→ Lance `ollama serve` dans un terminal séparé

**"Aucun document indexé"**  
→ Vérifie le chemin dans `config.py` et relance `python ingest.py`

**Réponses lentes**  
→ Normal sur CPU — le premier message prend 10-30 secondes  
→ Passe à `phi3:mini` si ta machine est limitée

**Erreur de mémoire**  
→ Change pour un modèle plus petit dans `config.py`

---

## Structure des fichiers

```
archivemind/
├── config.py          ← Configuration (chemin PDF, modèle)
├── ingest.py          ← Indexation des PDF
├── app.py             ← Serveur local
├── setup.py           ← Installation des dépendances
├── start.bat          ← Lancement Windows
├── start.sh           ← Lancement Mac/Linux
├── templates/
│   └── index.html     ← Interface chat
└── chroma_db/         ← Base vectorielle (créée automatiquement)
```
