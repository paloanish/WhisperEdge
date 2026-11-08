# WhisperEdge

![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)
![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux-lightgrey.svg)

<div align="center">
  <img src="assets/logo.png" alt="WhisperEdge Logo" width="256"/>
</div>

Welcome to **WhisperEdge**. 

I built this desktop app because I needed a reliable way to generate subtitles for massive media files (we're talking 12+ hours) entirely locally on my own hardware. I wanted something that wouldn't crash halfway through, wouldn't hallucinate weird text during silent gaps, and would keep all my data completely private. 

Powered by the `faster-whisper` engine and a clean CustomTkinter GUI, WhisperEdge takes your audio or video files and automatically generates highly accurate WebVTT captions and JSON data.

## ✨ Why use WhisperEdge?

* **Drop in a Video, Get Captions:** You don't need to strip the audio out yourself. If you give it a video file, WhisperEdge automatically uses `FFmpeg` under the hood to extract the audio, translate it, and generate subtitles. Standalone audio files work straight away too.
* **Crash-Proof (Live Appending):** This app flushes the data to your hard drive segment-by-segment in real-time. If you cancel the process or your computer dies, you keep every single word it already captioned. 
* **No More Hallucination Loops:** If you've used Whisper models before, you know they sometimes repeat the same phrase forever during silent parts of a video. The built-in Voice Activity Detection (VAD) filter completely neutralizes infinite loops of repeating the same phrase during silent parts of audio/video.
* **Track Selection:** This app scans the file and lets you pick exactly which audio stream you want to process in case of multiple audio tracks (like different languages).
* **Cross-Platform & GPU Acceleration:** It hooks seamlessly into Nvidia GPUs via CUDA for faster speeds. Plus, it works perfectly whether you are running Windows or booting into Linux.

---

## 📂 Project Structure

```yaml
WhisperEdge/
├── assets/                  # App icon and README image
│   ├── logo.png
│   └── logo.ico
├── src/                     # Core application source code
│   ├── main.py              # CustomTkinter GUI & threading
│   ├── transcriber.py       # faster-whisper logic & VAD filtering
│   └── media_utils.py       # FFmpeg audio extraction & duration utilities
├── .gitignore
├── LICENSE
├── README.md
└── requirements.txt

# --- Automatically generated or user-provided files (Not in Repo) ---
├── models/                  # Downloaded faster-whisper CTranslate2 models
├── ffmpeg.exe               # Required for Windows audio extraction
├── ffprobe.exe              # Required for Windows audio duration parsing
└── venv/                    # Virtual environment
```

---

## 🚀 Getting Started

Here is exactly how to get it running on your machine.

### 1. Install FFmpeg (Required)
WhisperEdge needs FFmpeg to handle the audio extraction.
* **Windows:** Download `ffmpeg.exe` and `ffprobe.exe` from [ffmpeg.org](https://ffmpeg.org/download.html) and drop those two `.exe` files straight into your `WhisperEdge` project folder.
* **Linux:** Just install it system-wide (e.g., `sudo dnf install ffmpeg` or `sudo pacman -S ffmpeg`). The app will automatically detect it.

### 2. Clone the Repository
Open your terminal and paste the code:
```bash
git clone https://github.com/paloanish/WhisperEdge.git
cd WhisperEdge
```

### 3. Create a Virtual Environment
Keep the dependencies clean and isolated by creating and activating a virtual environment:
```bash
# Create the environment
python -m venv venv

# Activate it (Windows)
.\venv\Scripts\activate

# Activate it (Linux)
source venv/bin/activate
```

### 4. Install CUDA PyTorch (Crucial for GPU Acceleration)
To make sure it actually uses your Nvidia GPU, you must install this specific version of PyTorch before anything else:
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### 5. Install other dependencies
Now install the core app dependencies:
```bash
pip install -r requirements.txt
```

### 6. Run the App
Launch the interface and start generating subtitles!
```bash
python src/main.py
```

---

## 🛠️ Building a Standalone Release

Want to share this with someone who doesn't have Python installed? You can compile the entire app into a standalone offline folder using **PyInstaller**.

Before building, ensure the local FFmpeg binaries are sitting in your root project folder. For the **Full** release, ensure you have run the app at least once so the AI models are downloaded into the `models/` directory.

*Note: We use `python -m PyInstaller` to ensure the build remains strictly isolated to your virtual environment.*

### 🪟 Windows Builds

**Full Release** (Includes AI models • 100% Offline)
```bash
python -m PyInstaller --noconsole --name "WhisperEdge-Full" --icon="assets/logo.ico" --add-data "ffmpeg.exe;." --add-data "ffprobe.exe;." --add-data "models;models" --collect-data "faster_whisper" src/main.py
```

**Lite Release** (Smaller size • Downloads models on first run)
```bash
python -m PyInstaller --noconsole --name "WhisperEdge-Lite" --icon="assets/logo.ico" --add-data "ffmpeg.exe;." --add-data "ffprobe.exe;." --collect-data "faster_whisper" src/main.py
```

### 🐧 Linux Builds

**Full Release** (Includes AI models • 100% Offline)
```bash
python -m PyInstaller --noconsole --name "WhisperEdge-Full" --add-data "ffmpeg:." --add-data "ffprobe:." --add-data "models:models" --collect-data "faster_whisper" src/main.py
```

**Lite Release** (Smaller size • Downloads models on first run)
```bash
python -m PyInstaller --noconsole --name "WhisperEdge-Lite" --add-data "ffmpeg:." --add-data "ffprobe:." --collect-data "faster_whisper" src/main.py
```

Once the build finishes, you'll find your ready-to-share distributable folder inside the `dist/` directory. Zip it up and send it!

---

## 📦 Download the Standalone App (No Python Required)

You can download the ready-to-use application directly from the [Releases](https://github.com/paloanish/WhisperEdge/releases) page. 

There are two versions available:
* **WhisperEdge Full:** Larger download size. Comes pre-loaded with the AI models and works 100% offline the second you extract the folder.
> Full version is NOT downloadable as github has a strict 2GB limit for a file.


* **WhisperEdge Lite:** Very small download size. Requires an internet connection on the first run to automatically fetch the AI models.

**How to use:**
1. Download your preferred `.zip` file from the latest release.
2. Extract the folder to your computer.
3. Double-click `WhisperEdge-Full.exe` or `WhisperEdge-Lite.exe` to launch the app!

---

## 📄 License
Copyright 2026 Anish Palo

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

---