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
import json
import threading
from faster_whisper import WhisperModel
from huggingface_hub import snapshot_download
from media_utils import get_project_root

def format_timestamp(seconds: float) -> str:
    """Formats seconds into WebVTT timestamp format (HH:MM:SS.mmm)"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int(round((seconds - int(seconds)) * 1000))
    return f"{h:02}:{m:02}:{s:02}.{ms:03}"

class WhisperTranscriber:
    def __init__(self):
        self.cancel_event = threading.Event()
        
    def cancel(self):
        self.cancel_event.set()
        
    def reset(self):
        self.cancel_event.clear()

    def transcribe(self, 
                   audio_path: str, 
                   output_vtt: str, 
                   output_json: str, 
                   model_size: str, 
                   total_duration: float, 
                   progress_callback=None):
        self.reset()
        
        # Checking for local files
        if progress_callback:
            progress_callback(f"Status: Checking local '{model_size}' model...", None)
            
        root_dir = get_project_root()
        model_dir = os.path.join(root_dir, "models", model_size)

        # Ensure the directory exists before downloading
        os.makedirs(model_dir, exist_ok=True)
            
        # If missing, update UI to Downloading before locking the thread
        if not os.path.exists(model_dir) or not os.listdir(model_dir):
            if progress_callback:
                progress_callback(f"Status: Downloading '{model_size}' model (Might take some minutes)...", None)
            
            snapshot_download(
                repo_id=f"Systran/faster-whisper-{model_size}",
                local_dir=model_dir,
                local_dir_use_symlinks=False
            )
            
        # When download is completed, load into RAM/VRAM
        if progress_callback:
            progress_callback("Status: Loading model into Memory/VRAM...", None)
            
        try:
            model = WhisperModel(model_dir, device="cuda", compute_type="float16")
        except Exception:
            model = WhisperModel(model_dir, device="cpu", compute_type="int8")
            
        # Actual transcription begins
        if progress_callback:
            progress_callback("Status: Generating Subtitles (Fast Mode Active)...", 0.0)

        # Greedy decoding (beam_size=1) and disabled condition_on_previous_text 
        # for maximum speed and anti-hallucination on long files.
        segments_result, _ = model.transcribe(
            audio_path, 
            beam_size=1, 
            word_timestamps=True, 
            language="en", 
            vad_filter=True, 
            condition_on_previous_text=False
        )
        
        segments_data = []
        
        # Live Append Mode for WebVTT
        with open(output_vtt, "w", encoding="utf-8") as vtt_file:
            vtt_file.write("WEBVTT\n\n")
            
            for segment in segments_result:
                if self.cancel_event.is_set():
                    break
                    
                for word in segment.words:
                    segments_data.append({
                        "start_time": word.start, 
                        "end_time": word.end, 
                        "word": word.word.strip()
                    })
                    vtt_file.write(f"{format_timestamp(word.start)} --> {format_timestamp(word.end)}\n{word.word.strip()}\n\n")
                
                vtt_file.flush() # Force write buffer to OS
                
                if progress_callback and total_duration > 0:
                    progress_callback(None, segment.end)

        # Dump structured data to JSON, preserving progress even if cancelled
        if segments_data:
            if progress_callback:
                progress_callback("Status: Saving JSON...", None)
            with open(output_json, "w", encoding="utf-8") as f:
                json.dump(segments_data, f, indent=4)
                
        return "Cancelled" if self.cancel_event.is_set() else "Completed"