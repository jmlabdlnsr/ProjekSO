"""
main.py — Single Start Button → Algorithm Selection Screen

When user clicks "Start", a new window opens showing 4 large buttons:
- FCFS
- SJF
- Round Robin
- Priority

No extra text, no description.
"""

import tkinter as tk
from tkinter import ttk
import subprocess
import sys
import os

# Helper to open external script
def open_script(script_name):
    python_executable = sys.executable
    script_path = os.path.join(os.path.dirname(__file__), script_name)
    subprocess.Popen([python_executable, script_path])


# ---------------- HOME WINDOW ----------------
def open_selection_window():
    sel = tk.Toplevel()
    sel.title("Select Algorithm")
    sel.geometry("420x320")
    sel.configure(bg="#F5F5F5")

    frame = tk.Frame(sel, bg="#F5F5F5")
    frame.pack(expand=True)

    # Buttons without text clutter
    ttk.Button(frame, text="FCFS", width=25,
               command=lambda: open_script("fcfs.py")).pack(pady=12)
    ttk.Button(frame, text="SJF", width=25,
               command=lambda: open_script("sjf.py")).pack(pady=12)
    ttk.Button(frame, text="Round Robin", width=25,
               command=lambda: open_script("rr.py")).pack(pady=12)
    ttk.Button(frame, text="Priority", width=25,
               command=lambda: open_script("priority.py")).pack(pady=12)


# Main window
root = tk.Tk()
root.title("CPU Scheduling")
root.geometry("400x240")
root.configure(bg="#F5F5F5")

start_btn = ttk.Button(root, text="Start", width=30, command=open_selection_window)
start_btn.pack(expand=True)

root.mainloop()
