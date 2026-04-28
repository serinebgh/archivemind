@echo off
title ArchiveMind
color 0A
echo.
echo  ===================================
echo   ArchiveMind — Demarrage
echo  ===================================
echo.

:: Vérifie que Python est dispo
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERREUR] Python non trouve.
    echo  Installe Python sur https://python.org
    pause
    exit /b 1
)

:: Vérifie que Ollama tourne
echo  Verification Ollama...
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo  [!] Ollama n'est pas lance.
    echo  Lance "ollama serve" dans un autre terminal.
    echo.
    echo  Appuie sur une touche pour continuer quand meme...
    pause >nul
)

echo  Demarrage du serveur...
echo  Ouvre ton navigateur sur http://localhost:5000
echo.
start "" http://localhost:5000
python app.py

pause
