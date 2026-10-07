import tkinter as tk
from tkinter import ttk, colorchooser


def clamp(value, low, high):
    return max(low, min(high, float(value)))

def rgb_to_cmyk(r, g, b):
    r = clamp(r, 0, 255) / 255.0
    g = clamp(g, 0, 255) / 255.0
    b = clamp(b, 0, 255) / 255.0

    k = 1.0 - max(r, g, b)

    if k >= 1.0:
        return 0.0, 0.0, 0.0, 100.0

    c = (1.0 - r - k) / (1.0 - k)
    m = (1.0 - g - k) / (1.0 - k)
    y = (1.0 - b - k) / (1.0 - k)

    return c * 100.0, m * 100.0, y * 100.0, k * 100.0


def cmyk_to_rgb(c, m, y, k):

    c = clamp(c, 0, 100) / 100.0
    m = clamp(m, 0, 100) / 100.0
    y = clamp(y, 0, 100) / 100.0
    k = clamp(k, 0, 100) / 100.0

    r = 255.0 * (1.0 - c) * (1.0 - k)
    g = 255.0 * (1.0 - m) * (1.0 - k)
    b = 255.0 * (1.0 - y) * (1.0 - k)

    return (
        int(round(clamp(r, 0, 255))),
        int(round(clamp(g, 0, 255))),
        int(round(clamp(b, 0, 255))),
    )


def rgb_to_hsv(r, g, b):
    r = clamp(r, 0, 255) / 255.0
    g = clamp(g, 0, 255) / 255.0
    b = clamp(b, 0, 255) / 255.0

    mx = max(r, g, b)
    mn = min(r, g, b)
    delta = mx - mn

    # Hue
    if delta == 0.0:
        h = 0.0
    elif mx == r:
        h = 60.0 * (((g - b) / delta) % 6.0)
    elif mx == g:
        h = 60.0 * (((b - r) / delta) + 2.0)
    else:
        h = 60.0 * (((r - g) / delta) + 4.0)

    h = h % 360.0

    # Saturation
    if mx == 0.0:
        s = 0.0
    else:
        s = (delta / mx) * 100.0

    # Value
    v = mx * 100.0

    return h, s, v


def hsv_to_rgb(h, s, v):

    h = float(h) % 360.0
    s = clamp(s, 0, 100) / 100.0
    v = clamp(v, 0, 100) / 100.0

    c = v * s
    x = c * (1.0 - abs((h / 60.0) % 2.0 - 1.0))
    m = v - c

    if 0.0 <= h < 60.0:
        r1, g1, b1 = c, x, 0.0
    elif 60.0 <= h < 120.0:
        r1, g1, b1 = x, c, 0.0
    elif 120.0 <= h < 180.0:
        r1, g1, b1 = 0.0, c, x
    elif 180.0 <= h < 240.0:
        r1, g1, b1 = 0.0, x, c
    elif 240.0 <= h < 300.0:
        r1, g1, b1 = x, 0.0, c
    else:
        r1, g1, b1 = c, 0.0, x

    r = int(round((r1 + m) * 255.0))
    g = int(round((g1 + m) * 255.0))
    b = int(round((b1 + m) * 255.0))

    return r, g, b

class ColorLabApp:
    MODELS = ("CMYK", "RGB", "HSV")

    COMPONENTS = {
        "CMYK": ("C", "M", "Y", "K"),
        "RGB": ("R", "G", "B"),
        "HSV": ("H", "S", "V"),
    }

    LABELS = {
        "CMYK.C": "C, %",
        "CMYK.M": "M, %",
        "CMYK.Y": "Y, %",
        "CMYK.K": "K, %",

        "RGB.R": "R, 0-255",
        "RGB.G": "G, 0-255",
        "RGB.B": "B, 0-255",

        "HSV.H": "H, град.",
        "HSV.S": "S, %",
        "HSV.V": "V, %",
    }

    def __init__(self, root):
        self.root = root

        self.r = 255
        self.g = 0
        self.b = 0

        self._updating = False

        self.scales = {model: {} for model in self.MODELS}
        self.entries = {model: {} for model in self.MODELS}

        self._build_ui()

        self.apply_color("RGB", (255, 0, 0))

    def _build_ui(self):
        self.root.title("Лабораторная работа 1: CMYK – RGB – HSV")
        self.root.geometry("1100x460")
        self.root.minsize(980, 400)

        top = ttk.Frame(self.root)
        top.pack(fill="x", padx=10, pady=10)

        self.preview_canvas = tk.Canvas(
            top,
            width=240,
            height=90,
            highlightthickness=1,
            highlightbackground="black"
        )
        self.preview_canvas.pack(side="left")

        self.preview_item = self.preview_canvas.create_rectangle(
            0, 0, 240, 90,
            fill="#FF0000",
            outline=""
        )

        info = ttk.Frame(top)
        info.pack(side="left", padx=15)

        self.hex_label = ttk.Label(
            info,
            text="#FF0000",
            font=("Arial", 13, "bold")
        )
        self.hex_label.pack(anchor="w")

        ttk.Button(
            info,
            text="Выбрать цвет из палитры",
            command=self.choose_color
        ).pack(anchor="w", pady=5)

        columns = ttk.Frame(self.root)
        columns.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        for i, model in enumerate(self.MODELS):
            box = ttk.LabelFrame(columns, text=f"Модель {model}")
            box.grid(row=0, column=i, sticky="nsew", padx=6)
            columns.columnconfigure(i, weight=1)
            columns.rowconfigure(0, weight=1)

            for comp in self.COMPONENTS[model]:
                self._add_component(box, model, comp)

    def _add_component(self, parent, model, comp):
        low, high = self._range(model, comp)

        row = ttk.Frame(parent)
        row.pack(fill="x", padx=6, pady=5)

        ttk.Label(
            row,
            text=self.LABELS[f"{model}.{comp}"],
            width=12
        ).pack(side="left")

        scale = ttk.Scale(
            row,
            from_=low,
            to=high,
            orient="horizontal",
            command=lambda value, m=model, c=comp: self._on_scale(m, c)
        )
        scale.pack(side="left", fill="x", expand=True, padx=6)

        entry = ttk.Entry(row, width=8)
        entry.pack(side="left")

        entry.bind(
            "<Return>",
            lambda event, m=model, c=comp: self._on_entry(m, c)
        )
        entry.bind(
            "<FocusOut>",
            lambda event, m=model, c=comp: self._on_entry(m, c)
        )

        self.scales[model][comp] = scale
        self.entries[model][comp] = entry


    def _range(self, model, comp):
        if model == "RGB":
            return 0, 255

        if model == "CMYK":
            return 0, 100

        if comp == "H":
            return 0, 360

        return 0, 100

    def _clamp_component(self, model, comp, value):
        low, high = self._range(model, comp)
        value = clamp(value, low, high)

        if model == "RGB":
            return int(round(value))

        return float(value)

    def _format_value(self, model, comp, value):
        if model == "RGB":
            return str(int(round(value)))

        return f"{float(value):.2f}"

    def _read_model_from_scales(self, model):
        values = []

        for comp in self.COMPONENTS[model]:
            value = self.scales[model][comp].get()
            value = self._clamp_component(model, comp, value)
            values.append(value)

        return tuple(values)

    def _read_model_from_entries(self, model):
        values = []

        for comp in self.COMPONENTS[model]:
            text = self.entries[model][comp].get().strip().replace(",", ".")

            try:
                value = float(text)
            except ValueError:
                value = self.scales[model][comp].get()

            value = self._clamp_component(model, comp, value)
            values.append(value)

        return tuple(values)

    def _on_scale(self, model, comp):
        if self._updating:
            return

        values = self._read_model_from_scales(model)
        self.apply_color(model, values)

    def _on_entry(self, model, comp):
        if self._updating:
            return

        values = self._read_model_from_entries(model)
        self.apply_color(model, values)

    def choose_color(self):
        initial_color = "#{:02x}{:02x}{:02x}".format(self.r, self.g, self.b)

        rgb, _ = colorchooser.askcolor(
            color=initial_color,
            title="Выбор цвета"
        )

        if rgb is not None:
            rgb = tuple(int(round(channel)) for channel in rgb)
            self.apply_color("RGB", rgb)

    def apply_color(self, source_model, values):

        self._updating = True

        try:
            if source_model == "RGB":
                rgb_vals = tuple(
                    self._clamp_component("RGB", comp, value)
                    for comp, value in zip(self.COMPONENTS["RGB"], values)
                )

                self.r, self.g, self.b = rgb_vals

                cmyk_vals = rgb_to_cmyk(*rgb_vals)
                hsv_vals = rgb_to_hsv(*rgb_vals)

            elif source_model == "CMYK":
                cmyk_vals = tuple(
                    self._clamp_component("CMYK", comp, value)
                    for comp, value in zip(self.COMPONENTS["CMYK"], values)
                )

                rgb_vals = cmyk_to_rgb(*cmyk_vals)
                self.r, self.g, self.b = rgb_vals

                hsv_vals = rgb_to_hsv(*rgb_vals)

            elif source_model == "HSV":
                hsv_vals = tuple(
                    self._clamp_component("HSV", comp, value)
                    for comp, value in zip(self.COMPONENTS["HSV"], values)
                )

                rgb_vals = hsv_to_rgb(*hsv_vals)
                self.r, self.g, self.b = rgb_vals

                cmyk_vals = rgb_to_cmyk(*rgb_vals)

            else:
                raise ValueError(f"Неизвестная цветовая модель: {source_model}")

            self._write_model("RGB", rgb_vals)
            self._write_model("CMYK", cmyk_vals)
            self._write_model("HSV", hsv_vals)

            self._update_preview()

        finally:
            self._updating = False

    def _write_model(self, model, values):
        for comp, value in zip(self.COMPONENTS[model], values):
            self.scales[model][comp].set(float(value))

            entry = self.entries[model][comp]
            entry.delete(0, tk.END)
            entry.insert(0, self._format_value(model, comp, value))

    def _update_preview(self):
        hex_color = "#{:02x}{:02x}{:02x}".format(self.r, self.g, self.b)

        self.preview_canvas.itemconfigure(
            self.preview_item,
            fill=hex_color
        )

        self.hex_label.config(text=hex_color.upper())


def main():
    root = tk.Tk()
    app = ColorLabApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()