from tkinter import *
from tkinter import ttk, messagebox, filedialog
import threading, time, os
from dataclasses import dataclass, field
from typing import List, Tuple, Optional
import matplotlib
# ensure TkAgg backend for embedding
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
    """
    Input: list of (pid, arrival, burst, priority)
    Returns:
        - procs: list of Process objects with metrics filled
        - gantt_segments: list of (start, end, pid)
    """
    # Create Process objects (deep-ish copy)
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

    # If no processes, return early
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

        # choose by priority (lower number = higher priority)
        ready.sort(key=lambda p: (p.priority, p.arrival, p.pid))
        cur = ready[0]
        if cur.start_time is None:
            cur.start_time = time_now

        if last_pid != cur.pid:
            gantt_marks.append((time_now, cur.pid))
            last_pid = cur.pid

        # decide run length
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
                    # preempt now
                    break
        if cur.remaining == 0:
            cur.completion_time = time_now
            cur.turnaround_time = cur.completion_time - cur.arrival
            cur.waiting_time = cur.turnaround_time - cur.burst
            if cur in ready:
                ready.remove(cur)
            completed += 1

    # build gantt segments merged
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

# ---------------- GUI ----------------
APP_BG = "#F6F8FB"
BAR_COLOR = "#7747FD"
TEXT_COLOR = "#001858"

root = Tk()
root.title("Priority Scheduler - Kelas A ")
root.geometry("1300x760")
root.configure(bg=APP_BG)

# Main paned layout: three columns
main_frame = Frame(root, bg=APP_BG)
main_frame.pack(fill=BOTH, expand=True, padx=8, pady=8)

# Left column frame (width ~ 25%)
left_frame = Frame(main_frame, bg=APP_BG, width=330)
left_frame.pack(side=LEFT, fill=Y, padx=6, pady=6)
left_frame.pack_propagate(False)

# Middle column (process table) - ~ 35%
mid_frame = Frame(main_frame, bg=APP_BG, width=460)
mid_frame.pack(side=LEFT, fill=Y, padx=6, pady=6)
mid_frame.pack_propagate(False)

# Right column (3D Gantt) - ~ remaining width
right_frame = Frame(main_frame, bg=APP_BG)
right_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=6, pady=6)

# ---------------- Left: inputs + controls + results ----------------
Label(left_frame, text="➤ Priority Scheduler", font=("Segoe UI", 16, "bold"), bg=APP_BG, fg=TEXT_COLOR).pack(pady=8)

# Input entries
inp_frame = Frame(left_frame, bg=APP_BG)
inp_frame.pack(pady=6)
Label(inp_frame, text="Arrival", bg=APP_BG).grid(row=0, column=0, padx=4, pady=4)
entry_at = Entry(inp_frame, width=6); entry_at.grid(row=0, column=1, padx=4)
Label(inp_frame, text="Burst", bg=APP_BG).grid(row=0, column=2, padx=4, pady=4)
entry_bt = Entry(inp_frame, width=6); entry_bt.grid(row=0, column=3, padx=4)
Label(inp_frame, text="Priority", bg=APP_BG).grid(row=0, column=4, padx=4, pady=4)
entry_pr = Entry(inp_frame, width=6); entry_pr.grid(row=0, column=5, padx=4)

btn_add = Button(left_frame, text="➕ Add Process", bg=BAR_COLOR, fg="white", command=lambda: add_process())
btn_add.pack(fill=X, padx=12, pady=6)

# Controls
ctrl_frame = Frame(left_frame, bg=APP_BG)
ctrl_frame.pack(pady=6, fill=X)

preempt_var = BooleanVar(value=False)
chk_preempt = Checkbutton(ctrl_frame, text="Preemptive", variable=preempt_var, bg=APP_BG)
chk_preempt.pack(side=LEFT, padx=6)

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

# Save PNG button
btn_save = Button(left_frame, text="Save Gantt PNG", bg="#ffc8dd", command=lambda: save_gantt_png())
btn_save.pack(fill=X, padx=12, pady=6)

# Results area (Treeview for TAT/WT)
Label(left_frame, text="Results (per-process)", bg=APP_BG, fg=TEXT_COLOR, font=("Segoe UI",11,"bold")).pack(pady=6)
res_cols = ("PID","AT","BT","PR","ST","CT","TAT","WT")
res_tree = ttk.Treeview(left_frame, columns=res_cols, show="headings", height=8)
for c in res_cols:
    res_tree.heading(c, text=c)
    res_tree.column(c, width=36, anchor=CENTER)
res_tree.pack(fill=BOTH, expand=False, padx=8, pady=6)

avg_label = Label(left_frame, text="Avg WT: -    Avg TAT: -", bg=APP_BG, font=("Segoe UI",11,"bold"), fg=TEXT_COLOR)
avg_label.pack(pady=6)

# ---------------- Middle: process table ----------------
Label(mid_frame, text="Processes", font=("Segoe UI",13,"bold"), bg=APP_BG, fg=TEXT_COLOR).pack(pady=6)
cols = ("PID","Arrival","Burst","Priority")
tree = ttk.Treeview(mid_frame, columns=cols, show="headings", height=20)
for c,w in zip(cols, (80,80,80,80)):
    tree.heading(c, text=c)
    tree.column(c, width=w, anchor=CENTER)
tree.pack(fill=BOTH, expand=True, padx=6, pady=6)

# Buttons under table: load sample & import CSV
mid_btn_frame = Frame(mid_frame, bg=APP_BG)
mid_btn_frame.pack(fill=X, pady=4)
btn_sample = Button(mid_btn_frame, text="Load Sample", bg="#ffc8dd", command=lambda: load_sample())
btn_sample.pack(side=LEFT, padx=6)
btn_import = Button(mid_btn_frame, text="Import CSV", bg="#ffd3b6", command=lambda: import_csv())
btn_import.pack(side=LEFT, padx=6)

# ---------------- Right: 3D Gantt (matplotlib) ----------------
Label(right_frame, text="3D Gantt Chart", font=("Segoe UI",13,"bold"), bg=APP_BG, fg=TEXT_COLOR).pack(pady=6)
fig = plt.Figure(figsize=(7,5), dpi=100)
ax = fig.add_subplot(111, projection='3d')
fig.patch.set_facecolor(APP_BG)
canvas = FigureCanvasTkAgg(fig, master=right_frame)
canvas.get_tk_widget().pack(fill=BOTH, expand=True, padx=6, pady=6)

# ---------------- Data store ----------------
process_list: List[Tuple[str,int,int,int]] = []  # (pid, at, bt, pr)

# ---------------- Helper functions ----------------
def update_treeviews():
    # middle table
    tree.delete(*tree.get_children())
    for pid, at, bt, pr in process_list:
        tree.insert("", END, values=(pid, at, bt, pr))
    # results tree will be updated after simulation

def add_process():
    global process_list
    try:
        at = int(entry_at.get())
        bt = int(entry_bt.get())
        pr = int(entry_pr.get())
    except ValueError:
        messagebox.showerror("Input Error", "Arrival, Burst, Priority must be integers.")
        return
    pid = f"P{len(process_list)+1}"
    process_list.append((pid, at, bt, pr))
    entry_at.delete(0, END); entry_bt.delete(0, END); entry_pr.delete(0, END)
    update_treeviews()

def load_sample():
    global process_list
    process_list = [("P1",0,4,2),("P2",1,2,1),("P3",2,6,3)]
    update_treeviews()

def import_csv():
    global process_list
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
            process_list = []
            for i,row in enumerate(rows[start_idx:], start=1):
                if len(row) >= 4:
                    pid = row[0].strip()
                    at = int(row[1]); bt = int(row[2]); pr = int(row[3])
                elif len(row) == 3:
                    pid = f"P{i}"
                    at = int(row[0]); bt = int(row[1]); pr = int(row[2])
                else:
                    continue
                process_list.append((pid, at, bt, pr))
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

# ---------------- Rendering 3D Gantt ----------------
def render_3d_gantt(gantt_segments: List[Tuple[int,int,str]], procs_meta: List[Process], total_time: int):
    """
    Render the 3D Gantt in the FCFS-style from your example:
    - nicer color set (one color per process),
    - clearer axes limits and labels,
    - consistent bar widths and slight transparency,
    - uses ax.bar3d with edgecolor and alpha.
    """
    ax.clear()
    ax.set_facecolor(APP_BG)
    fig.patch.set_facecolor(APP_BG)

    # color palette for processes (will cycle)
    colors = [BAR_COLOR, "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FECA57", "#B28DFF", "#FFA8A8"]

    # build order of PIDs appearing in gantt (preserve appearance order)
    pids_order = []
    for seg in gantt_segments:
        if seg[2] not in pids_order:
            pids_order.append(seg[2])

    # safety: if gantt empty, show nothing
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
        # use alpha and edge styling to match fcfs example
        ax.bar3d(xs, ys, zs, dxs, dys, dzs,
                 color=bar_colors,
                 alpha=0.9,
                 shade=True,
                 edgecolor='black',
                 linewidth=0.4)

    # labels and ticks
    ax.set_yticks(list(y_pos.values()))
    ax.set_yticklabels(list(y_pos.keys()))
    ax.set_xlabel("Time", labelpad=10)
    ax.set_ylabel("Process", labelpad=10)
    ax.set_zlabel("")  # hide z label to keep it clean

    # compute time bounds
    max_time = max([seg[1] for seg in gantt_segments]) if gantt_segments else total_time
    ax.set_xlim(0, max(1, max_time))
    ax.set_ylim(-0.5, len(pids_order) - 0.5)
    ax.set_zlim(0, 1.5)

    # view & title
    ax.view_init(elev=20, azim=-60)
    ax.set_title("3D Gantt (Priority Scheduling)", pad=20, color=TEXT_COLOR)

    # grid for readability
    ax.grid(True, alpha=0.25)

    # set reasonable x-ticks (up to 10 ticks)
    try:
        step = max(1, max_time // 10)
    except Exception:
        step = 1
    ax.set_xticks(range(0, max(1, max_time + 1), step))

    canvas.draw()

# ---------------- Run simulation and update UI ----------------
def run_sim():
    if not process_list:
        messagebox.showwarning("No processes", "Add at least one process first.")
        return
    btn_start.config(state=DISABLED)
    btn_reset.config(state=DISABLED)
    # snapshot
    procs_snapshot = process_list.copy()
    preempt = preempt_var.get()
    # simulate (in background thread)
    def worker():
        procs_meta, gantt, total_time = simulate_priority_processes(procs_snapshot, preemptive=preempt)
        # update results in main thread
        root.after(0, update_after_sim, procs_meta, gantt, total_time)
    threading.Thread(target=worker).start()

def update_after_sim(procs_meta: List[Process], gantt: List[Tuple[int,int,str]], total_time: int):
    # fill results tree
    res_tree.delete(*res_tree.get_children())
    for p in sorted(procs_meta, key=lambda x: x.pid):
        st = p.start_time if p.start_time is not None else "-"
        ct = p.completion_time if p.completion_time is not None else "-"
        tat = p.turnaround_time if p.turnaround_time is not None else "-"
        wt = p.waiting_time if p.waiting_time is not None else "-"
        res_tree.insert("", END, values=(p.pid, p.arrival, p.burst, p.priority, st, ct, tat, wt))
    # avg
    tats = [p.turnaround_time for p in procs_meta if p.turnaround_time is not None]
    wts = [p.waiting_time for p in procs_meta if p.waiting_time is not None]
    avg_tat = sum(tats)/len(tats) if tats else 0
    avg_wt = sum(wts)/len(wts) if wts else 0
    avg_label.config(text=f"Avg WT: {avg_wt:.2f}    Avg TAT: {avg_tat:.2f}")
    # render 3D gantt
    render_3d_gantt(gantt, procs_meta, total_time)
    # populate middle table ST/CT columns not present; leave as originally (only initial data)
    btn_start.config(state=NORMAL)
    btn_reset.config(state=NORMAL)

# ---------------- Save Gantt PNG ----------------
def save_gantt_png():
    # Ask path
    p = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG","*.png")], initialfile="gantt_7747FD_gui.png")
    if not p:
        return
    # Render current figure to file
    fig.savefig(p, dpi=150)
    messagebox.showinfo("Saved", f"Gantt PNG saved to:\n{p}")

# ---------------- Wiring missing references (buttons) ----------------
# (buttons were created earlier but referenced names need assignment)
# Re-bind buttons to functions now available
btn_start = btn_start  # exist
btn_reset = btn_reset

# ---------------- Start with a sample ----------------
load_sample()

# ---------------- Mainloop ----------------
root.mainloop()
