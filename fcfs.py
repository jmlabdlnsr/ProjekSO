"""
fcfs.py

FCFS Scheduling GUI
"""

from tkinter import *
from tkinter import ttk, messagebox, filedialog
import threading
from dataclasses import dataclass, field
from typing import List, Tuple, Optional
import matplotlib
try:
    matplotlib.use("TkAgg")
except Exception:
    pass
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

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

# ---------------- FCFS Scheduling logic ----------------
def simulate_fcfs_processes(proc_tuples: List[Tuple[str,int,int]]):
    """
    FCFS Scheduling Algorithm
    Input: list of (pid, arrival, burst)
    """
    procs = [Process(pid, at, bt) for (pid, at, bt) in proc_tuples]
    procs_sorted = sorted(procs, key=lambda p: (p.arrival, p.pid))
    
    n = len(procs)
    time_now = 0
    gantt_segments = []
    
    for proc in procs_sorted:
        if time_now < proc.arrival:
            time_now = proc.arrival
        
        proc.start_time = time_now
        proc.completion_time = time_now + proc.burst
        proc.turnaround_time = proc.completion_time - proc.arrival
        proc.waiting_time = proc.turnaround_time - proc.burst
        
        gantt_segments.append((time_now, proc.completion_time, proc.pid))
        time_now = proc.completion_time
    
    return procs, gantt_segments, time_now

# ---------------- GUI ----------------
APP_BG = "#F6F8FB"
BAR_COLOR = "#7747FD"
TEXT_COLOR = "#001858"

root = Tk()
root.title("FCFS Scheduler - Kelas A")
root.geometry("1300x760")
root.configure(bg=APP_BG)

main_frame = Frame(root, bg=APP_BG)
main_frame.pack(fill=BOTH, expand=True, padx=8, pady=8)

# Left column
left_frame = Frame(main_frame, bg=APP_BG, width=330)
left_frame.pack(side=LEFT, fill=Y, padx=6, pady=6)
left_frame.pack_propagate(False)

# Middle column
mid_frame = Frame(main_frame, bg=APP_BG, width=460)
mid_frame.pack(side=LEFT, fill=Y, padx=6, pady=6)
mid_frame.pack_propagate(False)

# Right column
right_frame = Frame(main_frame, bg=APP_BG)
right_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=6, pady=6)

# ---------------- Left: inputs + controls + results ----------------
Label(left_frame, text="➤ FCFS Scheduler", font=("Segoe UI", 16, "bold"), bg=APP_BG, fg=TEXT_COLOR).pack(pady=8)

# Input entries
inp_frame = Frame(left_frame, bg=APP_BG)
inp_frame.pack(pady=6)
Label(inp_frame, text="Arrival", bg=APP_BG).grid(row=0, column=0, padx=4, pady=4)
entry_at = Entry(inp_frame, width=8); entry_at.grid(row=0, column=1, padx=4)
Label(inp_frame, text="Burst", bg=APP_BG).grid(row=0, column=2, padx=4, pady=4)
entry_bt = Entry(inp_frame, width=8); entry_bt.grid(row=0, column=3, padx=4)

btn_add = Button(left_frame, text="➕ Add Process", bg=BAR_COLOR, fg="white", command=lambda: add_process())
btn_add.pack(fill=X, padx=12, pady=6)

# Controls
ctrl_frame = Frame(left_frame, bg=APP_BG)
ctrl_frame.pack(pady=6, fill=X)

Label(ctrl_frame, text="FCFS - Non Preemptive", bg=APP_BG, font=("Segoe UI", 10, "bold")).pack(side=LEFT, padx=6)
btn_start = Button(ctrl_frame, text="▶ Start", bg="#8bd3dd", command=lambda: threading.Thread(target=run_sim).start())
btn_start.pack(side=LEFT, padx=6)
btn_reset = Button(ctrl_frame, text="🔁 Reset", bg="#f3d2c1", command=lambda: reset_all())
btn_reset.pack(side=LEFT, padx=6)

# Gantt scale slider
scale_frame = Frame(left_frame, bg=APP_BG)
scale_frame.pack(pady=8, fill=X)
Label(scale_frame, text="Gantt scale (px/unit):", bg=APP_BG).pack(anchor=W, padx=6)
scale_var = IntVar(value=30)
scale_slider = Scale(scale_frame, from_=10, to=80, orient=HORIZONTAL, variable=scale_var)
scale_slider.pack(fill=X, padx=6)

btn_save = Button(left_frame, text="Save Gantt PNG", bg="#ffc8dd", command=lambda: save_gantt_png())
btn_save.pack(fill=X, padx=12, pady=6)

# Results area
Label(left_frame, text="Results (per-process)", bg=APP_BG, fg=TEXT_COLOR, font=("Segoe UI",11,"bold")).pack(pady=6)
res_cols = ("PID","AT","BT","ST","CT","TAT","WT")
res_tree = ttk.Treeview(left_frame, columns=res_cols, show="headings", height=8)
for c in res_cols:
    res_tree.heading(c, text=c)
    res_tree.column(c, width=45, anchor=CENTER)
res_tree.pack(fill=BOTH, expand=False, padx=8, pady=6)

avg_label = Label(left_frame, text="Avg WT: -    Avg TAT: -", bg=APP_BG, font=("Segoe UI",11,"bold"), fg=TEXT_COLOR)
avg_label.pack(pady=6)

# ---------------- Middle: process table ----------------
Label(mid_frame, text="Processes", font=("Segoe UI",13,"bold"), bg=APP_BG, fg=TEXT_COLOR).pack(pady=6)
cols = ("PID","Arrival","Burst")
tree = ttk.Treeview(mid_frame, columns=cols, show="headings", height=20)
for c,w in zip(cols, (120,120,120)):
    tree.heading(c, text=c)
    tree.column(c, width=w, anchor=CENTER)
tree.pack(fill=BOTH, expand=True, padx=6, pady=6)

mid_btn_frame = Frame(mid_frame, bg=APP_BG)
mid_btn_frame.pack(fill=X, pady=4)
btn_sample = Button(mid_btn_frame, text="Load Sample", bg="#ffc8dd", command=lambda: load_sample())
btn_sample.pack(side=LEFT, padx=6)
btn_import = Button(mid_btn_frame, text="Import CSV", bg="#ffd3b6", command=lambda: import_csv())
btn_import.pack(side=LEFT, padx=6)

# ---------------- Right: 3D Gantt ----------------
Label(right_frame, text="3D Gantt Chart", font=("Segoe UI",13,"bold"), bg=APP_BG, fg=TEXT_COLOR).pack(pady=6)
fig = plt.Figure(figsize=(7,5), dpi=100)
ax = fig.add_subplot(111, projection='3d')
fig.patch.set_facecolor(APP_BG)
canvas = FigureCanvasTkAgg(fig, master=right_frame)
canvas.get_tk_widget().pack(fill=BOTH, expand=True, padx=6, pady=6)

# ---------------- Data store ----------------
process_list: List[Tuple[str,int,int]] = []  # (pid, at, bt)

# ---------------- Helper functions ----------------
def update_treeviews():
    tree.delete(*tree.get_children())
    for pid, at, bt in process_list:
        tree.insert("", END, values=(pid, at, bt))

def add_process():
    global process_list
    try:
        at = int(entry_at.get())
        bt = int(entry_bt.get())
    except ValueError:
        messagebox.showerror("Input Error", "Arrival and Burst must be integers.")
        return
    pid = f"P{len(process_list)+1}"
    process_list.append((pid, at, bt))
    entry_at.delete(0, END); entry_bt.delete(0, END)
    update_treeviews()

def load_sample():
    global process_list
    process_list = [
        ("P1", 0, 4),
        ("P2", 1, 2), 
        ("P3", 2, 6),
        ("P4", 2, 6)
    ]
    update_treeviews()

def import_csv():
    global process_list
    path = filedialog.askopenfilename(filetypes=[("CSV files","*.csv")])
    if not path:
        return
    try:
        with open(path, newline='') as f:
            import csv
            rows = list(csv.reader(f))
            process_list = []
            for i,row in enumerate(rows, start=1):
                if len(row) >= 3:
                    pid = row[0].strip()
                    at = int(row[1]); bt = int(row[2])
                elif len(row) == 2:
                    pid = f"P{i}"
                    at = int(row[0]); bt = int(row[1])
                else:
                    continue
                process_list.append((pid, at, bt))
            update_treeviews()
    except Exception as e:
        messagebox.showerror("CSV Error", f"Failed to read CSV: {e}")

def reset_all():
    global process_list
    process_list = []
    update_treeviews()
    res_tree.delete(*res_tree.get_children())
    avg_label.config(text="Avg WT: -    Avg TAT: -")
    ax.clear()
    canvas.draw()

def render_3d_gantt(gantt_segments: List[Tuple[int,int,str]], procs_meta: List[Process], total_time: int):
    ax.clear()
    ax.set_facecolor(APP_BG)
    fig.patch.set_facecolor(APP_BG)
    
    colors = [BAR_COLOR, "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FECA57"]
    pids_order = []
    for seg in gantt_segments:
        if seg[2] not in pids_order:
            pids_order.append(seg[2])
    
    if not pids_order:
        canvas.draw()
        return
    
    y_pos = {pid: idx for idx, pid in enumerate(pids_order)}
    xs, ys, zs, dxs, dys, dzs, bar_colors = [], [], [], [], [], [], []
    
    for i, (start, end, pid) in enumerate(gantt_segments):
        duration = end - start
        xs.append(start)
        ys.append(y_pos[pid])
        zs.append(0)
        dxs.append(duration)
        dys.append(0.8)
        dzs.append(1)
        color_idx = list(y_pos.keys()).index(pid) % len(colors)
        bar_colors.append(colors[color_idx])
    
    if xs:
        ax.bar3d(xs, ys, zs, dxs, dys, dzs, 
                color=bar_colors, 
                alpha=0.8,
                shade=True,
                edgecolor='black',
                linewidth=0.5)
    
    ax.set_yticks(list(y_pos.values()))
    ax.set_yticklabels(list(y_pos.keys()))
    ax.set_xlabel("Time", labelpad=10)
    ax.set_ylabel("Process", labelpad=10)
    ax.set_zlabel("")
    
    max_time = max([seg[1] for seg in gantt_segments]) if gantt_segments else total_time
    ax.set_xlim(0, max(1, max_time))
    ax.set_ylim(-0.5, len(pids_order) - 0.5)
    ax.set_zlim(0, 1)
    ax.view_init(elev=20, azim=-60)
    ax.set_title("3D Gantt (FCFS Scheduling)", pad=20, color=TEXT_COLOR)
    ax.grid(True, alpha=0.3)
    canvas.draw()

def run_sim():
    if not process_list:
        messagebox.showwarning("No processes", "Add at least one process first.")
        return
    btn_start.config(state=DISABLED)
    btn_reset.config(state=DISABLED)
    procs_snapshot = process_list.copy()
    def worker():
        procs_meta, gantt, total_time = simulate_fcfs_processes(procs_snapshot)
        root.after(0, update_after_sim, procs_meta, gantt, total_time)
    threading.Thread(target=worker).start()

def update_after_sim(procs_meta: List[Process], gantt: List[Tuple[int,int,str]], total_time: int):
    res_tree.delete(*res_tree.get_children())
    for p in sorted(procs_meta, key=lambda x: x.pid):
        st = p.start_time if p.start_time is not None else "-"
        ct = p.completion_time if p.completion_time is not None else "-"
        tat = p.turnaround_time if p.turnaround_time is not None else "-"
        wt = p.waiting_time if p.waiting_time is not None else "-"
        res_tree.insert("", END, values=(p.pid, p.arrival, p.burst, st, ct, tat, wt))
    
    tats = [p.turnaround_time for p in procs_meta if p.turnaround_time is not None]
    wts = [p.waiting_time for p in procs_meta if p.waiting_time is not None]
    avg_tat = sum(tats)/len(tats) if tats else 0
    avg_wt = sum(wts)/len(wts) if wts else 0
    avg_label.config(text=f"Avg WT: {avg_wt:.2f}    Avg TAT: {avg_tat:.2f}")
    
    render_3d_gantt(gantt, procs_meta, total_time)
    btn_start.config(state=NORMAL)
    btn_reset.config(state=NORMAL)

def save_gantt_png():
    p = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG","*.png")], initialfile="gantt_fcfs.png")
    if not p:
        return
    fig.savefig(p, dpi=150)
    messagebox.showinfo("Saved", f"Gantt PNG saved to:\n{p}")

load_sample()

root.mainloop()


