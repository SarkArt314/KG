import cv2
import numpy as np

from .image_utils import cv_bgr_to_pil, pil_to_cv_bgr


def _normalize_ksize(value, max_value=31):
    """Make a kernel size odd and keep it within the supported range."""
    ksize = max(1, min(int(value), max_value))
    if ksize % 2 == 0:
        ksize = ksize + 1 if ksize < max_value else ksize - 1
    return max(1, ksize)


def unsharp_mask_bgr(bgr, amount=1.0, ksize=5, threshold=0):
    """Sharpen using original + amount * (original - Gaussian blur)."""
    ksize = _normalize_ksize(ksize, max_value=31)
    blurred = cv2.GaussianBlur(bgr, (ksize, ksize), 0)
    sharpened = cv2.addWeighted(
        bgr, 1.0 + float(amount), blurred, -float(amount), 0
    )

    if threshold > 0:
        diff = cv2.absdiff(bgr, blurred).astype(np.int16)
        mask = np.all(diff <= int(threshold), axis=2)
        sharpened[mask] = bgr[mask]
    return sharpened


def laplacian_sharpen_bgr(bgr, amount=1.0, ksize=3):
    """Sharpen only the LAB luminance channel with a Laplacian."""
    ksize = _normalize_ksize(ksize, max_value=7)
    lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)
    l_channel, a_channel, b_channel = cv2.split(lab)
    l_float = l_channel.astype(np.float32)
    laplacian = cv2.Laplacian(l_float, cv2.CV_32F, ksize=ksize)
    sharp_l = cv2.addWeighted(l_float, 1.0, laplacian, -float(amount), 0.0)
    sharp_l = np.clip(sharp_l, 0, 255).astype(np.uint8)
    return cv2.cvtColor(
        cv2.merge([sharp_l, a_channel, b_channel]), cv2.COLOR_LAB2BGR
    )


def apply_unsharp(img, amount=1.0, ksize=5, threshold=0):
    return cv_bgr_to_pil(
        unsharp_mask_bgr(
            pil_to_cv_bgr(img), amount=amount, ksize=ksize, threshold=threshold
        )
    )


def apply_laplacian(img, amount=1.0, ksize=3):
    return cv_bgr_to_pil(
        laplacian_sharpen_bgr(pil_to_cv_bgr(img), amount=amount, ksize=ksize)
    )
