#fcfs.py
from tkinter import *
from tkinter import ttk, messagebox, filedialog
import threading, os
from dataclasses import dataclass, field
from typing import List, Tuple, Optional
import matplotlib
try:
    matplotlib.use("TkAgg")
except Exception:
    pass
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

# ---------------- Data class ----------------
@dataclass
class Process:
    pid: str
    arrival: int
    burst: int
    remaining: int = field(init=False)
    start_time: Optional[int] = None
    completion_time: Optional[int] = None
    waiting_time: Optional[int] = None
    turnaround_time: Optional[int] = None

    def __post_init__(self):
        self.remaining = self.burst

# ---------------- Scheduling logic ----------------
def simulate_fcfs(proc_tuples: List[Tuple[str,int,int]]):
    procs = [Process(pid, at, bt) for (pid, at, bt) in proc_tuples]
    procs.sort(key=lambda p: p.arrival)
    time_now = 0
    gantt = []

    for p in procs:
        if time_now < p.arrival:
            time_now = p.arrival
        p.start_time = time_now
        gantt.append((time_now, time_now + p.burst, p.pid))
        time_now += p.burst
        p.completion_time = time_now
        p.turnaround_time = p.completion_time - p.arrival
        p.waiting_time = p.start_time - p.arrival
    return procs, gantt, time_now

# ---------------- UI constants ----------------
APP_BG = "#69259c"
BAR_COLOR = "#fb47b2"
TEXT_COLOR = "#ffddff"

# ---------------- FCFSPage ----------------
class FCFSPage(Frame):
    def __init__(self, parent, app=None):
        super().__init__(parent, bg=APP_BG)
        self.pack(fill=BOTH, expand=True)
        self.app = app

        # Prepare matplotlib figure
        self.fig = plt.Figure(figsize=(7,5), dpi=100)
        self.ax = self.fig.add_subplot(111, projection='3d')
        self.fig.patch.set_facecolor(APP_BG)

        # Data
        self.process_list: List[Tuple[str,int,int]] = []

        # Layout: three columns
        main_frame = Frame(self, bg=APP_BG)
        main_frame.pack(fill=BOTH, expand=True, padx=8, pady=8)

        # left
        left_frame = Frame(main_frame, bg=APP_BG, width=330)
        left_frame.pack(side=LEFT, fill=Y, padx=6, pady=6)
        left_frame.pack_propagate(False)

        # mid
        mid_frame = Frame(main_frame, bg=APP_BG, width=460)
        mid_frame.pack(side=LEFT, fill=Y, padx=6, pady=6)
        mid_frame.pack_propagate(False)

        # right
        right_frame = Frame(main_frame, bg=APP_BG)
        right_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=6, pady=6)

        # Left widgets
        Label(left_frame, text="FCFS Scheduler", font=("Segoe UI", 16, "bold"), bg=APP_BG, fg=TEXT_COLOR).pack(pady=8)

        inp_frame = Frame(left_frame, bg=APP_BG)
        inp_frame.pack(pady=6)
        Label(inp_frame, text="Arrival", bg=APP_BG).grid(row=0, column=0, padx=4, pady=4)
        self.entry_at = Entry(inp_frame, width=6); self.entry_at.grid(row=0, column=1, padx=4)
        Label(inp_frame, text="Burst", bg=APP_BG).grid(row=0, column=2, padx=4, pady=4)
        self.entry_bt = Entry(inp_frame, width=6); self.entry_bt.grid(row=0, column=3, padx=4)

        self.btn_add = Button(left_frame, text="➕ Add Process", bg=BAR_COLOR, fg="white", command=self.add_process)
        self.btn_add.pack(fill=X, padx=12, pady=6)

        ctrl_frame = Frame(left_frame, bg=APP_BG)
        ctrl_frame.pack(pady=6, fill=X)
        self.btn_start = Button(ctrl_frame, text="▶ Start", bg="#f2d6e4", command=lambda: threading.Thread(target=self.run_sim).start())
        self.btn_start.pack(side=LEFT, padx=6)
        self.btn_reset = Button(ctrl_frame, text="🔁 Reset", bg="#f2d6ef", command=self.reset_all)
        self.btn_reset.pack(side=LEFT, padx=6)

        scale_frame = Frame(left_frame, bg=APP_BG)
        scale_frame.pack(pady=8, fill=X)
        Label(scale_frame, text="Gantt scale (px/unit):", bg=APP_BG).pack(anchor=W, padx=6)
        self.scale_var = IntVar(value=30)
        self.scale_slider = Scale(scale_frame, from_=10, to=80, orient=HORIZONTAL, variable=self.scale_var)
        self.scale_slider.pack(fill=X, padx=6)

        self.btn_save = Button(left_frame, text="Save Gantt PNG", fg="white", bg="#fb47b2", command=self.save_gantt_png)
        self.btn_save.pack(fill=X, padx=12, pady=6)

        Label(left_frame, text="Results (per-process)", bg=APP_BG, fg=TEXT_COLOR, font=("Segoe UI",11,"bold")).pack(pady=6)
        res_cols = ("PID","AT","BT","ST","CT","TAT","WT")
        self.res_tree = ttk.Treeview(left_frame, columns=res_cols, show="headings", height=8)
        for c in res_cols:
            self.res_tree.heading(c, text=c)
            self.res_tree.column(c, width=36, anchor=CENTER)
        self.res_tree.pack(fill=BOTH, expand=False, padx=8, pady=6)

        self.avg_label = Label(left_frame, text="Avg WT: -    Avg TAT: -", bg=APP_BG, font=("Segoe UI",11,"bold"), fg=TEXT_COLOR)
        self.avg_label.pack(pady=6)

        # Middle: process list + back button
        Label(mid_frame, text="Processes", font=("Segoe UI",13,"bold"), bg=APP_BG, fg=TEXT_COLOR).pack(pady=6)
        cols = ("PID","Arrival","Burst")
        self.tree = ttk.Treeview(mid_frame, columns=cols, show="headings", height=20)
        for c,w in zip(cols, (80,80,80)):
            self.tree.heading(c, text=c)
            self.tree.column(c, width=w, anchor=CENTER)
        self.tree.pack(fill=BOTH, expand=True, padx=6, pady=6)

        mid_btn_frame = Frame(mid_frame, bg=APP_BG)
        mid_btn_frame.pack(fill=X, pady=4)
        self.btn_back = Button(mid_btn_frame, text="↩ Back", bg="#f2d6ef", command=self._on_back)
        self.btn_back.pack(side=LEFT, padx=6)

        # Right: 3D Gantt
        Label(right_frame, text="3D Gantt Chart", font=("Segoe UI",13,"bold"), bg=APP_BG, fg=TEXT_COLOR).pack(pady=6)
        self.canvas = FigureCanvasTkAgg(self.fig, master=right_frame)
        self.canvas.get_tk_widget().pack(fill=BOTH, expand=True, padx=6, pady=6)

        self.load_sample()

    # ----- helpers -----
    def update_treeviews(self):
        self.tree.delete(*self.tree.get_children())
        for pid, at, bt in self.process_list:
            self.tree.insert("", END, values=(pid, at, bt))

    def add_process(self):
        try:
            at = int(self.entry_at.get())
            bt = int(self.entry_bt.get())
        except ValueError:
            messagebox.showerror("Input Error", "Arrival and Burst must be integers.")
            return
        pid = f"P{len(self.process_list)+1}"
        self.process_list.append((pid, at, bt))
        self.entry_at.delete(0, END); self.entry_bt.delete(0, END)
        self.update_treeviews()

    def load_sample(self):
        self.process_list = [("P1",0,4),("P2",1,3),("P3",2,5)]
        self.update_treeviews()

    def reset_all(self):
        self.process_list = []
        self.update_treeviews()
        self.res_tree.delete(*self.res_tree.get_children())
        self.avg_label.config(text="Avg WT: -    Avg TAT: -")
        self.ax.clear()
        self.canvas.draw()

    # ----- Gantt rendering -----
    def render_3d_gantt(self, gantt_segments: List[Tuple[int,int,str]], procs_meta: List[Process], total_time: int):
        ax = self.ax
        fig = self.fig
        ax.clear()
        ax.set_facecolor(APP_BG)
        fig.patch.set_facecolor(APP_BG)
        y_pos = {pid: idx for idx,pid in enumerate([seg[2] for seg in gantt_segments])}
        xs=[]; ys=[]; zs=[]; dxs=[]; dys=[]; dzs=[]; colors=[]
        for start,end,pid in gantt_segments:
            dur = end - start
            xs.append(start); ys.append(y_pos[pid]); zs.append(0)
            dxs.append(dur); dys.append(0.6); dzs.append(1)
            colors.append(BAR_COLOR)
        if xs:
            ax.bar3d(xs, ys, zs, dxs, dys, dzs, color=colors, shade=True, edgecolor="#222222", linewidth=0.2)
        ax.set_yticks(list(y_pos.values()))
        ax.set_yticklabels(list(y_pos.keys()))
        ax.set_xlabel("Time")
        ax.set_zlim(0,1.5)
        ax.set_zlabel("")
        ax.set_title("3D Gantt (FCFS Scheduling)", color=TEXT_COLOR)
        ax.view_init(elev=20, azim=-60)
        step = max(1, max([seg[1] for seg in gantt_segments]+[1])//10)
        ax.set_xticks(range(0, max([seg[1] for seg in gantt_segments]+[1])+1, step))
        self.canvas.draw()

    # ----- simulate -----
    def run_sim(self):
        if not self.process_list:
            messagebox.showwarning("No processes", "Add at least one process first.")
            return
        self.btn_start.config(state=DISABLED)
        self.btn_reset.config(state=DISABLED)
        snapshot = self.process_list.copy()
        def worker():
            procs_meta, gantt, total_time = simulate_fcfs(snapshot)
            self.after(0, self.update_after_sim, procs_meta, gantt, total_time)
        threading.Thread(target=worker).start()

    def update_after_sim(self, procs_meta: List[Process], gantt: List[Tuple[int,int,str]], total_time: int):
        self.res_tree.delete(*self.res_tree.get_children())
        for p in procs_meta:
            st = p.start_time if p.start_time is not None else "-"
            ct = p.completion_time if p.completion_time is not None else "-"
            tat = p.turnaround_time if p.turnaround_time is not None else "-"
            wt = p.waiting_time if p.waiting_time is not None else "-"
            self.res_tree.insert("", END, values=(p.pid, p.arrival, p.burst, st, ct, tat, wt))
        tats = [p.turnaround_time for p in procs_meta if p.turnaround_time is not None]
        wts = [p.waiting_time for p in procs_meta if p.waiting_time is not None]
        avg_tat = sum(tats)/len(tats) if tats else 0
        avg_wt = sum(wts)/len(wts) if wts else 0
        self.avg_label.config(text=f"Avg WT: {avg_wt:.2f}    Avg TAT: {avg_tat:.2f}")
        self.render_3d_gantt(gantt, procs_meta, total_time)
        self.btn_start.config(state=NORMAL)
        self.btn_reset.config(state=NORMAL)

    def save_gantt_png(self):
        p = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG","*.png")], initialfile="gantt_fcfs.png")
        if not p:
            return
        try:
            self.fig.savefig(p, dpi=150)
            messagebox.showinfo("Saved", f"Gantt PNG saved to:\n{p}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save PNG: {e}")

    # ----- back handling -----
    def _on_back(self):
        if getattr(self, "app", None):
            try:
                if hasattr(self.app, "_mode_page"):
                    self.app._mode_page()
                else:
                    self.app._home_page()
            except Exception:
                pass
        else:
            top = self.winfo_toplevel()
            try:
                top.destroy()
            except:
                pass

# ---------------- standalone fallback ----------------
def main_standalone():
    root = Tk()
    root.title("FCFS Scheduler - Kelompok 4 AB")
    root.geometry("1300x760")
    FCFSPage(root)
    root.mainloop()

if __name__ == "__main__":
    main_standalone()
