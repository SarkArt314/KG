from PIL import Image, ImageOps
import numpy as np


def load_image(path):
    """Load an image and normalize its mode for processing."""
    with Image.open(path) as source:
        img = ImageOps.exif_transpose(source)

        if img.mode == "P":
            img = img.convert("RGBA" if "transparency" in img.info else "RGB")

        if img.mode in ("RGBA", "LA"):
            rgba = img.convert("RGBA")
            background = Image.new("RGB", rgba.size, (255, 255, 255))
            background.paste(rgba, mask=rgba.getchannel("A"))
            return background

        if img.mode not in ("RGB", "L"):
            return img.convert("RGB")

        return img.copy()


def save_image(img, path):
    """Save a PIL image, converting palette images to RGB first."""
    if img.mode == "P":
        img = img.convert("RGB")
    img.save(path)


def ensure_rgb(img):
    return img if img.mode == "RGB" else img.convert("RGB")


def ensure_l(img):
    return img if img.mode == "L" else img.convert("L")


def fit_image(img, max_size=360, allow_upscale=False):
    """Resize an image to fit the requested bounds while preserving its aspect ratio."""
    width, height = img.size
    if isinstance(max_size, int):
        max_width = max_height = max_size
    else:
        max_width, max_height = max_size
    scale = min(max_width / width, max_height / height)
    if not allow_upscale:
        scale = min(scale, 1.0)
    if scale == 1.0:
        return img.copy()

    new_size = (max(1, int(width * scale)), max(1, int(height * scale)))
    return img.resize(new_size, Image.Resampling.LANCZOS)


def pil_to_cv_bgr(img):
    rgb = np.asarray(ensure_rgb(img))
    return rgb[:, :, ::-1].copy()


def cv_bgr_to_pil(bgr):
    if bgr.dtype != np.uint8:
        bgr = np.clip(bgr, 0, 255).astype(np.uint8)
    if bgr.ndim == 2:
        return Image.fromarray(bgr)
    return Image.fromarray(bgr[:, :, ::-1].copy())
