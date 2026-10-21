import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from PIL import ImageTk

from .image_utils import fit_image, load_image, save_image
from .sharpening import apply_laplacian, apply_unsharp
from .thresholding import apply_threshold, binary_difference_percent, binary_stats


def _app_directory():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


class Application(tk.Tk):
    IMAGE_FILETYPES = [
        ("Изображения", "*.png *.jpg *.jpeg *.bmp *.tif *.tiff *.webp"),
        ("Все файлы", "*.*"),
    ]

    def __init__(self):
        super().__init__()
        self.title("Лабораторная работа 2 — Вариант 8")
        self.geometry("1280x820")
        self.minsize(1050, 700)
        self.app_dir = _app_directory()
        self.original_image = None
        self.last_result = None
        self.th_otsu_result = None
        self.th_mean_result = None
        self.sh_unsharp_result = None
        self.sh_laplacian_result = None

        self._build_menu()
        self._build_ui()

    def _build_menu(self):
        menu = tk.Menu(self)
        file_menu = tk.Menu(menu, tearoff=0)
        file_menu.add_command(label="Открыть изображение...", command=self.open_image, accelerator="Ctrl+O")
        file_menu.add_command(label="Сохранить последний результат...", command=self.save_last_result, accelerator="Ctrl+S")
        menu.add_cascade(label="Файл", menu=file_menu)
        self.config(menu=menu)
        self.bind("<Control-o>", lambda _event: self.open_image())
        self.bind("<Control-s>", lambda _event: self.save_last_result())

    def _build_ui(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=8, pady=(8, 2))
        self.threshold_tab = ttk.Frame(self.notebook)
        self.sharpen_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.threshold_tab, text="Глобальная пороговая обработка")
        self.notebook.add(self.sharpen_tab, text="Высокочастотные фильтры")
        self._build_threshold_tab()
        self._build_sharpen_tab()

    def _build_threshold_tab(self):
        self.th_invert = tk.BooleanVar(value=False)
        controls = ttk.LabelFrame(self.threshold_tab, text="Параметры глобальной пороговой обработки")
        controls.pack(fill="x", padx=6, pady=6)
        ttk.Label(controls, text="Метод 1: Otsu (Отсу)").grid(row=0, column=0, sticky="w", padx=6, pady=4)
        ttk.Label(controls, text="Метод 2: Средний порог").grid(row=1, column=0, sticky="w", padx=6, pady=4)
        ttk.Checkbutton(controls, text="Инвертировать результат", variable=self.th_invert).grid(
            row=2, column=0, sticky="w", padx=6, pady=2
        )
        buttons = ttk.Frame(controls)
        buttons.grid(row=3, column=0, sticky="w", padx=6, pady=6)
        ttk.Button(buttons, text="Применить и сравнить", command=self.apply_threshold).pack(side="left", padx=4)
        for title, attr, filename in (
            ("Сохранить Otsu", "th_otsu_result", "threshold_otsu.png"),
            ("Сохранить средний порог", "th_mean_result", "threshold_mean.png"),
        ):
            ttk.Button(
                buttons, text=title,
                command=lambda a=attr, f=filename: self._save_image(getattr(self, a), f),
            ).pack(side="left", padx=4)

        self.th_info = self._make_info(
            self.threshold_tab, "Пояснение и метрики",
            "Откройте изображение и нажмите «Применить и сравнить».\n"
            "Реализованы ровно два метода: Otsu и средний порог."
        )
        images = ttk.Frame(self.threshold_tab)
        images.pack(fill="both", expand=True, padx=6, pady=6)
        self.th_canvases = []
        titles = ("Исходное изображение", "Порог: Otsu", "Порог: средний")
        for index, title in enumerate(titles):
            frame, canvas = self._make_image_panel(images, title)
            frame.grid(row=0, column=index, padx=6, pady=6, sticky="nsew")
            images.rowconfigure(0, weight=1)
            images.columnconfigure(index, weight=1)
            self.th_canvases.append(canvas)

    def _build_sharpen_tab(self):
        self.sh_amount = tk.DoubleVar(value=1.0)
        self.sh_ksize = tk.IntVar(value=5)
        self.sh_threshold = tk.IntVar(value=8)
        controls = ttk.LabelFrame(self.sharpen_tab, text="Параметры увеличения резкости")
        controls.pack(fill="x", padx=6, pady=6)
        self._add_scale(controls, 0, "Сила эффекта (amount):", 0, 5, self.sh_amount, 1, 0.1)
        self._add_scale(controls, 1, "Размер ядра / размытия:", 1, 31, self.sh_ksize, 1, 1)
        self._add_scale(controls, 2, "Порог подавления шума (только Unsharp):", 0, 100, self.sh_threshold, 1, 1)
        buttons = ttk.Frame(controls)
        buttons.grid(row=3, column=0, columnspan=3, sticky="w", padx=6, pady=6)
        ttk.Button(buttons, text="Применить оба метода", command=self.apply_sharpening).pack(side="left", padx=4)
        for title, attr, filename in (
            ("Сохранить Unsharp", "sh_unsharp_result", "sharpen_unsharp_mask.png"),
            ("Сохранить Laplacian", "sh_laplacian_result", "sharpen_laplacian.png"),
        ):
            ttk.Button(
                buttons, text=title,
                command=lambda a=attr, f=filename: self._save_image(getattr(self, a), f),
            ).pack(side="left", padx=4)
        self.sh_info = self._make_info(
            self.sharpen_tab, "Пояснение",
            "Реализованы ровно два высокочастотных метода: Unsharp Mask и Laplacian.\n"
            "Порог подавления шума применяется только к Unsharp Mask."
        )
        images = ttk.Frame(self.sharpen_tab)
        images.pack(fill="both", expand=True, padx=6, pady=6)
        self.sh_canvases = []
        for index, title in enumerate(("Исходное изображение", "Unsharp Mask", "Laplacian")):
            frame, canvas = self._make_image_panel(images, title)
            frame.grid(row=0, column=index, padx=6, pady=6, sticky="nsew")
            images.rowconfigure(0, weight=1)
            images.columnconfigure(index, weight=1)
            self.sh_canvases.append(canvas)

    def _add_scale(self, parent, row, text, start, end, variable, column, resolution):
        ttk.Label(parent, text=text).grid(row=row, column=0, sticky="w", padx=6, pady=4)
        label = ttk.Label(parent, text=str(variable.get()), width=6)
        ttk.Scale(
            parent, from_=start, to=end, orient="horizontal", variable=variable,
            command=lambda value: self._update_scale(variable, label, value, resolution),
        ).grid(row=row, column=column, sticky="ew", padx=6, pady=4)
        label.grid(row=row, column=2, sticky="w")
        parent.columnconfigure(column, weight=1)

    @staticmethod
    def _update_scale(variable, label, value, resolution):
        numeric = float(value)
        if resolution == 1:
            numeric = int(numeric)
        variable.set(numeric)
        label.config(text=f"{numeric:.1f}" if resolution < 1 else str(int(numeric)))

    @staticmethod
    def _make_info(parent, title, text):
        frame = ttk.LabelFrame(parent, text=title)
        frame.pack(fill="x", padx=6, pady=4)
        widget = tk.Text(frame, height=7, wrap="word")
        widget.pack(fill="x", padx=6, pady=6)
        widget.insert("1.0", text)
        widget.config(state="disabled")
        return widget

    def _make_image_panel(self, parent, title):
        frame = ttk.LabelFrame(parent, text=title)
        canvas = tk.Canvas(frame, bg="#202020", highlightthickness=0,
                           width=320, height=320)
        canvas.pack(padx=6, pady=6, fill="both", expand=True)
        canvas.source_image = None
        canvas.bind("<Configure>", lambda _event, target=canvas: self._redraw_canvas(target))
        return frame, canvas

    def open_image(self):
        path = filedialog.askopenfilename(
            title="Открыть изображение", initialdir=str(self.app_dir),
            filetypes=self.IMAGE_FILETYPES,
        )
        if not path:
            return
        try:
            img = load_image(path)
        except Exception as exc:
            messagebox.showerror("Ошибка загрузки изображения", str(exc))
            return

        self.original_image = img
        self.last_result = None
        self.th_otsu_result = self.th_mean_result = None
        self.sh_unsharp_result = self.sh_laplacian_result = None
        self._clear_canvases()
        self._show_image(self.th_canvases[0], img)
        self._show_image(self.sh_canvases[0], img)
        self._set_text(self.th_info, "Изображение загружено. Примените Otsu и средний порог для сравнения.")
        self._set_text(self.sh_info, "Изображение загружено. Примените Unsharp Mask и Laplacian для сравнения.")

    def apply_threshold(self):
        if self.original_image is None:
            messagebox.showwarning("Нет изображения", "Сначала откройте изображение.")
            return
        try:
            invert = bool(self.th_invert.get())
            t_otsu, res_otsu = apply_threshold(self.original_image, "otsu", invert=invert)
            t_mean, res_mean = apply_threshold(self.original_image, "mean", invert=invert)
            diff_percent = binary_difference_percent(res_otsu, res_mean)
        except Exception as exc:
            messagebox.showerror("Ошибка пороговой обработки", str(exc))
            return
        self.th_otsu_result, self.th_mean_result = res_otsu, res_mean
        self.last_result = res_otsu
        self._show_image(self.th_canvases[1], res_otsu)
        self._show_image(self.th_canvases[2], res_mean)
        stats_otsu, stats_mean = binary_stats(res_otsu), binary_stats(res_mean)
        info = (
            f"Метод 1: Otsu\nПорог: {t_otsu}\nБелых пикселей: {stats_otsu['white_percent']:.2f}%\n"
            f"Чёрных пикселей: {stats_otsu['black_percent']:.2f}%\n\n"
            f"Метод 2: Средний порог\nПорог: {t_mean}\n"
            f"Белых пикселей: {stats_mean['white_percent']:.2f}%\n"
            f"Чёрных пикселей: {stats_mean['black_percent']:.2f}%\n\n"
            f"Различие результатов: {diff_percent:.2f}% пикселей."
        )
        self._set_text(self.th_info, info)

    def apply_sharpening(self):
        if self.original_image is None:
            messagebox.showwarning("Нет изображения", "Сначала откройте изображение.")
            return
        amount, ksize, threshold = float(self.sh_amount.get()), int(self.sh_ksize.get()), int(self.sh_threshold.get())
        try:
            unsharp = apply_unsharp(self.original_image, amount, ksize, threshold)
            laplacian = apply_laplacian(self.original_image, amount, ksize)
        except Exception as exc:
            messagebox.showerror("Ошибка увеличения резкости", str(exc))
            return
        self.sh_unsharp_result, self.sh_laplacian_result = unsharp, laplacian
        self.last_result = unsharp
        self._show_image(self.sh_canvases[1], unsharp)
        self._show_image(self.sh_canvases[2], laplacian)
        self._set_text(
            self.sh_info,
            f"Unsharp Mask\nСила эффекта: {amount:.2f}\nРазмер размытия: {ksize}\n"
            f"Порог подавления шума: {threshold}\n\nLaplacian\n"
            f"Сила эффекта: {amount:.2f}\nРазмер ядра: {min(ksize, 7)}",
        )

    def save_last_result(self):
        self._save_image(self.last_result, "result.png")

    def _save_image(self, image, default_name):
        if image is None:
            messagebox.showwarning("Нет изображения", "Сначала выполните обработку.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".png", initialfile=default_name, initialdir=str(self.app_dir),
            filetypes=[("PNG", "*.png"), ("BMP", "*.bmp"), ("JPEG", "*.jpg *.jpeg")],
        )
        if not path:
            return
        try:
            save_image(image, path)
        except Exception as exc:
            messagebox.showerror("Ошибка сохранения", str(exc))

    def _clear_canvases(self):
        for canvas in self.th_canvases + self.sh_canvases:
            canvas.delete("all")
            canvas.image = None
            canvas.source_image = None

    def _show_image(self, canvas, image):
        if image is None:
            return
        canvas.source_image = image.copy()
        self._redraw_canvas(canvas)

    def _redraw_canvas(self, canvas):
        if canvas.source_image is None:
            return
        size = (max(1, canvas.winfo_width()), max(1, canvas.winfo_height()))
        display = fit_image(canvas.source_image.convert("RGB"), size, allow_upscale=True)
        photo = ImageTk.PhotoImage(display)
        canvas.delete("all")
        canvas.create_image(size[0] // 2, size[1] // 2, anchor="center", image=photo)
        canvas.image = photo

    @staticmethod
    def _set_text(widget, text):
        widget.config(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", text)
        widget.config(state="disabled")
