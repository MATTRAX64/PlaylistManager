# Playlist Manager 🎧

Une application de bureau (Windows, avec fenêtre native via `pywebview`) pour **rechercher, écouter et télécharger des playlists YouTube** en MP3, avec une interface inspirée de Spotify — le tout en un seul fichier `manager.pyw`.

## ✨ Fonctionnalités

- 🔎 Recherche de playlists YouTube par mot-clé, ou ajout direct via un lien (`youtube.com/playlist?list=...`)
- ⭐ Sauvegarde de playlists en favoris, avec vérification automatique de leur disponibilité
- ▶️ Lecture audio des titres directement dans l'app (téléchargement temporaire + lecture via `pygame`)
- ⬇️ Téléchargement des titres en MP3 (individuellement ou playlist entière), avec tags ID3 (titre / artiste / album) automatiques
- ⚙️ Paramètres personnalisables : qualité audio, dossier de téléchargement, organisation par playlist, thème d'accent, etc.
- 🖥️ Interface 100% HTML/CSS/JS embarquée, affichée dans une fenêtre native grâce à `pywebview`

## 📦 Prérequis

- **Python 3.9+** installé et accessible dans le PATH
- **ffmpeg** installé et accessible dans le PATH (nécessaire pour convertir l'audio en MP3 — ce n'est pas une librairie Python, voir ci-dessous)

## 🚀 Installation

### 1. Installer les dépendances Python

Ce projet utilise des librairies qui ne font pas partie de la bibliothèque standard de Python. Un script d'installation automatique est fourni :

```
install_dependencies.bat
```

Double-clique dessus (ou lance-le depuis un terminal) : il va installer automatiquement :

| Librairie | Rôle |
|---|---|
| [`yt-dlp`](https://github.com/yt-dlp/yt-dlp) | Recherche, extraction d'infos et téléchargement des vidéos/playlists YouTube |
| [`pywebview`](https://pywebview.flowrl.com/) | Affiche l'interface HTML dans une fenêtre native (sans navigateur externe) |
| [`mutagen`](https://mutagen.readthedocs.io/) | Écrit les tags ID3 (titre, artiste, album) sur les fichiers MP3 téléchargés |
| [`pygame`](https://www.pygame.org/) | Lecture audio locale des MP3 (contourne les limitations de WebView2 avec `<audio>`) |

Le script vérifie aussi si Python et **ffmpeg** sont bien accessibles, et t'indique où télécharger ffmpeg si besoin (il ne s'installe pas via pip, car ce n'est pas une librairie Python mais un exécutable externe).

### 2. Lancer l'application

Une fois les dépendances installées, double-clique simplement sur :

```
manager.pyw
```

(Le `.pyw` lance le script sans ouvrir de console, comme une vraie application Windows.)

## 🗂️ Structure des données

Au premier lancement, l'application crée automatiquement à côté du script :

- `data.json` — playlists sauvegardées en favoris
- `settings.json` — préférences utilisateur (qualité audio, dossier de téléchargement, thème...)
- `Playlists/` — dossier par défaut des MP3 téléchargés (modifiable dans les paramètres)

## ⚠️ Avertissement

Ce projet interagit avec le contenu de YouTube via `yt-dlp`. Le téléchargement de contenu protégé par des droits d'auteur peut être soumis à des restrictions légales selon ta juridiction et les conditions d'utilisation de YouTube. Utilise cet outil de manière responsable et à des fins personnelles.

## 🛠️ Stack technique

- **Backend** : Python (`webview`, `yt_dlp`, `mutagen`, `pygame`)
- **Frontend** : HTML/CSS/JS vanilla, embarqué directement dans le script Python et affiché via `pywebview`
- **Communication** : pont JS ↔ Python via l'API `js_api` de `pywebview`
