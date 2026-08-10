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
- [4. Download a channel's transcripts](#4-download-a-channels-transcripts)
- [5. Consolidate transcripts for NotebookLM](#5-consolidate-transcripts-for-notebooklm)
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

## 4. Download a channel's transcripts

There are two ways to run it — pick whichever you prefer.

### Option A: interactive mode (recommended if you're not comfortable with the terminal)

From the project folder, run:

```bash
python descargar_transcripciones.py
```

The script will ask you for:
1. The channel URL (e.g. `https://www.youtube.com/@ChannelName`)
2. The folder to save the `.txt` files in (press Enter to auto-generate one from the channel name)
3. The subtitle language (press Enter to default to English)

> 💡 You don't need to add `/videos` to the end of the URL — the script does that automatically, to avoid downloading Shorts, livestreams, and duplicate videos from the channel's playlists.

### Option B: command line (to automate it or rerun it without typing anything by hand)

```bash
python descargar_transcripciones.py -c "https://www.youtube.com/@ChannelName" -d "transcripciones/MyChannel" -i en,es
```

| Flag | What it does | Required |
|---|---|---|
| `-c`, `--canal` | YouTube channel URL | Yes |
| `-d`, `--destino` | Folder to save the `.txt` files in | No (auto-generated if omitted) |
| `-i`, `--idiomas` | Subtitle languages, comma-separated (e.g. `en,es`) | No (defaults to `en`) |

The script will show progress in the terminal, and once it finishes, you'll have the clean `.txt` files in the destination folder.

---

## 5. Consolidate transcripts for NotebookLM

If you're going to upload the transcripts to [NotebookLM](https://notebooklm.google/), the project includes `Consolidador.py`, which groups the loose `.txt` files into "volumes" that respect NotebookLM's **500,000-words-per-source** limit (with a 450,000-word safety margin by default), instead of uploading each video as a separate source and quickly burning through the free plan's 50-source limit.

### Option A: interactive mode

```bash
python Consolidador.py
```

It will ask for the source folder (where the `.txt` files are), the destination folder, the word limit per volume, and optionally a name for the generated files.

### Option B: command line

```bash
python Consolidador.py -o "transcripciones/MyChannel" -d "notebooklm_listo" -l 450000 -n "MyChannel"
```

| Flag | What it does | Required |
|---|---|---|
| `-o`, `--origen` | Folder with the loose `.txt` files to consolidate | Yes |
| `-d`, `--destino` | Folder to save the consolidated volumes in | No (defaults to `notebooklm_listo`) |
| `-l`, `--limite` | Word limit per volume | No (defaults to 450,000) |
| `-n`, `--nombre` | Prefix for naming the generated volumes | No (derived from the source folder) |

When it finishes, the script warns you if the number of generated volumes exceeds NotebookLM's 50-source limit on the free plan.

---

## 6. Customize the project

Most settings (channel, folder, language, word limit) no longer require touching the code — they're passed as flags or answered interactively, as explained in steps 4 and 5.

For anything beyond that, you'll need to edit the code directly:

| What you want to change | Where to edit it | How |
|---|---|---|
| The output filename format for each video | `'outtmpl'` inside `ydl_opts` in `descargar_transcripciones.py` | Use [yt-dlp's output templates](https://github.com/yt-dlp/yt-dlp#output-template) |
| The separator between transcripts inside the consolidated volumes | The `texto_consolidado += ...` block in `Consolidador.py` | Change the separator text and the `FUENTE:` label to your liking |

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
