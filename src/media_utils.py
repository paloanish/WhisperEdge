# Copyright 2026 Anish Palo
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import sys
import json
import subprocess

CREATE_NO_WINDOW = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0

def get_project_root():
    """
    Returns the path where the executable or main.py actually lives
    This escapes PyInstaller's _internal directory
    """
    if getattr(sys, 'frozen', False):
        # If running as PyInstaller executable, get the folder containing the .exe
        return os.path.dirname(sys.executable)
    else:
        # If running from source, get the folder containing src/
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Resolve executable paths (Prefers bundled .exe, falls back to system PATH)
FFMPEG_BIN = os.path.join(get_project_root(), "ffmpeg.exe")
if not os.path.exists(FFMPEG_BIN):
    FFMPEG_BIN = "ffmpeg"  # Fallback to system PATH

FFPROBE_BIN = os.path.join(get_project_root(), "ffprobe.exe")
if not os.path.exists(FFPROBE_BIN):
    FFPROBE_BIN = "ffprobe"

def get_audio_duration(input_path: str) -> float:
    """Returns the media duration in seconds"""
    cmd = [
        FFPROBE_BIN, "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", input_path
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, creationflags=CREATE_NO_WINDOW)
        return float(result.stdout.strip())
    except Exception:
        return 0.0

def probe_audio_tracks(media_path: str) -> list:
    """Returns a list of dictionaries containing audio track metadata"""
    if not os.path.isfile(media_path):
        return []
    
    cmd = [
        FFPROBE_BIN, "-v", "error", "-select_streams", "a",
        "-show_entries", "stream=index,codec_name:stream_tags=language,title",
        "-of", "json", media_path
    ]
    
    tracks = []
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, creationflags=CREATE_NO_WINDOW)
        data = json.loads(result.stdout)
        streams = data.get("streams", [])
        
        for i, s in enumerate(streams):
            tags = s.get("tags", {})
            lang = tags.get("language", "und")
            title = tags.get("title", f"Track {i + 1}")
            codec = s.get("codec_name", "unknown")
            
            tracks.append({
                "index": i,
                "display_text": f"Track {i}: {title} ({lang}) [{codec}]"
            })
    except Exception:
        pass
        
    return tracks

def extract_audio_for_whisper(input_path: str, output_path: str, track_idx: int = 0, sample_rate: int = 16000):
    """Extracts a specific audio track to a 16kHz mono WAV file optimized for Whisper Models"""
    cmd = [
        FFMPEG_BIN, "-y", "-i", input_path,
        "-map", f"0:a:{track_idx}", "-vn",
        "-acodec", "pcm_s16le", "-ar", str(sample_rate), "-ac", "1",
        "-threads", "0", 
        output_path
    ]
    # Let exceptions bubble up so the UI can catch and display them
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True, creationflags=CREATE_NO_WINDOW)