# YouTube Transcript Downloader & Cleaner

[Español](README.md) · [中文](README.zh.md)

Download available YouTube captions as clean text files, one file per video. Optionally combine them into word-limited volumes for NotebookLM.

This tool downloads **subtitles, not audio or video**. It cannot transcribe videos without accessible captions.

## Install

Python 3.11+ is required.

```bash
git clone https://github.com/samuher/YouTube-Transcript-Downloader-and-Cleaner.git
cd YouTube-Transcript-Downloader-and-Cleaner
python -m pip install -r requirements.txt
```

On Windows, try `py` if `python` is unavailable; on macOS/Linux try `python3`.

## Download subtitles

```bash
python descargar_transcripciones.py -c "https://www.youtube.com/@ChannelName" -i en,es
```

By default, the files are stored in `transcripciones/ChannelName/`. Use another directory and limit the first run to five videos:

```bash
python descargar_transcripciones.py -c "https://www.youtube.com/@ChannelName" -d "my_transcripts" -i en --max-videos 5
```

Individual video links are supported. Run without `-c` for interactive prompts.

| Flag | Description |
| --- | --- |
| `-c, --canal` | Channel or video URL |
| `-i, --idiomas` | Comma-separated languages, default `en` |
| `-d, --destino` | Output directory |
| `--max-videos N` | Process up to N videos |
| `--forzar` | Force previously completed downloads |

Filenames include video IDs (e.g., `Video [abcdefghijk].en.txt`) to prevent collisions. A hidden `.transcripciones_index.json` records successful downloads so they are skipped on subsequent runs. Videos with no available captions are retryable.

## Combine for NotebookLM

```bash
python Consolidador.py -o "transcripciones/ChannelName" -d "notebooklm_listo"
```

Customize the word limit and output prefix:

```bash
python Consolidador.py -o "my_transcripts" -d "notebooklm_listo" -l 100000 -n "Course"
```

The default limit is 450,000 words per volume, with a maximum of 500,000. Headings count toward that limit. Oversized files are split into labeled parts. Input and output directories must differ. Existing numbered volumes using the same prefix are replaced, and old excess volumes are removed.

NotebookLM has [separate word, file size, and source count limits](https://support.google.com/gemininotebook/answer/16215270?hl=en); this tool checks word count only.

## Troubleshooting

- No TXT: try a video with captions or another language.
- 403/429 or sign-in errors: YouTube may limit access; try again later.
- Downloads fail unexpectedly: update using `python -m pip install -U yt-dlp`.
- Automatic subtitles remain imperfect: the cleaner handles common overlap, not speech recognition mistakes.

## Tests

```bash
python -m unittest discover -s tests -v
```

The automated tests do not contact YouTube.
