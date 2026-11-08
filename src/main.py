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
import time
import threading
import customtkinter as ctk
from tkinter import filedialog, messagebox
from transcriber import WhisperTranscriber, format_timestamp
from media_utils import get_audio_duration, probe_audio_tracks, extract_audio_for_whisper

# PyInstaller No-Console Fix
class DummyStream:
    def write(self, _): pass
    def flush(self): pass
if sys.stdout is None:
    sys.stdout = DummyStream()
if sys.stderr is None:
    sys.stderr = DummyStream()

def format_duration(seconds: float) -> str:
    m = int(seconds // 60)
    s = int(seconds % 60)
    if seconds >= 3600:
        h = int(seconds // 3600)
        return f"{h}h {m}m {s}s"
    return f"{m}m {s}s"

class WhisperEdgeApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("WhisperEdge")
        self.geometry("680x380")
        self.resizable(False, False)
        
        self.transcriber = WhisperTranscriber()
        self.audio_tracks_data = []
        self.total_duration = 0.0
        
        self._build_ui()
        
    def _build_ui(self):
        self.path_entry = ctk.CTkEntry(self, width=450, placeholder_text="Enter Path of the Video or Audio File", justify="center")
        self.path_entry.grid(row=0, column=0, padx=(20, 10), pady=(20, 10), sticky="ew")

        self.browse_btn = ctk.CTkButton(self, text="Browse Media", command=self.browse_media)
        self.browse_btn.grid(row=0, column=1, padx=(0, 20), pady=(20, 10))

        self.out_path_entry = ctk.CTkEntry(self, width=450, placeholder_text="Output Destination (Auto-fills on Media Selection)", justify="center")
        self.out_path_entry.grid(row=1, column=0, padx=(20, 10), pady=(5, 10), sticky="ew")

        self.out_browse_btn = ctk.CTkButton(self, text="Browse Output", command=self.browse_output)
        self.out_browse_btn.grid(row=1, column=1, padx=(0, 20), pady=(5, 10))

        # Track Selector
        track_frame = ctk.CTkFrame(self)
        track_frame.grid(row=2, column=0, columnspan=2, padx=20, pady=(0, 10), sticky="ew")
        ctk.CTkLabel(track_frame, text="Audio Track:").pack(side="left", padx=(10, 5), pady=5)

        self.track_menu_var = ctk.StringVar(value="Default (First Track)")
        self.track_menu = ctk.CTkOptionMenu(track_frame, variable=self.track_menu_var, values=["Default (First Track)"], width=400)
        self.track_menu.pack(side="left", padx=5, pady=5, fill="x", expand=True)

        # Model Selector
        self.model_name = ctk.StringVar(value="small")
        model_frame = ctk.CTkFrame(self)
        model_frame.grid(row=3, column=0, columnspan=2, pady=(0, 10), padx=20, sticky="ew")
        self.model_buttons = []
        for idx, model in enumerate(["tiny", "base", "small", "medium", "large-v3"]):
            btn = ctk.CTkRadioButton(model_frame, text=model.capitalize().replace("v", "V"), variable=self.model_name, value=model)
            btn.grid(row=0, column=idx, padx=12, pady=5)
            self.model_buttons.append(btn)

        # Status Update
        self.progress_label = ctk.CTkLabel(self, text="Status: Inactive")
        self.progress_label.grid(row=4, column=0, columnspan=2, padx=20, sticky="w")

        self.progress_bar = ctk.CTkProgressBar(self, width=550)
        self.progress_bar.set(0)
        self.progress_bar.grid(row=5, column=0, columnspan=2, padx=20, pady=5, sticky="ew")

        self.time_label = ctk.CTkLabel(self, text="Time taken: N/A")
        self.time_label.grid(row=6, column=0, columnspan=2, padx=20, sticky="w")

        self.start_btn = ctk.CTkButton(self, text="Generate Data", command=self.start_transcription)
        self.start_btn.grid(row=7, column=0, padx=20, pady=(10, 10), sticky="ew")

        self.cancel_btn = ctk.CTkButton(self, text="Cancel", state="disabled", fg_color="gray25", command=self.cancel_process)
        self.cancel_btn.grid(row=7, column=1, padx=20, pady=(10, 10), sticky="ew")

    def toggle_ui_state(self, active: bool):
        state = "normal" if active else "disabled"
        fg_color = "#1F6AA5" if active else "gray25"
        
        self.browse_btn.configure(state=state, fg_color=fg_color)
        self.out_browse_btn.configure(state=state, fg_color=fg_color)
        self.start_btn.configure(state=state, fg_color=fg_color)
        self.track_menu.configure(state=state)
        
        for btn in self.model_buttons:
            btn.configure(state=state)
            
        if active:
            self.cancel_btn.configure(state="disabled", fg_color="gray25", text="Cancel")
        else:
            self.cancel_btn.configure(state="normal", fg_color="red", hover_color="#990000", text="Cancel")

    def browse_media(self):
        path = filedialog.askopenfilename(title="Open Video or Audio File", filetypes=[("Media Files", "*.mp4 *.mkv *.avi *.mov *.mp3 *.wav *.flac")])
        if path:
            self.path_entry.delete(0, "end")
            self.path_entry.insert(0, path)
            
            out_path = os.path.splitext(path)[0] + ".vtt"
            self.out_path_entry.delete(0, "end")
            self.out_path_entry.insert(0, out_path)
            
            tracks = probe_audio_tracks(path)
            self.audio_tracks_data = tracks
            
            if tracks:
                options = [t["display_text"] for t in tracks]
                self.track_menu.configure(values=options)
                self.track_menu_var.set(options[0])
            else:
                self.track_menu.configure(values=["Default (First Track)"])
                self.track_menu_var.set("Default (First Track)")

    def browse_output(self):
        path = filedialog.asksaveasfilename(title="Save VTT File", defaultextension=".vtt", filetypes=[("VTT Files", "*.vtt")])
        if path:
            self.out_path_entry.delete(0, "end")
            self.out_path_entry.insert(0, path)

    def cancel_process(self):
        self.transcriber.cancel()
        self.cancel_btn.configure(state="disabled", text="Halting...")
        self.progress_label.configure(text="Status: Halting operations (Awaiting final write)...")

    def ui_callback(self, status_text: str | None, current_time_sec: float | None):
        if status_text:
            self.after(0, lambda text=status_text: self.progress_label.configure(text=text))
            
        if current_time_sec is not None:
            if self.total_duration > 0:
                pct = min(current_time_sec / self.total_duration, 1.0)
                status = f"Status: Transcribing ({format_timestamp(current_time_sec)} / {format_timestamp(self.total_duration)})"
                self.after(0, lambda p=pct, s=status: (self.progress_bar.set(p), self.progress_label.configure(text=s)))
            else:
                status = f"Status: Transcribing ({format_timestamp(current_time_sec)} / Unknown Total)"
                self.after(0, lambda s=status: self.progress_label.configure(text=s))

    def start_transcription(self):
        media_path = self.path_entry.get().strip()
        out_dest = self.out_path_entry.get().strip()
        
        if not os.path.isfile(media_path):
            messagebox.showerror("Error", "Invalid Media File Path")
            return
            
        if not out_dest:
            messagebox.showerror("Error", "Output destination cannot be empty")
            return

        if os.path.isdir(out_dest):
            base_name = os.path.basename(media_path)
            name_without_ext = os.path.splitext(base_name)[0]
            output_vtt = os.path.join(out_dest, name_without_ext + ".vtt")
        else:
            output_vtt = out_dest if out_dest.endswith(".vtt") else out_dest + ".vtt"
            
        output_json = os.path.splitext(output_vtt)[0] + ".json"

        # Accidental Overwrite Protection
        if os.path.exists(output_vtt) or os.path.exists(output_json):
            overwrite = messagebox.askyesno(
                "File Already Exists",
                f"Transcription files already exist at:\n{output_vtt}\n\nDo you want to overwrite them?"
            )
            if not overwrite:
                return
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(os.path.abspath(output_vtt)), exist_ok=True)
        
        # Determine track index
        chosen_audio_idx = 0
        if self.audio_tracks_data:
            selected_str = self.track_menu_var.get()
            for t in self.audio_tracks_data:
                if t["display_text"] == selected_str:
                    chosen_audio_idx = t["index"]
                    break

        self.toggle_ui_state(False)
        self.progress_bar.set(0)
        self.time_label.configure(text="Time taken: N/A")
        
        # Clear the cancel event so it can run again after being cancelled
        self.transcriber.cancel_event.clear()

        # Execute in background thread
        threading.Thread(
            target=self._process_media_thread, 
            args=(media_path, output_vtt, output_json, chosen_audio_idx), 
            daemon=True
        ).start()

    def _process_media_thread(self, media_path, output_vtt, output_json, chosen_audio_idx):
        temp_audio = os.path.splitext(media_path)[0] + "_temp_audio_extract.wav"
        start_time = time.time()
        
        try:
            self.ui_callback("Status: Analyzing File Duration...", None)
            self.total_duration = get_audio_duration(media_path)
            
            self.ui_callback(f"Status: Extracting Audio Track {chosen_audio_idx}...", None)
            extract_audio_for_whisper(media_path, temp_audio, chosen_audio_idx)
            
            if self.transcriber.cancel_event.is_set():
                return
            
            model_size = self.model_name.get()
            
            result_state = self.transcriber.transcribe(
                audio_path=temp_audio,
                output_vtt=output_vtt,
                output_json=output_json,
                model_size=model_size,
                total_duration=self.total_duration,
                progress_callback=self.ui_callback
            )
            
            elapsed = time.time() - start_time
            self.after(0, lambda e=elapsed: self.time_label.configure(text=f"Time taken: {format_duration(e)}"))
            
            if result_state == "Cancelled":
                self.ui_callback("Status: Cancelled. Partial outputs saved.", None)
            else:
                self.ui_callback("Status: Completed", None)
                self.after(0, lambda: self.progress_bar.set(1.0))
                self.after(0, lambda: messagebox.showinfo("Done", f"Files generated at:\n{output_vtt}"))
                
        except Exception as error:
            self.after(0, lambda e=error: messagebox.showerror("Error", str(e)))
        finally:
            if os.path.exists(temp_audio):
                try: os.remove(temp_audio)
                except: pass
            
            self.after(0, lambda: self.toggle_ui_state(True))
            if not self.transcriber.cancel_event.is_set():
                self.after(0, lambda: self.progress_bar.set(0))

if __name__ == "__main__":
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("dark-blue")
    app = WhisperEdgeApp()
    app.mainloop()