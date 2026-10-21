import ctypes

from app.gui import Application


def enable_dpi_awareness():
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except (AttributeError, OSError):
        pass


def main():
    enable_dpi_awareness()
    Application().mainloop()


if __name__ == "__main__":
    main()
