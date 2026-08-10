# 📺 YouTube 字幕下载与清理工具

**🌐 Idiomas / Languages / 语言:** [Español](README.md) · [English](README.en.md) · [中文](README.zh.md)

这是一个 Python 脚本，可以自动下载 YouTube 频道中所有视频的字幕（transcript），并将其转换为干净的 `.txt` 文件，不含时间戳或标签——可直接用于阅读、分析或作为纯文本使用。

---

## 📑 目录

- [这个脚本能做什么？](#-这个脚本能做什么)
- [环境要求](#-环境要求)
- [1. 安装 Python](#1-安装-python)
- [2. 下载项目](#2-下载项目)
- [3. 安装依赖库](#3-安装依赖库)
- [4. 配置要下载的频道](#4-配置要下载的频道)
- [5. 运行脚本](#5-运行脚本)
- [6. 自定义项目](#6-自定义项目)
- [无需安装的替代方案：Google Colab / Jupyter](#-无需安装的替代方案google-colab--jupyter)
- [注意事项与常见问题](#-注意事项与常见问题)

---

## 🔍 这个脚本能做什么？

1. 接收一个 YouTube 频道的链接。
2. 使用 [`yt-dlp`](https://github.com/yt-dlp/yt-dlp) 库**只下载字幕**（不下载视频本身）。
3. 清理每个字幕文件（`.vtt`）：去除时间戳、HTML 标签和重复的行。
4. 将结果保存为每个视频对应的纯文本 `.txt` 文件。
5. 删除原始的 `.vtt` 文件，最终目标文件夹中只保留干净的 `.txt` 文件。

---

## ✅ 环境要求

- **Python 3.8 或更高版本**
- **稳定的网络连接** —— 脚本会逐个视频从 YouTube 下载数据，如果频道视频较多，会花费较长时间并消耗较多带宽。

---

## 1. 安装 Python

### 检查是否已经安装

打开终端（Windows 上是 `cmd` 或 `PowerShell`，macOS/Linux 上是 `Terminal`），输入：

```bash
python --version
```

如果提示命令无法识别，试试：

```bash
python3 --version
```

如果显示类似 `Python 3.11.4` 的内容，说明已经安装好了，可以直接跳到[第 2 步](#2-下载项目)。

### 如果尚未安装

1. 前往官方网站：**[python.org/downloads](https://www.python.org/downloads/)**
2. 下载适合你操作系统的最新稳定版本。
3. **Windows：** 安装过程中，务必勾选 **"Add python.exe to PATH"** 选项后再点击安装（这是大多数人容易漏掉的一步）。
4. **macOS：** 可以使用官方安装包，或者如果安装了 [Homebrew](https://brew.sh/)，运行 `brew install python`。
5. **Linux（Debian/Ubuntu）：** 通常系统自带；如果没有，运行：
   ```bash
   sudo apt update && sudo apt install python3 python3-pip
   ```
6. 关闭并重新打开终端，再次运行 `python --version` 确认安装成功。

---

## 2. 下载项目

使用 Git 克隆仓库：

```bash
git clone https://github.com/<你的用户名>/<你的仓库名>.git
cd <你的仓库名>
```

如果不使用 Git，也可以直接在 GitHub 上点击绿色的 **"Code" → "Download ZIP"** 按钮下载压缩包并解压。

---

## 3. 安装依赖库

本项目只需要一个外部库：`yt-dlp`（`os` 和 `re` 是 Python 自带的标准库）。

在项目文件夹中运行：

```bash
pip install -r requirements.txt
```

如果 `pip` 命令无效，试试 `pip3` 或 `python -m pip install -r requirements.txt`。

---

## 4. 配置要下载的频道

打开 `descargar_transcripciones.py`，找到文件末尾的这两行：

```python
url_del_canal = "https://www.youtube.com/@CanalDeEjemplo"
ruta_de_guardado = r"transcripciones/CanalDeEjemplo"
```

- **`url_del_canal`**：替换为你想下载的频道链接（例如 `https://www.youtube.com/@频道名` 或 `https://www.youtube.com/channel/UCxxxxxx`）。
- **`ruta_de_guardado`**：这是保存 `.txt` 文件的文件夹名称，可以自由命名。

---

## 5. 运行脚本

在项目文件夹中运行：

```bash
python descargar_transcripciones.py
```

（根据系统情况，也可能是 `python3 descargar_transcripciones.py`）

脚本会在终端中显示进度，完成后，你可以在 `ruta_de_guardado` 指定的文件夹中找到清理好的 `.txt` 文件。

---

## 6. 自定义项目

| 想修改的内容 | 修改位置 | 方法 |
|---|---|---|
| 要下载的频道 | `url_del_canal` | 粘贴新的频道链接 |
| 输出文件夹 | `ruta_de_guardado` | 填写你想要的路径/名称 |
| 字幕语言 | `ydl_opts` 中的 `'subtitleslangs': ['en']` | 将 `'en'` 改为 `'es'`（西班牙语）、`'zh'`（中文）等，也可以填写多个：`['zh', 'en']` |
| 输出文件命名格式 | `ydl_opts` 中的 `'outtmpl'` | 参考 [yt-dlp 的输出模板文档](https://github.com/yt-dlp/yt-dlp#output-template) |

---

## 💻 无需安装的替代方案：Google Colab / Jupyter

如果不想在电脑上安装 Python，也可以在网页版笔记本中运行同样的代码：

- **[Google Colab](https://colab.research.google.com/)**：新建一个笔记本，把代码粘贴到单元格中，运行前先添加一个单元格执行 `!pip install yt-dlp`。只需要一个 Google 账号即可。
- **Jupyter Notebook**：如果想在本地电脑上使用笔记本形式，运行 `pip install notebook` 安装后，通过 `jupyter notebook` 命令打开。

⚠️ **使用 Colab 或其他云端笔记本前请注意：**
- 整个运行过程中都**需要稳定的网络连接**，因为每个视频都是实时下载的。
- 对于视频数量较多的频道，运行时间可能**较长**，并且会占用笔记本会话中较多的临时存储空间。
- 免费版 Colab 在长时间无操作后会自动断开连接，因此非常大的频道可能需要分多次运行完成。

---

## 🛠 注意事项与常见问题

- **"字幕不可用"报错**：并不是所有视频都有配置语言的自动或人工字幕；脚本会自动跳过这些视频并继续处理其余的（这得益于 `'ignoreerrors': True` 设置）。
- **yt-dlp 突然无法使用**：YouTube 平台经常更新，如果脚本开始报错，请更新该库：
  ```bash
  pip install -U yt-dlp
  ```
- **运行速度很慢**：这是正常现象，因为频道视频较多时，每个视频都需要单独发起一次请求。为避免被 YouTube 临时封锁请求，不建议并行处理。
