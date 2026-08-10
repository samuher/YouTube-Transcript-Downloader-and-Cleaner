# 📺 YouTube Transcript Downloader & Cleaner

**🌐 Idiomas / Languages / 语言:** [Español](README.md) · [English](README.en.md) · [中文](README.zh.md)

A Python script that automatically downloads the transcripts (subtitles) of every video on a YouTube channel and converts them into clean `.txt` files, with no timestamps or tags — ready to read, analyze, or use as plain text.

---

## 📑 Table of contents

- [What does this script do?](#-what-does-this-script-do)
- [Prerequisites](#-prerequisites)
- [1. Install Python](#1-install-python)
- [2. Download the project](#2-download-the-project)
- [3. Install the dependencies](#3-install-the-dependencies)
- [4. Configure the channel to download](#4-configure-the-channel-to-download)
- [5. Run the script](#5-run-the-script)
- [6. Customize the project](#6-customize-the-project)
- [No-install alternatives: Google Colab / Jupyter](#-no-install-alternatives-google-colab--jupyter)
- [Notes and common issues](#-notes-and-common-issues)

---

## 🔍 What does this script do?

1. Takes the URL of a YouTube channel.
2. Uses the [`yt-dlp`](https://github.com/yt-dlp/yt-dlp) library to download **only the subtitles** of each video (it does not download the video itself).
3. Cleans each subtitle file (`.vtt`): removes timestamps, HTML tags, and duplicate lines.
4. Saves the result as a plain `.txt` file per video.
5. Deletes the original `.vtt` files, leaving only the clean `.txt` files in the destination folder.

---

## ✅ Prerequisites

- **Python 3.8 or higher**
- **A stable internet connection** — the script downloads data from YouTube video by video, so on large channels it can take a while and use significant bandwidth.

---

## 1. Install Python

### Check if you already have it installed

Open a terminal (`cmd`/`PowerShell` on Windows, `Terminal` on macOS/Linux) and type:

```bash
python --version
```

If the command isn't recognized, try:

```bash
python3 --version
```

If you see something like `Python 3.11.4`, you're already set — skip to [step 2](#2-download-the-project).

### If it's not installed

1. Go to the official site: **[python.org/downloads](https://www.python.org/downloads/)**
2. Download the latest stable release for your operating system.
3. **Windows:** during installation, check the box **"Add python.exe to PATH"** before clicking install (this is the step most people miss).
4. **macOS:** you can use the official installer, or if you have [Homebrew](https://brew.sh/), run `brew install python`.
5. **Linux (Debian/Ubuntu):** it's usually already installed; if not, run:
   ```bash
   sudo apt update && sudo apt install python3 python3-pip
   ```
6. Close and reopen your terminal, then run `python --version` again to confirm it installed correctly.

---

## 2. Download the project

Clone the repository with Git:

```bash
git clone https://github.com/<your-username>/<your-repository>.git
cd <your-repository>
```

If you don't use Git, you can also download the project as a ZIP from GitHub (green **"Code" → "Download ZIP"** button) and extract it.

---

## 3. Install the dependencies

This project only needs one external library: `yt-dlp` (the other two, `os` and `re`, come built into Python).

From the project folder, run:

```bash
pip install -r requirements.txt
```

If `pip` doesn't work, try `pip3` or `python -m pip install -r requirements.txt`.

---

## 4. Configure the channel to download

Open `descargar_transcripciones.py` and find these two lines at the end of the file:

```python
url_del_canal = "https://www.youtube.com/@CanalDeEjemplo"
ruta_de_guardado = r"transcripciones/CanalDeEjemplo"
```

- **`url_del_canal`**: replace it with the URL of the channel you want (e.g. `https://www.youtube.com/@ChannelName` or `https://www.youtube.com/channel/UCxxxxxx`).
- **`ruta_de_guardado`**: this is the folder name where the `.txt` files will be saved. You can name it whatever you like.

---

## 5. Run the script

From the project folder:

```bash
python descargar_transcripciones.py
```

(or `python3 descargar_transcripciones.py` depending on your system)

The script will show progress in the terminal, and once it finishes, you'll find the clean `.txt` files inside the folder you set in `ruta_de_guardado`.

---

## 6. Customize the project

| What you want to change | Where to edit it | How |
|---|---|---|
| The channel to download | `url_del_canal` | Paste the new channel's URL |
| The output folder | `ruta_de_guardado` | Type whatever path/name you want |
| The subtitle language | `'subtitleslangs': ['en']` inside `ydl_opts` | Change `'en'` to `'es'` (Spanish), `'zh'` (Chinese), etc. You can list several: `['es', 'en']` |
| The output filename format | `'outtmpl'` inside `ydl_opts` | Use [yt-dlp's output templates](https://github.com/yt-dlp/yt-dlp#output-template) |

---

## 💻 No-install alternatives: Google Colab / Jupyter

If you don't want to install Python on your computer, you can run this same code in a notebook:

- **[Google Colab](https://colab.research.google.com/)**: create a new notebook, paste the code into a cell, and before running it, add a cell with `!pip install yt-dlp`. You only need a Google account.
- **Jupyter Notebook**: if you'd rather run it on your own machine, install it with `pip install notebook` and open it with `jupyter notebook`.

⚠️ **Before using Colab or another cloud notebook, keep in mind:**
- You need a **stable internet connection for the entire run**, since each video is downloaded on the spot.
- On channels with many videos, the process can be **long** and use a fair amount of temporary storage in the notebook session.
- Free Colab sessions disconnect after a period of inactivity, so very large channels may need to be split across several runs.

---

## 🛠 Notes and common issues

- **"Subtitles not available" error**: not every video has automatic or manual subtitles in the configured language; the script will skip those and continue with the rest (thanks to `'ignoreerrors': True`).
- **yt-dlp suddenly stops working**: YouTube changes its platform frequently. If the script starts failing, update the library:
  ```bash
  pip install -U yt-dlp
  ```
- **The process is very slow**: this is normal on channels with many videos, since a request is made per video. There's no safe way to parallelize it without risking a temporary block from YouTube.
