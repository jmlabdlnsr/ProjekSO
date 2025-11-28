#priority.py
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
@dataclass(order=True)
class Process:
    sort_index: tuple = field(init=False, repr=False)
    pid: str
    arrival: int
    burst: int
    priority: int
    remaining: int = field(init=False)
    start_time: Optional[int] = None
    completion_time: Optional[int] = None
    waiting_time: Optional[int] = None
    turnaround_time: Optional[int] = None

    def __post_init__(self):
        self.remaining = self.burst
        self.sort_index = (self.priority, self.arrival, self.pid)

# ---------------- Scheduling logic ----------------
def simulate_priority_processes(proc_tuples: List[Tuple[str,int,int,int]], preemptive: bool=False):
    procs = [Process(pid, at, bt, pr) for (pid, at, bt, pr) in proc_tuples]
    procs_sorted = sorted(procs, key=lambda p: (p.arrival, p.priority, p.pid))
    n = len(procs)
    time_now = 0
    completed = 0
    ready: List[Process] = []
    arrival_idx = 0
    gantt_marks = []

    def add_arrivals(t):
        nonlocal arrival_idx
        while arrival_idx < n and procs_sorted[arrival_idx].arrival <= t:
            ready.append(procs_sorted[arrival_idx])
            arrival_idx += 1

    add_arrivals(time_now)
    last_pid = None

    if n == 0:
        return procs, [], 0

    while completed < n:
        if not ready:
            if arrival_idx < n:
                time_now = procs_sorted[arrival_idx].arrival
                add_arrivals(time_now)
                continue
            else:
                break

        ready.sort(key=lambda p: (p.priority, p.arrival, p.pid))
        cur = ready[0]
        if cur.start_time is None:
            cur.start_time = time_now

        if last_pid != cur.pid:
            gantt_marks.append((time_now, cur.pid))
            last_pid = cur.pid

        run_len = 1 if preemptive else cur.remaining
        ran = 0
        while ran < run_len:
            time_now += 1
            cur.remaining -= 1
            ran += 1
            add_arrivals(time_now)
            if preemptive and cur.remaining > 0 and ready:
                ready.sort(key=lambda p: (p.priority, p.arrival, p.pid))
                if ready[0].pid != cur.pid:
                    break
        if cur.remaining == 0:
            cur.completion_time = time_now
            cur.turnaround_time = cur.completion_time - cur.arrival
            cur.waiting_time = cur.turnaround_time - cur.burst
            if cur in ready:
                ready.remove(cur)
            completed += 1

    merged = []
    if gantt_marks:
        for i, (s, pid) in enumerate(gantt_marks):
            if i == 0:
                merged.append([s, None, pid])
            else:
                merged[-1][1] = s
                merged.append([s, None, pid])
        merged[-1][1] = time_now
    gantt = [(m[0], m[1], m[2]) for m in merged]

    return procs, gantt, time_now

# ---------------- UI constants ----------------
APP_BG = "#69259c"
BAR_COLOR = "#fb47b2"
TEXT_COLOR = "#ffddff"

# ---------------- PriorityPage ----------------
class PriorityPage(Frame):
    def __init__(self, parent, app=None):
        super().__init__(parent, bg=APP_BG)
        self.pack(fill=BOTH, expand=True)
        self.app = app

        # Prepare matplotlib figure
        self.fig = plt.Figure(figsize=(7,5), dpi=100)
        self.ax = self.fig.add_subplot(111, projection='3d')
        self.fig.patch.set_facecolor(APP_BG)

        # Data
        self.process_list: List[Tuple[str,int,int,int]] = []

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
        Label(left_frame, text="Priority Scheduler", font=("Segoe UI", 16, "bold"), bg=APP_BG, fg=TEXT_COLOR).pack(pady=8)

        inp_frame = Frame(left_frame, bg=APP_BG)
        inp_frame.pack(pady=6)
        Label(inp_frame, text="Arrival", bg=APP_BG).grid(row=0, column=0, padx=4, pady=4)
        self.entry_at = Entry(inp_frame, width=6); self.entry_at.grid(row=0, column=1, padx=4)
        Label(inp_frame, text="Burst", bg=APP_BG).grid(row=0, column=2, padx=4, pady=4)
        self.entry_bt = Entry(inp_frame, width=6); self.entry_bt.grid(row=0, column=3, padx=4)
        Label(inp_frame, text="Priority", bg=APP_BG).grid(row=0, column=4, padx=4, pady=4)
        self.entry_pr = Entry(inp_frame, width=6); self.entry_pr.grid(row=0, column=5, padx=4)

        self.btn_add = Button(left_frame, text="➕ Add Process", bg=BAR_COLOR, fg="white", command=self.add_process)
        self.btn_add.pack(fill=X, padx=12, pady=6)

        ctrl_frame = Frame(left_frame, bg=APP_BG)
        ctrl_frame.pack(pady=6, fill=X)

        self.preempt_var = BooleanVar(value=False)
        self.chk_preempt = Checkbutton(ctrl_frame, text="Preemptive", variable=self.preempt_var, bg=APP_BG)
        self.chk_preempt.pack(side=LEFT, padx=6)

        self.btn_start = Button(ctrl_frame, text="▶ Start", bg="#f2d6ef", command=lambda: threading.Thread(target=self.run_sim).start())
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
        res_cols = ("PID","AT","BT","PR","ST","CT","TAT","WT")
        self.res_tree = ttk.Treeview(left_frame, columns=res_cols, show="headings", height=8)
        for c in res_cols:
            self.res_tree.heading(c, text=c)
            self.res_tree.column(c, width=36, anchor=CENTER)
        self.res_tree.pack(fill=BOTH, expand=False, padx=8, pady=6)

        self.avg_label = Label(left_frame, text="Avg WT: -    Avg TAT: -", bg=APP_BG, font=("Segoe UI",11,"bold"), fg=TEXT_COLOR)
        self.avg_label.pack(pady=6)

        # Middle: process list + back button
        Label(mid_frame, text="Processes", font=("Segoe UI",13,"bold"), bg=APP_BG, fg=TEXT_COLOR).pack(pady=6)
        cols = ("PID","Arrival","Burst","Priority")
        self.tree = ttk.Treeview(mid_frame, columns=cols, show="headings", height=20)
        for c,w in zip(cols, (80,80,80,80)):
            self.tree.heading(c, text=c)
            self.tree.column(c, width=w, anchor=CENTER)
        self.tree.pack(fill=BOTH, expand=True, padx=6, pady=6)

        mid_btn_frame = Frame(mid_frame, bg=APP_BG)
        mid_btn_frame.pack(fill=X, pady=4)
        # Back button (returns to main launcher mode page)
        self.btn_back = Button(mid_btn_frame, text="↩ Back", bg="#f2d6ef", command=self._on_back)
        self.btn_back.pack(side=LEFT, padx=6)

        # Right: 3D Gantt
        Label(right_frame, text="3D Gantt Chart", font=("Segoe UI",13,"bold"), bg=APP_BG, fg=TEXT_COLOR).pack(pady=6)
        self.canvas = FigureCanvasTkAgg(self.fig, master=right_frame)
        self.canvas.get_tk_widget().pack(fill=BOTH, expand=True, padx=6, pady=6)

        # start with example data
        self.load_sample()

    # ----- helpers -----
    def update_treeviews(self):
        self.tree.delete(*self.tree.get_children())
        for pid, at, bt, pr in self.process_list:
            self.tree.insert("", END, values=(pid, at, bt, pr))

    def add_process(self):
        try:
            at = int(self.entry_at.get())
            bt = int(self.entry_bt.get())
            pr = int(self.entry_pr.get())
        except ValueError:
            messagebox.showerror("Input Error", "Arrival, Burst, Priority must be integers.")
            return
        pid = f"P{len(self.process_list)+1}"
        self.process_list.append((pid, at, bt, pr))
        self.entry_at.delete(0, END); self.entry_bt.delete(0, END); self.entry_pr.delete(0, END)
        self.update_treeviews()

    def load_sample(self):
        # sample used when first opened; user can add real processes manually
        self.process_list = [("P1",0,4,2),("P2",1,2,1),("P3",2,6,3)]
        self.update_treeviews()

    def import_csv(self):
        path = filedialog.askopenfilename(filetypes=[("CSV files","*.csv"),("All files","*.*")])
        if not path:
            return
        try:
            with open(path, newline='') as f:
                import csv
                rows = list(csv.reader(f))
                if not rows:
                    messagebox.showerror("CSV Error", "Empty CSV")
                    return
                header = rows[0]
                start_idx = 0
                if any(not cell.strip().isdigit() for cell in header[1:]):
                    start_idx = 1
                pl = []
                for i,row in enumerate(rows[start_idx:], start=1):
                    if len(row) >= 4:
                        pid = row[0].strip()
                        at = int(row[1]); bt = int(row[2]); pr = int(row[3])
                    elif len(row) == 3:
                        pid = f"P{i}"
                        at = int(row[0]); bt = int(row[1]); pr = int(row[2])
                    else:
                        continue
                    pl.append((pid, at, bt, pr))
                self.process_list = pl
                self.update_treeviews()
        except Exception as e:
            messagebox.showerror("CSV Error", f"Failed to read CSV: {e}")

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
        pids_order = []
        for seg in gantt_segments:
            if seg[2] not in pids_order:
                pids_order.append(seg[2])
        if not pids_order:
            pids_order = [p.pid for p in procs_meta]
        y_pos = {pid: idx for idx,pid in enumerate(pids_order)}
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
        ax.set_title("3D Gantt (Priority Scheduling)", color=TEXT_COLOR)
        ax.view_init(elev=20, azim=-60)
        if gantt_segments:
            max_t = max(seg[1] for seg in gantt_segments)
        else:
            max_t = total_time
        # safe xticks
        step = max(1, max(1, max_t//10))
        ax.set_xticks(range(0, max(1, max_t+1), step))
        self.canvas.draw()

    # ----- simulate -----
    def run_sim(self):
        if not self.process_list:
            messagebox.showwarning("No processes", "Add at least one process first.")
            return
        self.btn_start.config(state=DISABLED)
        self.btn_reset.config(state=DISABLED)
        snapshot = self.process_list.copy()
        preempt = self.preempt_var.get()
        def worker():
            procs_meta, gantt, total_time = simulate_priority_processes(snapshot, preemptive=preempt)
            self.after(0, self.update_after_sim, procs_meta, gantt, total_time)
        threading.Thread(target=worker).start()

    def update_after_sim(self, procs_meta: List[Process], gantt: List[Tuple[int,int,str]], total_time: int):
        self.res_tree.delete(*self.res_tree.get_children())
        for p in sorted(procs_meta, key=lambda x: x.pid):
            st = p.start_time if p.start_time is not None else "-"
            ct = p.completion_time if p.completion_time is not None else "-"
            tat = p.turnaround_time if p.turnaround_time is not None else "-"
            wt = p.waiting_time if p.waiting_time is not None else ""
            self.res_tree.insert("", END, values=(p.pid, p.arrival, p.burst, p.priority, st, ct, tat, wt))
        tats = [p.turnaround_time for p in procs_meta if p.turnaround_time is not None]
        wts = [p.waiting_time for p in procs_meta if p.waiting_time is not None]
        avg_tat = sum(tats)/len(tats) if tats else 0
        avg_wt = sum(wts)/len(wts) if wts else 0
        self.avg_label.config(text=f"Avg WT: {avg_wt:.2f}    Avg TAT: {avg_tat:.2f}")
        self.render_3d_gantt(gantt, procs_meta, total_time)
        self.btn_start.config(state=NORMAL)
        self.btn_reset.config(state=NORMAL)

    def save_gantt_png(self):
        p = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG","*.png")], initialfile="gantt_priority.png")
        if not p:
            return
        try:
            self.fig.savefig(p, dpi=150)
            messagebox.showinfo("Saved", f"Gantt PNG saved to:\n{p}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save PNG: {e}")

    # ----- back handling -----
    def _on_back(self):
        # If embedded in launcher, call its _mode_page (or show_page)
        if getattr(self, "app", None):
            try:
                if hasattr(self.app, "_mode_page"):
                    self.app._mode_page()
                else:
                    self.app._home_page()
            except Exception:
                pass
        else:
            # standalone fallback: close top-level window
            top = self.winfo_toplevel()
            try:
                top.destroy()
            except:
                pass

# ---------------- standalone fallback ----------------
def main_standalone():
    root = Tk()
    root.title("Priority Scheduler - Kelompok 4 AB")
    root.geometry("1300x760")
    PriorityPage(root)
    root.mainloop()

if __name__ == "__main__":
    main_standalone()
