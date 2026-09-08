@echo off
setlocal enabledelayedexpansion
title Playlist Manager - Installation des dependances
color 0A

echo ============================================================
echo   Playlist Manager - Installation des dependances Python
echo ============================================================
echo.

REM --- Verifie que Python est installe et accessible dans le PATH ---
where python >nul 2>nul
if errorlevel 1 (
    echo [ERREUR] Python n'a pas ete trouve dans le PATH.
    echo Installe Python depuis https://www.python.org/downloads/
    echo puis coche "Add python.exe to PATH" pendant l'installation.
    echo.
    pause
    exit /b 1
)

echo Python detecte :
python --version
echo.

REM --- Met pip a jour ---
echo Mise a jour de pip...
python -m pip install --upgrade pip
echo.

REM --- Installe les librairies tierces necessaires (non incluses dans la
REM     bibliotheque standard de Python) ---
echo Installation des librairies Python requises :
echo   - yt-dlp    (recherche / extraction / telechargement YouTube)
echo   - pywebview (interface graphique / fenetre app)
echo   - mutagen   (ecriture des tags ID3 sur les MP3)
echo   - pygame    (lecture audio)
echo.

python -m pip install --upgrade yt-dlp pywebview mutagen pygame

if errorlevel 1 (
    echo.
    echo [ERREUR] L'installation d'une ou plusieurs librairies a echoue.
    echo Verifie ta connexion internet ou les messages ci-dessus.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   Librairies Python installees avec succes !
echo ============================================================
echo.

REM --- Verifie la presence de ffmpeg, requis mais non installable via pip ---
where ffmpeg >nul 2>nul
if errorlevel 1 (
    echo [ATTENTION] ffmpeg n'a pas ete trouve dans le PATH.
    echo ffmpeg est INDISPENSABLE pour convertir/telecharger l'audio en MP3.
    echo Ce n'est pas une librairie Python : il doit etre installe separement.
    echo.
    echo   1. Telecharge une version Windows ici :
    echo      https://www.gyan.dev/ffmpeg/builds/
    echo      ^(prends le build "release essentials"^)
    echo   2. Decompresse l'archive, ex : C:\ffmpeg
    echo   3. Ajoute le sous-dossier "bin" ^(ex: C:\ffmpeg\bin^) a la
    echo      variable d'environnement PATH de Windows.
    echo   4. Redemarre ce terminal pour verifier avec : ffmpeg -version
    echo.
) else (
    echo ffmpeg detecte :
    ffmpeg -version | findstr /b "ffmpeg"
    echo.
)

echo ============================================================
echo   Installation terminee. Tu peux maintenant lancer manager.pyw
echo ============================================================
echo.
pause
