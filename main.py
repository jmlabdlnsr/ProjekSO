# main.py — CPU Scheduling Simulator
# Author: Kel 4 AB (Sipa, Syaila, Sixta, Jamal, Irsyad, Fikri)
# Deskripsi: Launcher dengan tampilan gradient dan tombol custom untuk memilih mode CPU scheduling:
# - FCFS
# - SJF
# - Priority
# - Round Robin

import tkinter as tk
from tkinter import messagebox, font as tkfont
from fcfs import FCFSPage
from sjf import SJFPage
from priority import PriorityPage
from rr import RRPage

# Theme colors
BG_TOP = "#1c0f3d"
BG_BOTTOM = "#a017b9"
PANEL_BG = "#1c0f3d"
BUTTON_FILL = "#fb47b2"
BUTTON_BORDER = "#75173e"
BUTTON_SHADOW = "#75173e"
TEXT_DARK = "#f2d6e4"
TITLE_COLOR = "#ffffff"
TITLE_FILL = "#fb47b2"
TITLE_BORDER = "#75173e"
TITLE_SHADOW = "#ffffff"

# Rounded rectangle helper
def round_rect(canvas, x1, y1, x2, y2, r=12, **kwargs):
    points = [
        x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
        x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
        x1, y2, x1, y2 - r, x1, y1 + r, x1, y1
    ]
    return canvas.create_polygon(points, smooth=False, **kwargs)

# Custom canvas button
class CanvasButton:
    def __init__(self, canvas, x, y, w, h, text, command, font=("Helvetica", 13, "bold")):
        self.canvas = canvas
        self.command = command
        self.font = font
        self.tag = f"button_{id(self)}"

        self.shadow = round_rect(canvas, x + 4, y + 6, x + w + 4, y + h + 6, r=14, fill=BUTTON_SHADOW, outline="", tags=(self.tag,))
        self.border = round_rect(canvas, x, y, x + w, y + h, r=14, fill=BUTTON_BORDER, outline="", tags=(self.tag,))
        pad = 4
        self.fill = round_rect(canvas, x + pad, y + pad, x + w - pad, y + h - pad, r=12, fill=BUTTON_FILL, outline="", tags=(self.tag,))
        self.label = canvas.create_text(int(x + w // 2), int(y + h // 2), text=text, font=self.font, fill=TEXT_DARK, tags=(self.tag,))
        canvas.tag_raise(self.label)

        canvas.tag_bind(self.tag, "<Button-1>", self._on_click)
        canvas.tag_bind(self.tag, "<Enter>", self._on_enter)
        canvas.tag_bind(self.tag, "<Leave>", self._on_leave)

    def _on_click(self, event=None):
        try:
            self.command()
        except Exception as e:
            print("Button callback error:", e)

    def _on_enter(self, event=None):
        try:
            self.canvas.itemconfigure(self.fill, fill="#f3fbdf")
            self.canvas.move(self.shadow, 0, 1)
            self.canvas.move(self.border, 0, -2)
            self.canvas.move(self.fill, 0, -2)
            self.canvas.move(self.label, 0, -2)
        except:
            pass

    def _on_leave(self, event=None):
        try:
            self.canvas.itemconfigure(self.fill, fill=BUTTON_FILL)
            self.canvas.move(self.shadow, 0, -1)
            self.canvas.move(self.border, 0, 2)
            self.canvas.move(self.fill, 0, 2)
            self.canvas.move(self.label, 0, 2)
        except:
            pass

# Main App
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Launcher — CPU Scheduling Simulator")

        # Window size
        initial_w, initial_h = 1300, 760
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x_pos = (screen_w // 2) - (initial_w // 2)
        y_pos = (screen_h // 2) - (initial_h // 2)
        self.geometry(f"{initial_w}x{initial_h}+{x_pos}+{y_pos}")

        self.W = initial_w
        self.H = initial_h
        self.resizable(True, True)
        self.minsize(900, 600)

        self.pixel_font_name = self.pick_pixel_font()
        self.rebuilding = False
        self.current_page = "home"

        self.page_container = tk.Frame(self, bg=PANEL_BG)
        self.page_container.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.bind("<Configure>", self._on_resize)
        self._build_ui()

    def pick_pixel_font(self):
        families = set(tkfont.families())
        candidates = ["Press Start 2P", "PixelOperator", "Minecraft", "Minecraftia", "Px437", "VT323", "OCR A Extended", "Consolas", "Courier New", "Courier", "Helvetica"]
        for name in candidates:
            if name in families:
                return name
        return "Helvetica"

    def _draw_gradient(self, canvas):
        steps = 60
        def hex_to_rgb(h):
            h = h.lstrip("#")
            return tuple(int(h[i:i+2], 16) for i in (0,2,4))
        def rgb_to_hex(rgb):
            return "#" + "".join(f"{v:02x}" for v in rgb)
        c1 = hex_to_rgb(BG_TOP)
        c2 = hex_to_rgb(BG_BOTTOM)
        for i in range(steps):
            r = i / (steps - 1)
            rgb = (int(c1[0] + (c2[0]-c1[0])*r),
                   int(c1[1] + (c2[1]-c1[1])*r),
                   int(c1[2] + (c2[2]-c1[2])*r))
            y0 = int(self.H * i / steps)
            y1 = int(self.H * (i + 1) / steps)
            canvas.create_rectangle(0, y0, self.W, y1, fill=rgb_to_hex(rgb), outline=rgb_to_hex(rgb))

    def draw_text_with_shadow_border(self, canvas, x, y, text, font, fill, border, shadow, shadow_offset=(4,4), border_thickness=4):
        sx, sy = shadow_offset
        canvas.create_text(int(x+sx), int(y+sy), text=text, font=font, fill=shadow)
        for dx in range(-border_thickness, border_thickness+1):
            for dy in range(-border_thickness, border_thickness+1):
                if dx == 0 and dy == 0:
                    continue
                canvas.create_text(int(x+dx), int(y+dy), text=text, font=font, fill=border)
        canvas.create_text(int(x), int(y), text=text, font=font, fill=fill)

    # HOME PAGE
    def _home_page(self):
        if self.rebuilding: return
        self.rebuilding = True
        self.current_page = "home"

        for w in self.page_container.winfo_children():
            w.destroy()

        canvas = tk.Canvas(self.page_container, width=self.W, height=self.H, highlightthickness=0)
        canvas.pack(fill="both", expand=True)
        self._draw_gradient(canvas)

        cx = self.W // 2
        top_margin = int(self.H * 0.06)
        top_h = int(self.H * 0.50)

        title_font_size = max(150, int(self.H * 0.08))
        title_font = (self.pixel_font_name, title_font_size, "bold")
        line_spacing_title = int(title_font_size * 1.2)

        self.draw_text_with_shadow_border(canvas, cx, top_margin + int(top_h*0.30), text="LET'S", font=title_font, fill=TITLE_FILL, border=TITLE_BORDER, shadow=TITLE_SHADOW)
        self.draw_text_with_shadow_border(canvas, cx, top_margin + int(top_h*0.30) + line_spacing_title, text="PLAY", font=title_font, fill=TITLE_FILL, border=TITLE_BORDER, shadow=TITLE_SHADOW)

        btn_w = int(self.W * 0.18)
        btn_h = max(int(self.H * 0.08), 48)
        gap = int(btn_w * 0.20)
        total_w = btn_w + gap + btn_w
        bx = (self.W - total_w) // 2
        by = top_margin + top_h + (self.H - (top_margin + top_h) - btn_h) // 2

        CanvasButton(canvas, bx, by, btn_w, btn_h, "START", lambda: self._mode_page(), font=(self.pixel_font_name, max(12, int(self.H * 0.03)), "bold"))
        CanvasButton(canvas, bx + btn_w + gap, by, btn_w, btn_h, "EXIT", lambda: self.destroy(), font=(self.pixel_font_name, max(12, int(self.H * 0.03)), "bold"))

        line_height = int(self.H * 0.03)
        canvas.create_text(cx, by + btn_h + 5 * line_height, text="Made by Sipa, Syaila, Sixta, Jamal, Irsyad, Fikri - Kel 4 AB", font=(self.pixel_font_name, max(8, int(self.H * 0.015))), fill="#20435a")
        self.rebuilding = False

    # MODE SELECTION PAGE
    def _mode_page(self):
        if self.rebuilding: return
        self.rebuilding = True
        self.current_page = "mode"

        for w in self.page_container.winfo_children():
            w.destroy()

        canvas = tk.Canvas(self.page_container, width=self.W, height=self.H, highlightthickness=0)
        canvas.pack(fill="both", expand=True)
        self._draw_gradient(canvas)

        cx = self.W // 2
        cy = self.H // 4
        title_font = (self.pixel_font_name, max(30, int(self.H * 0.05)), "bold")
        canvas.create_text(cx, cy, text="Select Scheduling Mode", font=title_font, fill=TITLE_COLOR)

        btn_w = int(self.W * 0.18)
        btn_h = max(int(self.H * 0.08), 48)
        line_height = int(self.H * 0.03)
        gap_y = line_height * 3
        cy_start = cy + 80

        # posisi kiri & kanan
        bx_left = (self.W // 2) - btn_w - 10
        bx_right = (self.W // 2) + 10

        # tombol kiri
        left_buttons = [("SJF", SJFPage), ("Priority", PriorityPage)]
        for i, (text, page) in enumerate(left_buttons):
            by = cy_start + i * (btn_h + gap_y)
            CanvasButton(canvas, bx_left, by, btn_w, btn_h, text, lambda p=page: self.show_page(p), font=(self.pixel_font_name, max(12, int(self.H * 0.03)), "bold"))

        # tombol kanan
        right_buttons = [("FCFS", FCFSPage), ("Round Robin", RRPage)]
        for i, (text, page) in enumerate(right_buttons):
            by = cy_start + i * (btn_h + gap_y)
            CanvasButton(canvas, bx_right, by, btn_w, btn_h, text, lambda p=page: self.show_page(p), font=(self.pixel_font_name, max(12, int(self.H * 0.03)), "bold"))

        # tombol BACK
        by_back = cy_start + max(len(left_buttons), len(right_buttons)) * (btn_h + gap_y)
        bx_back = (self.W - btn_w) // 2
        CanvasButton(canvas, bx_back, by_back, btn_w, btn_h, "BACK", lambda: self._home_page(), font=(self.pixel_font_name, max(12, int(self.H * 0.03)), "bold"))

        self.rebuilding = False

    # Show page
    def show_page(self, PageClass):
        for w in self.page_container.winfo_children():
            w.destroy()
        try:
            PageClass(self.page_container, app=self)
        except Exception as e:
            messagebox.showerror("Page error", f"Gagal membuat halaman:\n{e}")

    # RESIZE HANDLER
    def _on_resize(self, event):
        if event.widget == self:
            self.W = event.width
            self.H = event.height
            if self.current_page == "home":
                self._home_page()
            elif self.current_page == "mode":
                self._mode_page()

    def _build_ui(self):
        self._home_page()

if __name__ == "__main__":
    app = App()
    app.mainloop()
