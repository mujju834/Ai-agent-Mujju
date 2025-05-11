#!/usr/bin/env python3
import sys
import threading
import asyncio
import tkinter as tk
from tkinter import scrolledtext, ttk
from PIL import Image, ImageTk

from ai_agent import run_autonomous

class BrowserUseGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("BrowserUse Agent Demo")
        self.geometry("1024x768")
        self._build_ui()

    def _build_ui(self):
        # Top frame: input + run button + headless toggle
        frm = ttk.Frame(self)
        frm.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(frm, text="Task:").pack(side=tk.LEFT)
        self.task_entry = ttk.Entry(frm, width=70)
        self.task_entry.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        # Headless checkbox (unchecked => show browser)
        self.headless_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(frm, text="Headless", variable=self.headless_var).pack(side=tk.LEFT, padx=5)

        run_btn = ttk.Button(frm, text="Run", command=self._on_run)
        run_btn.pack(side=tk.LEFT)

        # Middle: logs
        self.log_widget = scrolledtext.ScrolledText(self, height=12)
        self.log_widget.pack(fill=tk.BOTH, expand=False, padx=10, pady=5)

        # Bottom: screenshot preview
        self.preview = ttk.Label(self)
        self.preview.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    def _on_run(self):
        task = self.task_entry.get().strip()
        if not task:
            self._log("⚠️ Please enter a task.\n")
            return
        self.log_widget.delete("1.0", tk.END)
        self.preview.config(image="")
        # Launch in background thread
        threading.Thread(target=self._run_task, args=(task,), daemon=True).start()

    def _run_task(self, task: str):
        show = not self.headless_var.get()
        self._log(f"🔍 Starting task (headless={not show}): {task}\n\n")
        try:
            results = asyncio.run(run_autonomous(task, headless=not show, slow_mo=300))
        except Exception as e:
            self._log(f"[Error] {e}\n")
            return

        for res in results:
            if "screenshot" in res:
                path = res["screenshot"]
                self._log(f"📸 Screenshot saved: {path}\n")
                self._show_image(path)
            if "extracted_text" in res:
                txt = res["extracted_text"]
                self._log(f"✂️ Extracted text: {txt}\n")

        self._log("\n✅ Task complete!\n")

    def _log(self, msg: str):
        self.log_widget.insert(tk.END, msg)
        self.log_widget.see(tk.END)

    def _show_image(self, path: str):
        try:
            img = Image.open(path)
            # fit thumbnail into preview area
            img.thumbnail((self.preview.winfo_width(), self.preview.winfo_height()))
            photo = ImageTk.PhotoImage(img)
            self.preview.image = photo
            self.preview.config(image=photo)
        except Exception as e:
            self._log(f"[Error displaying image] {e}\n")

if __name__ == "__main__":
    app = BrowserUseGUI()
    app.mainloop()
