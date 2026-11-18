# Transcript Studio

[Español](README.md) · [中文](README.zh.md)

Transcript Studio is a **local-first YouTube caption library**. It manages resumable downloads for videos and channel tabs, retains timed caption segments, lets you search the downloaded text, and exports TXT, Markdown, SRT, JSON or NotebookLM volumes. It does not download video or transcribe audio, and cannot guarantee access to YouTube captions.

## Install

Requires Python **3.11+**.

```bash
git clone https://github.com/samuher/YouTube-Transcript-Downloader-and-Cleaner.git
cd YouTube-Transcript-Downloader-and-Cleaner
python -m venv .venv
```

Activate the environment (`.venv\Scripts\Activate.ps1` on Windows PowerShell; `source .venv/bin/activate` on macOS/Linux), then:

```bash
python -m pip install -e .
python -m transcript_studio
```

Open http://127.0.0.1:8765. Create a job with a video or channel URL, start with 5 videos, then use 0 to process the entire `/videos` tab. Search in **Library** and create ZIP exports in **Export**. Jobs persist in SQLite and resume after application restarts; 403 and persistent 429 errors stop the job until you resume it manually. Optional browser cookies are sensitive and do not guarantee successful access.

The original `descargar_transcripciones.py` and `Consolidador.py` remain for command-line compatibility. They do not automatically import files into the new SQLite library. See [architecture](docs/architecture.md) and [Spanish documentation](README.md) for limitations, location of data files, API, and test instructions.

Run tests with `python -m pip install -e '.[dev]'` and `python -m pytest -q`.
