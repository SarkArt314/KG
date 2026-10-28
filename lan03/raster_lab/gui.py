from __future__ import annotations

import math
import tkinter as tk
from tkinter import messagebox, ttk

from . import algorithms
from .timing import benchmark_all, measure_once

ALGO_ORDER = ["step", "dda", "bresenham_line", "bresenham_circle"]
ALGO_ITEMS = [(key, algorithms.ALGORITHM_TITLES[key]) for key in ALGO_ORDER]
TITLE_TO_KEY = {title: key for key, title in ALGO_ITEMS}

COLORS = {
    "step": "#e63946",
    "dda": "#2a9d8f",
    "bresenham_line": "#4361ee",
    "bresenham_circle": "#7209b7",
}

MAX_COORD = 10_000
MAX_RADIUS = 5_000


class WorldCanvas:
    """Канва с мировой системой координат, сеткой, осями и масштабированием."""

    def __init__(self, parent):
        self.canvas = tk.Canvas(parent, bg="white", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.scale = 28.0
        self.origin_x = None
        self.origin_y = None
        self.pixels = []
        self._drag_start = None

        self.canvas.bind("<Configure>", self._on_configure)
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Button-4>", self._on_mousewheel)
        self.canvas.bind("<Button-5>", self._on_mousewheel)
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)

    def world_to_screen(self, wx, wy):
        ox = 0.0 if self.origin_x is None else self.origin_x
        oy = 0.0 if self.origin_y is None else self.origin_y
        return ox + wx * self.scale, oy - wy * self.scale

    def screen_to_world(self, sx, sy):
        ox = 0.0 if self.origin_x is None else self.origin_x
        oy = 0.0 if self.origin_y is None else self.origin_y
        return (sx - ox) / self.scale, (oy - sy) / self.scale

    def cell_bbox(self, x, y):
        """Возвращает границы клетки, начинающейся в координате (x, y)."""
        ox = 0.0 if self.origin_x is None else self.origin_x
        oy = 0.0 if self.origin_y is None else self.origin_y

        left = ox + x * self.scale
        top = oy - (y + 1) * self.scale
        right = ox + (x + 1) * self.scale
        bottom = oy - y * self.scale

        return left, top, right, bottom

    def _grid_step(self):
        """Подбирает шаг сетки, чтобы подписи не сливались."""
        min_px = 24.0

        if self.scale <= 0:
            return 1

        raw = min_px / self.scale

        if raw <= 1.0:
            return 1

        pow10 = 10 ** int(math.floor(math.log10(raw)))

        for m in (1, 2, 5, 10):
            step = m * pow10
            if step >= raw:
                return max(1, int(round(step)))

        return max(1, int(math.ceil(raw)))

    def redraw(self):
        self.canvas.delete("all")
        self._draw_grid()
        self._draw_pixels()

    def _draw_grid(self):
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()

        if w <= 1 or h <= 1 or self.origin_x is None or self.origin_y is None:
            return

        left, top = self.screen_to_world(0, 0)
        right, bottom = self.screen_to_world(w, h)

        xmin, xmax = left, right
        ymin, ymax = bottom, top

        step = self._grid_step()

        first = int(math.ceil(xmin / step)) * step
        last = int(math.floor(xmax / step)) * step

        for gx in range(first, last + 1, step):
            sx = self.origin_x + gx * self.scale
            self.canvas.create_line(
                sx,
                0,
                sx,
                h,
                fill="#d8dbe2",
                width=1,
            )

            if gx != 0:
                ly = min(max(self.origin_y + 12, 10), h - 10)
                self.canvas.create_text(
                    sx,
                    ly,
                    text=str(gx),
                    anchor="n",
                    fill="#6c757d",
                    font=("Segoe UI", 8),
                )

        first = int(math.ceil(ymin / step)) * step
        last = int(math.floor(ymax / step)) * step

        for gy in range(first, last + 1, step):
            sy = self.origin_y - gy * self.scale
            self.canvas.create_line(
                0,
                sy,
                w,
                sy,
                fill="#d8dbe2",
                width=1,
            )
            if gy != 0:
                lx = min(max(self.origin_x - 8, 30), w - 10)
                self.canvas.create_text(
                    lx,
                    sy,
                    text=str(gy),
                    anchor="e",
                    fill="#6c757d",
                    font=("Segoe UI", 8),
                )

        self.canvas.create_line(
            self.origin_x, 0, self.origin_x, h, fill="#2b2d42", width=2
        )
        self.canvas.create_line(
            0, self.origin_y, w, self.origin_y, fill="#2b2d42", width=2
        )

        zx = min(max(self.origin_x + 4, 4), w - 20)
        zy = min(max(self.origin_y - 12, 10), h - 10)

        self.canvas.create_text(
            zx,
            zy,
            text="0",
            anchor="nw",
            fill="#2b2d42",
            font=("Segoe UI", 9, "bold"),
        )

        self.canvas.create_text(
            w - 12,
            min(max(self.origin_y - 12, 10), h - 10),
            text="X",
            fill="#2b2d42",
            font=("Segoe UI", 9, "bold"),
        )

        self.canvas.create_text(
            min(max(self.origin_x + 8, 8), w - 20),
            10,
            text="Y",
            fill="#2b2d42",
            font=("Segoe UI", 9, "bold"),
        )

    def _draw_pixels(self):
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()

        if w <= 1 or h <= 1 or self.origin_x is None or self.origin_y is None:
            return

        for x, y, color in self.pixels:
            left, top, right, bottom = self.cell_bbox(x, y)

            if right < 0 or left > w or bottom < 0 or top > h:
                continue

            self.canvas.create_rectangle(
                left,
                top,
                right,
                bottom,
                fill=color,
                outline=color,
                width=0,
            )

    def set_pixels(self, points, color="#e63946"):
        unique_points = algorithms._unique([(int(x), int(y)) for x, y in points])
        self.pixels = [(x, y, color) for x, y in unique_points]
        self.redraw()

    def clear_pixels(self):
        self.pixels = []
        self.redraw()

    def zoom(self, factor, center=None):
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()

        if w <= 1 or h <= 1:
            return

        if self.origin_x is None or self.origin_y is None:
            self.origin_x = w / 2
            self.origin_y = h / 2

        if center is None:
            center = (w / 2, h / 2)

        wx, wy = self.screen_to_world(*center)

        new_scale = min(max(self.scale * factor, 3.0), 300.0)

        if new_scale == self.scale:
            return

        self.scale = new_scale
        self.origin_x = center[0] - wx * self.scale
        self.origin_y = center[1] + wy * self.scale

        self.redraw()

    def reset_view(self):
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()

        self.scale = 28.0

        if w > 1 and h > 1:
            self.origin_x = w / 2
            self.origin_y = h / 2
            self.redraw()

    def _on_configure(self, event):
        if self.origin_x is None or self.origin_y is None:
            self.origin_x = event.width / 2
            self.origin_y = event.height / 2

        self.redraw()

    def _on_mousewheel(self, event):
        num = getattr(event, "num", None)
        delta = getattr(event, "delta", 0)

        if num == 4:
            factor = 1.1
        elif num == 5:
            factor = 0.9
        else:
            factor = 1.1 if delta > 0 else 0.9

        self.zoom(factor, (event.x, event.y))

    def _on_press(self, event):
        if self.origin_x is None or self.origin_y is None:
            return

        self._drag_start = (event.x, event.y, self.origin_x, self.origin_y)

    def _on_drag(self, event):
        if self._drag_start is None:
            return

        dx = event.x - self._drag_start[0]
        dy = event.y - self._drag_start[1]

        self.origin_x = self._drag_start[2] + dx
        self.origin_y = self._drag_start[3] + dy

        self.redraw()

    def _on_release(self, event):
        self._drag_start = None

class RasterLabApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Лабораторная работа 3: базовые растровые алгоритмы")
        self.root.geometry("1150x720")
        self.root.minsize(950, 600)

        self._build_ui()

        self.view = WorldCanvas(self.canvas_frame)
        self._algo_changed()

    def _build_ui(self):
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=1)

        left = ttk.Frame(self.root, padding=10)
        left.grid(row=0, column=0, sticky="nsew")

        self.canvas_frame = ttk.Frame(self.root)
        self.canvas_frame.grid(row=0, column=1, sticky="nsew")
        self.canvas_frame.columnconfigure(0, weight=1)
        self.canvas_frame.rowconfigure(0, weight=1)

        ttk.Label(left, text="Алгоритм:").pack(anchor="w")

        self.algo_var = tk.StringVar(value=ALGO_ITEMS[2][1])
        self.algo_combo = ttk.Combobox(
            left,
            textvariable=self.algo_var,
            values=[title for _, title in ALGO_ITEMS],
            state="readonly",
        )
        self.algo_combo.pack(fill="x", pady=(2, 8))
        self.algo_combo.bind("<<ComboboxSelected>>", lambda event: self._algo_changed())

        params = ttk.LabelFrame(left, text="Параметры", padding=8)
        params.pack(fill="x", pady=8)
        params.columnconfigure(1, weight=1)

        self.x0_var = tk.StringVar(value="2")
        self.y0_var = tk.StringVar(value="1")
        self.x1_var = tk.StringVar(value="9")
        self.y1_var = tk.StringVar(value="5")
        self.r_var = tk.StringVar(value="5")

        self.x0_entry = self._add_entry(params, 0, "x0 / cx:", self.x0_var)
        self.y0_entry = self._add_entry(params, 1, "y0 / cy:", self.y0_var)
        self.x1_entry = self._add_entry(params, 2, "x1:", self.x1_var)
        self.y1_entry = self._add_entry(params, 3, "y1:", self.y1_var)
        self.r_entry = self._add_entry(params, 4, "Радиус:", self.r_var)

        buttons = ttk.Frame(left)
        buttons.pack(fill="x", pady=8)
        buttons.columnconfigure(0, weight=1)

        ttk.Button(buttons, text="Построить", command=self.draw).grid(
            row=0, column=0, sticky="ew", pady=2
        )
        ttk.Button(buttons, text="Очистить", command=self.clear).grid(
            row=1, column=0, sticky="ew", pady=2
        )
        ttk.Button(buttons, text="Бенчмарк времени", command=self.run_benchmark).grid(
            row=2, column=0, sticky="ew", pady=2
        )
        zoom = ttk.Frame(left)
        zoom.pack(fill="x", pady=6)

        ttk.Button(zoom, text="+", width=4, command=lambda: self.view.zoom(1.25)).pack(
            side="left"
        )
        ttk.Button(zoom, text="-", width=4, command=lambda: self.view.zoom(0.8)).pack(
            side="left", padx=4
        )
        ttk.Button(zoom, text="Сброс", command=lambda: self.view.reset_view()).pack(
            side="left"
        )

        result_frame = ttk.LabelFrame(left, text="Результат и замеры", padding=6)
        result_frame.pack(fill="both", expand=True)

        self.result_text = tk.Text(result_frame, height=10, wrap="word")
        self.result_text.pack(fill="both", expand=True)
        self.result_text.config(state="disabled")

    def _add_entry(self, container, row, label_text, var):
        ttk.Label(container, text=label_text).grid(
            row=row, column=0, sticky="w", pady=2
        )

        entry = ttk.Entry(container, textvariable=var, width=10)
        entry.grid(row=row, column=1, sticky="ew", pady=2, padx=(6, 0))

        return entry

    def _current_algo_key(self):
        title = self.algo_var.get()
        return TITLE_TO_KEY.get(title, "bresenham_line")

    def _algo_changed(self):
        key = self._current_algo_key()
        is_circle = key == "bresenham_circle"

        line_extra_state = "disabled" if is_circle else "normal"
        radius_state = "normal" if is_circle else "disabled"

        self.x1_entry.config(state=line_extra_state)
        self.y1_entry.config(state=line_extra_state)
        self.r_entry.config(state=radius_state)

    def _set_result_text(self, text):
        self.result_text.config(state="normal")
        self.result_text.delete("1.0", "end")
        self.result_text.insert("1.0", text)
        self.result_text.config(state="disabled")

    def _get_int(self, var, name):
        text = var.get().strip()

        try:
            value = float(text.replace(",", "."))
        except ValueError:
            raise ValueError(f"Поле «{name}» должно содержать число.")

        if not math.isfinite(value):
            raise ValueError(f"Поле «{name}» должно содержать конечное число.")

        return algorithms._iround(value)

    def _get_line_args(self):
        x0 = self._get_int(self.x0_var, "x0")
        y0 = self._get_int(self.y0_var, "y0")
        x1 = self._get_int(self.x1_var, "x1")
        y1 = self._get_int(self.y1_var, "y1")

        args = (x0, y0, x1, y1)

        if any(abs(v) > MAX_COORD for v in args):
            raise ValueError(f"Координаты не должны превышать {MAX_COORD} по модулю.")

        return args

    def _get_circle_args(self):
        cx = self._get_int(self.x0_var, "cx")
        cy = self._get_int(self.y0_var, "cy")
        r = self._get_int(self.r_var, "r")

        if abs(cx) > MAX_COORD or abs(cy) > MAX_COORD:
            raise ValueError(
                f"Координаты центра не должны превышать {MAX_COORD} по модулю."
            )

        if r < 0:
            raise ValueError("Радиус не может быть отрицательным.")

        if r > MAX_RADIUS:
            raise ValueError(f"Радиус не должен превышать {MAX_RADIUS}.")

        return cx, cy, r

    def draw(self):
        key = self._current_algo_key()

        try:
            if key == "bresenham_circle":
                args = self._get_circle_args()
                func = algorithms.bresenham_circle
            else:
                args = self._get_line_args()
                func = algorithms.LINE_ALGORITHMS[key]

            points, info = measure_once(func, *args)
            self.view.set_pixels(points, COLORS[key])

            title = algorithms.ALGORITHM_TITLES[key]
            text = "\n".join(
                [
                    f"Алгоритм: {title}",
                    f"Параметры после округления до пикселей: {args}",
                    f"Точек: {info['points']}",
                    f"Время построения: {info['time_ms']:.6f} мс",
                    f"Время построения: {info['time_ns']} нс",
                ]
            )

            self._set_result_text(text)

        except ValueError as e:
            messagebox.showerror("Ошибка ввода", str(e))
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось выполнить алгоритм: {e}")

    def clear(self):
        self.view.clear_pixels()
        self._set_result_text("Холст очищен.")

    def run_benchmark(self):
        try:
            line_args = self._get_line_args()
        except ValueError:
            line_args = (0, 0, 160, 100)

        try:
            circle_args = self._get_circle_args()
        except ValueError:
            circle_args = (0, 0, 80)

        try:
            data = benchmark_all(
                line_args=line_args,
                circle_args=circle_args,
                min_total_ns=50_000_000,
            )

            lines = ["Бенчмарк (среднее время на один вызов):", ""]

            for key, title in ALGO_ITEMS:
                item = data.get(key)

                if not item:
                    continue

                lines.append(f"{title}")
                lines.append(f"  Точек: {item['points']}")
                lines.append(f"  Повторов: {item['repeats']}")
                lines.append(f"  Среднее время: {item['avg_ms']:.6f} мс")
                lines.append(f"  Суммарное время: {item['total_ms']:.3f} мс")
                lines.append("")

            self._set_result_text("\n".join(lines))

        except Exception as e:
            messagebox.showerror("Ошибка бенчмарка", str(e))

def main():
    root = tk.Tk()

    try:
        ttk.Style().theme_use("clam")
    except tk.TclError:
        pass

    RasterLabApp(root)
    root.mainloop()
