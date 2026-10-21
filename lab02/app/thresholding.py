import cv2
import numpy as np
from PIL import Image

from .image_utils import ensure_l


def pil_to_gray_cv(img):
    return np.asarray(ensure_l(img))


def otsu_threshold(gray):
    threshold_value, binary = cv2.threshold(
        gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )
    return int(threshold_value), binary


def mean_threshold(gray):
    threshold_value = int(round(float(gray.mean())))
    _, binary = cv2.threshold(gray, threshold_value, 255, cv2.THRESH_BINARY)
    return threshold_value, binary


def apply_threshold(img, method, invert=False):
    """Apply Otsu or mean global thresholding to a PIL image."""
    gray = pil_to_gray_cv(img)
    method = method.lower()

    if method == "otsu":
        threshold_value, binary = otsu_threshold(gray)
    elif method == "mean":
        threshold_value, binary = mean_threshold(gray)
    else:
        raise ValueError(f"Неизвестный метод пороговой обработки: {method}")

    if invert:
        binary = cv2.bitwise_not(binary)
    return threshold_value, Image.fromarray(binary)


def binary_stats(binary_img):
    arr = np.asarray(binary_img.convert("L"))
    total = int(arr.size)
    white = int(np.count_nonzero(arr > 127))
    black = total - white
    return {
        "white": white,
        "black": black,
        "white_percent": 100.0 * white / total if total else 0.0,
        "black_percent": 100.0 * black / total if total else 0.0,
    }


def binary_difference_percent(img1, img2):
    """Return the percentage of pixels that differ between binary images."""
    a = np.asarray(img1.convert("L"))
    b = np.asarray(img2.convert("L"))
    if a.shape != b.shape:
        raise ValueError("Размеры бинарных изображений должны совпадать.")

    diff = cv2.absdiff(a, b)
    changed = int(np.count_nonzero(diff))
    return 100.0 * changed / diff.size if diff.size else 0.0
