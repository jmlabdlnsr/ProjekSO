"""
rr.py

Round Robin Scheduling GUI
Quantum-based preemptive scheduling
"""

from tkinter import *
from tkinter import ttk, messagebox, filedialog
import threading
from dataclasses import dataclass, field
from typing import List, Tuple, Optional
import matplotlib
try:
    matplotlib.use("TkAgg")
except:
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

    timeline: List[Tuple[int,int]] = field(default_factory=list)

    def __post_init__(self):
        self.remaining = self.burst

# ---------------- Round Robin Logic ----------------
def simulate_rr(proc_tuples: List[Tuple[str,int,int]], quantum: int):
    """
    Round Robin (Preemptive)
    Returns:
        - process meta list
        - gantt segments
        - total time
    """
    procs = [Process(pid, at, bt) for (pid, at, bt) in proc_tuples]
    n = len(procs)
    time = 0
    gantt = []

    # Sort by arrival
    procs_sorted = sorted(procs, key=lambda x: x.arrival)
    ready = []
    idx = 0

    while True:
        # Add newly arrived processes
        while idx < n and procs_sorted[idx].arrival <= time:
            ready.append(procs_sorted[idx])
            idx += 1

        if not ready:  # No one ready → jump to next arrival
            if idx < n:
                time = procs_sorted[idx].arrival
                continue
            else:
                break

        p = ready.pop(0)

        if p.start_time is None:
            p.start_time = time

        exec_time = min(quantum, p.remaining)
        start = time
        end = time + exec_time

        # Log into gantt
        p.timeline.append((start, end))
        gantt.append((start, end, p.pid))

        time = end
        p.remaining -= exec_time

        # Check arrivals during execution
        while idx < n and procs_sorted[idx].arrival <= time:
            ready.append(procs_sorted[idx])
            idx += 1

        if p.remaining > 0:
            ready.append(p)
        else:
            p.completion_time = time
            p.turnaround_time = p.completion_time - p.arrival
            p.waiting_time = p.turnaround_time - p.burst

    return procs_sorted, gantt, time

# ---------------- GUI ----------------
APP_BG = "#F6F8FB"
BAR_COLOR = "#7747FD"
TEXT_COLOR = "#001858"

root = Tk()
root.title("Round Robin Scheduler - Kelas A")
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

# ---------------- Left: Inputs ----------------
Label(left_frame, text="➤ Round Robin Scheduler", font=("Segoe UI",16,"bold"), bg=APP_BG, fg=TEXT_COLOR).pack(pady=8)

inp_frame = Frame(left_frame, bg=APP_BG)
inp_frame.pack(pady=6)
Label(inp_frame, text="Arrival", bg=APP_BG).grid(row=0, column=0, padx=4)
entry_at = Entry(inp_frame, width=8); entry_at.grid(row=0, column=1, padx=4)
Label(inp_frame, text="Burst", bg=APP_BG).grid(row=0, column=2, padx=4)
entry_bt = Entry(inp_frame, width=8); entry_bt.grid(row=0, column=3, padx=4)

Label(inp_frame, text="Quantum", bg=APP_BG).grid(row=1, column=0, padx=4, pady=4)
entry_q = Entry(inp_frame, width=8)
entry_q.grid(row=1, column=1, padx=4)
entry_q.insert(0, "2")

Button(left_frame, text="➕ Add Process", bg=BAR_COLOR, fg="white",
       command=lambda: add_process()).pack(fill=X, padx=12, pady=6)

ctrl_frame = Frame(left_frame, bg=APP_BG)
ctrl_frame.pack(pady=6, fill=X)
Label(ctrl_frame, text="RR - Preemptive", bg=APP_BG,
      font=("Segoe UI",10,"bold")).pack(side=LEFT, padx=6)
btn_start = Button(ctrl_frame, text="▶ Start", bg="#8bd3dd",
                   command=lambda: threading.Thread(target=run_sim).start())
btn_start.pack(side=LEFT, padx=6)
btn_reset = Button(ctrl_frame, text="🔁 Reset", bg="#f3d2c1",
                   command=lambda: reset_all())
btn_reset.pack(side=LEFT, padx=6)

Button(left_frame, text="Save Gantt PNG", bg="#ffc8dd",
       command=lambda: save_gantt_png()).pack(fill=X, padx=12, pady=6)

# Results table
Label(left_frame, text="Results (per-process)", bg=APP_BG, fg=TEXT_COLOR,
      font=("Segoe UI",11,"bold")).pack(pady=6)

res_cols = ("PID","AT","BT","ST","CT","TAT","WT")
res_tree = ttk.Treeview(left_frame, columns=res_cols, show="headings", height=8)
for c in res_cols:
    res_tree.heading(c, text=c)
    res_tree.column(c, width=45, anchor=CENTER)
res_tree.pack(fill=BOTH, padx=8, pady=6)

avg_label = Label(left_frame, text="Avg WT: -    Avg TAT: -", bg=APP_BG,
                  font=("Segoe UI",11,"bold"), fg=TEXT_COLOR)
avg_label.pack(pady=6)

# ---------------- Middle: Table ----------------
Label(mid_frame, text="Processes", font=("Segoe UI",13,"bold"),
      bg=APP_BG, fg=TEXT_COLOR).pack(pady=6)
cols = ("PID","Arrival","Burst")
tree = ttk.Treeview(mid_frame, columns=cols, show="headings", height=20)
for c,w in zip(cols, (120,120,120)):
    tree.heading(c, text=c)
    tree.column(c, width=w, anchor=CENTER)
tree.pack(fill=BOTH, expand=True, padx=6, pady=6)

mid_btn_frame = Frame(mid_frame, bg=APP_BG)
mid_btn_frame.pack(fill=X, pady=4)
Button(mid_btn_frame, text="Load Sample", bg="#ffc8dd",
       command=lambda: load_sample()).pack(side=LEFT, padx=6)
Button(mid_btn_frame, text="Import CSV", bg="#ffd3b6",
       command=lambda: import_csv()).pack(side=LEFT, padx=6)

# ---------------- Right: 3D Gantt Chart ----------------
Label(right_frame, text="3D Gantt Chart", font=("Segoe UI",13,"bold"),
      bg=APP_BG, fg=TEXT_COLOR).pack(pady=6)

fig = plt.Figure(figsize=(7,5), dpi=100)
ax = fig.add_subplot(111, projection='3d')
fig.patch.set_facecolor(APP_BG)
canvas = FigureCanvasTkAgg(fig, master=right_frame)
canvas.get_tk_widget().pack(fill=BOTH, expand=True, padx=6, pady=6)

# ---------------- Data storage ----------------
process_list: List[Tuple[str,int,int]] = []

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
    except:
        messagebox.showerror("Error", "Arrival/Burst harus integer.")
        return

    pid = f"P{len(process_list)+1}"
    process_list.append((pid, at, bt))
    entry_at.delete(0, END); entry_bt.delete(0, END)
    update_treeviews()

def load_sample():
    global process_list
    process_list = [
        ("P1", 0, 5),
        ("P2", 1, 3),
        ("P3", 2, 8),
        ("P4", 3, 6)
    ]
    update_treeviews()

def import_csv():
    global process_list
    p = filedialog.askopenfilename(filetypes=[("CSV","*.csv")])
    if not p:
        return
    try:
        import csv
        with open(p) as f:
            rows = list(csv.reader(f))

        process_list = []
        for i,row in enumerate(rows,1):
            if len(row)>=3:
                pid=row[0]; at=int(row[1]); bt=int(row[2])
            else:
                pid=f"P{i}"; at=int(row[0]); bt=int(row[1])
            process_list.append((pid,at,bt))
        update_treeviews()
    except Exception as e:
        messagebox.showerror("CSV Error", str(e))

def reset_all():
    global process_list
    process_list=[]
    update_treeviews()
    res_tree.delete(*res_tree.get_children())
    avg_label.config(text="Avg WT: -    Avg TAT: -")
    ax.clear()
    canvas.draw()

def render_3d_gantt(gantt, procs, total):
    ax.clear()
    ax.set_facecolor(APP_BG)
    fig.patch.set_facecolor(APP_BG)

    colors=["#7747FD","#FF6B6B","#4ECDC4","#45B7D1","#96CEB4","#FECA57"]
    pids = []
    for s in gantt:
        if s[2] not in pids:
            pids.append(s[2])

    ymap = {pid:i for i,pid in enumerate(pids)}

    xs=[]; ys=[]; zs=[]; dx=[]; dy=[]; dz=[]; c=[]

    for (s,e,pid) in gantt:
        xs.append(s)
        ys.append(ymap[pid])
        zs.append(0)
        dx.append(e-s)
        dy.append(0.8)
        dz.append(1)
        c.append(colors[ymap[pid] % len(colors)])

    if xs:
        ax.bar3d(xs,ys,zs,dx,dy,dz,color=c,alpha=0.85,
                 edgecolor='black', linewidth=0.4)

    ax.set_yticks(list(ymap.values()))
    ax.set_yticklabels(list(ymap.keys()))
    ax.set_xlabel("Time"); ax.set_ylabel("Process")
    ax.set_zlabel("")
    ax.set_title("3D Gantt (Round Robin)", color=TEXT_COLOR)

    ax.view_init(20,-60)
    canvas.draw()

def run_sim():
    if not process_list:
        messagebox.showwarning("Empty", "Tambahkan proses dahulu.")
        return
    try:
        q = int(entry_q.get())
    except:
        messagebox.showerror("Error", "Quantum harus integer.")
        return

    btn_start.config(state=DISABLED)
    btn_reset.config(state=DISABLED)

    snapshot = process_list.copy()

    def worker():
        meta, gantt, total = simulate_rr(snapshot, q)
        root.after(0, update_after_sim, meta, gantt, total)

    threading.Thread(target=worker).start()

def update_after_sim(meta, gantt, total):
    res_tree.delete(*res_tree.get_children())
    for p in meta:
        st = p.start_time if p.start_time is not None else "-"
        ct = p.completion_time if p.completion_time is not None else "-"
        tat = p.turnaround_time if p.turnaround_time is not None else "-"
        wt = p.waiting_time if p.waiting_time is not None else "-"
        res_tree.insert("",END,values=(p.pid,p.arrival,p.burst,st,ct,tat,wt))

    wt_list=[p.waiting_time for p in meta]
    tat_list=[p.turnaround_time for p in meta]
    avg_wt=sum(wt_list)/len(wt_list)
    avg_tat=sum(tat_list)/len(tat_list)
    avg_label.config(text=f"Avg WT: {avg_wt:.2f}    Avg TAT: {avg_tat:.2f}")

    render_3d_gantt(gantt, meta, total)

    btn_start.config(state=NORMAL)
    btn_reset.config(state=NORMAL)

def save_gantt_png():
    p = filedialog.asksaveasfilename(defaultextension=".png",
                    filetypes=[("PNG","*.png")],
                    initialfile="gantt_rr.png")
    if p:
        fig.savefig(p, dpi=150)
        messagebox.showinfo("Saved", f"Saved to:\n{p}")

load_sample()

root.mainloop()
