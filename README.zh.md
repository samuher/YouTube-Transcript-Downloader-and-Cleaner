# Transcript Studio

[Español](README.md) · [English](README.en.md)

Transcript Studio 是一款**本地优先的 YouTube 字幕管理工具**。支持视频和频道字幕下载、持久化任务队列、字幕时间戳保存、文本搜索，以及 TXT、Markdown、SRT、JSON、NotebookLM 分卷 ZIP 导出。

**本项目不会下载视频或转录音频，也无法保证 YouTube 始终允许访问所有字幕。** 遇到 403 或持续 429 时，任务会停止，用户可以稍后手动恢复，之前保存的结果不会丢失。

## 安装

需要 Python **3.11 或更高版本**：

```bash
git clone https://github.com/samuher/YouTube-Transcript-Downloader-and-Cleaner.git
cd YouTube-Transcript-Downloader-and-Cleaner
python -m venv .venv
```

Windows PowerShell 使用 `.venv\Scripts\Activate.ps1` 激活环境，macOS/Linux 使用 `source .venv/bin/activate`。然后运行：

```bash
python -m pip install -e .
python -m transcript_studio
```

浏览器打开 http://127.0.0.1:8765。先用 5 个视频测试，再把数量设置为 0 以处理整个频道的 `/videos` 页面。可在“Biblioteca”中搜索字幕，在“Exportaciones”中下载 ZIP。任务记录储存在本机 SQLite 数据库中。浏览器 cookies 为敏感凭据，不应分享，且不能保证解除平台限制。

旧版命令行脚本 `descargar_transcripciones.py` 与 `Consolidador.py` 仍保留，但不会自动导入新数据库。更多详情参阅[架构说明](docs/architecture.md)和[西班牙语文档](README.md)。

测试：`python -m pip install -e '.[dev]'` 后运行 `python -m pytest -q`。
