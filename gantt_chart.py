# visualization/gantt_chart.py
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from typing import List, Tuple
from src.core.process import Process

APP_BG = "#F6F8FB"
BAR_COLOR = "#7747FD"
TEXT_COLOR = "#001858"

def create_figure(figsize=(7,5), dpi=100):
    fig = plt.Figure(figsize=figsize, dpi=dpi)
    ax = fig.add_subplot(111, projection="3d")
    fig.patch.set_facecolor(APP_BG)
    return fig, ax

def render_3d_gantt(canvas, fig, ax, gantt_segments: List[Tuple[int,int,str]], procs_meta: List[Process], total_time: int):
    """
    canvas: FigureCanvasTkAgg instance (so we can call canvas.draw())
    fig, ax: matplotlib Figure and Axes3D
    """
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

    xs, ys, zs, dxs, dys, dzs, colors = [], [], [], [], [], [], []
    for start,end,pid in gantt_segments:
        dur = end - start
        xs.append(start)
        ys.append(y_pos[pid])
        zs.append(0)
        dxs.append(dur)
        dys.append(0.6)
        dzs.append(1)
        colors.append(BAR_COLOR)
    if xs:
        ax.bar3d(xs, ys, zs, dxs, dys, dzs, color=colors, shade=True, edgecolor="#222222", linewidth=0.2)
    ax.set_yticks(list(y_pos.values()))
    ax.set_yticklabels(list(y_pos.keys()))
    ax.set_xlabel("Time")
    ax.set_zlim(0, 1.5)
    ax.set_zlabel("")
    ax.set_title("3D Gantt (Priority Scheduling)", color=TEXT_COLOR)
    ax.view_init(elev=20, azim=-60)
    # set xticks
    if gantt_segments:
        max_t = max(seg[1] for seg in gantt_segments)
    else:
        max_t = total_time
    ax.set_xticks(range(0, max(1, max_t+1), max(1, max(1, max_t//10))))
    canvas.draw()
