# YouTube 字幕下载与清理

[Español](README.md) · [English](README.en.md)

下载 YouTube 视频已有的字幕，清理时间戳和常见重复片段，并为每个视频生成 TXT 文件。也可以把文件整理成适合 NotebookLM 的分卷。

**本程序不会下载视频或转录音频。** 如果视频没有可访问的字幕，将不会产生转录文本。

## 安装

需要 Python 3.11 或更高版本。

```bash
git clone https://github.com/samuher/YouTube-Transcript-Downloader-and-Cleaner.git
cd YouTube-Transcript-Downloader-and-Cleaner
python -m pip install -r requirements.txt
```

Windows 可以使用 `py`，macOS/Linux 可以使用 `python3` 代替 `python`。

## 下载字幕

```bash
python descargar_transcripciones.py -c "https://www.youtube.com/@ChannelName" -i zh,en
```

可以指定文件夹或先下载前五个视频：

```bash
python descargar_transcripciones.py -c "https://www.youtube.com/@ChannelName" -i zh -d "my_transcripts" --max-videos 5
```

也支持单个视频链接。省略 `-c` 可以使用交互模式。

| 参数 | 功能 |
| --- | --- |
| `-c, --canal` | 频道或视频链接 |
| `-i, --idiomas` | 字幕语言，以逗号分隔；默认 `en` |
| `-d, --destino` | 输出文件夹 |
| `--max-videos N` | 最多处理 N 个视频 |
| `--forzar` | 重新下载已有结果 |

输出文件名包含视频 ID，避免同名文件覆盖。隐藏文件 `.transcripciones_index.json` 记录成功下载的字幕，以便下次跳过。没有字幕的视频会在以后重新尝试。

## 整理 NotebookLM 分卷

```bash
python Consolidador.py -o "transcripciones/ChannelName" -d "notebooklm_listo"
```

指定每卷的单词数及文件名前缀：

```bash
python Consolidador.py -o "my_transcripts" -d "notebooklm_listo" -l 100000 -n "Course"
```

默认每卷最多 450000 词，可设置的最大值为 500000，且标题词数也计算在内。过长的单个字幕会自动分段。输入文件夹与输出文件夹必须不同。重新运行时，相同前缀的旧分卷将被替换，剩余旧卷将被删除。

NotebookLM 还有[词数、文件大小、来源数量限制](https://support.google.com/gemininotebook/answer/16215270?hl=en)；本程序仅检查词数。

## 常见问题

- 没有生成 TXT：确认视频有对应语言的字幕。
- 403、429 或登录限制：YouTube 可能拒绝请求，可以稍后再试。
- 下载工具失效：运行 `python -m pip install -U yt-dlp`。
- 自动字幕仍有错误：程序只能清理常见重叠文本，无法纠正语音识别错误。

## 测试

```bash
python -m unittest discover -s tests -v
```

自动化测试不会访问 YouTube。
