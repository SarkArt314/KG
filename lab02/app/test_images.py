from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


def generate_samples(out_dir="test_images"):
    """Generate five reproducible sample images for variant 8."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    size = (512, 512)
    rng = np.random.default_rng(8)

    arr = np.full(size, 90, dtype=np.float32)
    arr += rng.normal(0, 18, size)
    yy, xx = np.ogrid[:size[0], :size[1]]
    mask = (yy - 256) ** 2 + (xx - 256) ** 2 <= 62**2
    arr[mask] = 205 + rng.normal(0, 8, int(mask.sum()))
    Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGB").save(
        out / "01_threshold_small_object_noise.png"
    )

    arr = np.full(size, 70, dtype=np.float32) + rng.normal(0, 4, size)
    rect = np.zeros(size, dtype=bool)
    rect[130:380, 120:420] = True
    arr[rect] = 190 + rng.normal(0, 4, int(rect.sum()))
    Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGB").save(
        out / "02_threshold_balanced_bimodal.png"
    )

    base = Image.new("L", size, 30)
    draw = ImageDraw.Draw(base)
    draw.line([60, 80, 430, 130], fill=220, width=6)
    draw.line([90, 420, 450, 360], fill=200, width=4)
    draw.ellipse([180, 180, 330, 330], outline=235, width=5)
    arr = np.asarray(base.filter(ImageFilter.GaussianBlur(2.0)), dtype=np.float32)
    arr += rng.normal(0, 12, size)
    Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGB").save(
        out / "03_sharpen_noisy_blurred.png"
    )

    base = Image.new("L", size, 40)
    draw = ImageDraw.Draw(base)
    for x in range(0, 512, 24):
        draw.line([x, 0, x, 512], fill=190, width=2)
    for y in range(0, 512, 48):
        draw.line([0, y, 512, y], fill=150, width=1)
    draw.rectangle([120, 120, 390, 390], outline=240, width=3)
    base.filter(ImageFilter.GaussianBlur(1.1)).convert("RGB").save(
        out / "04_sharpen_fine_details.png"
    )

    gradient = np.linspace(95, 135, size[1], dtype=np.float32)
    arr = np.tile(gradient, (size[0], 1))
    mask = (yy - 260) ** 2 + (xx - 200) ** 2 <= 70**2
    arr[mask] += 18
    arr += rng.normal(0, 2, size)
    Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGB").save(
        out / "05_low_contrast.png"
    )
    return out
