import unittest

import numpy as np
from PIL import Image

from app.sharpening import apply_laplacian, apply_unsharp
from app.test_images import generate_samples
from app.image_utils import fit_image
from app.thresholding import apply_threshold, binary_difference_percent, binary_stats


class ProcessingTests(unittest.TestCase):
    def setUp(self):
        pixels = np.zeros((32, 32), dtype=np.uint8)
        pixels[:, 16:] = 200
        self.image = Image.fromarray(pixels)

    def test_global_threshold_methods_return_binary_images(self):
        for method in ("otsu", "mean"):
            threshold, result = apply_threshold(self.image, method)
            self.assertGreaterEqual(threshold, 0)
            self.assertLessEqual(threshold, 255)
            self.assertEqual(set(np.unique(result)), {0, 255})

    def test_unknown_threshold_method_is_rejected(self):
        with self.assertRaises(ValueError):
            apply_threshold(self.image, "adaptive")

    def test_threshold_inversion_and_statistics(self):
        _, regular = apply_threshold(self.image, "mean")
        _, inverted = apply_threshold(self.image, "mean", invert=True)
        self.assertTrue(np.array_equal(np.asarray(regular), 255 - np.asarray(inverted)))
        stats = binary_stats(regular)
        self.assertEqual(stats["white"] + stats["black"], 32 * 32)
        self.assertAlmostEqual(stats["white_percent"] + stats["black_percent"], 100)

    def test_binary_difference_percent_rejects_different_sizes(self):
        with self.assertRaises(ValueError):
            binary_difference_percent(self.image, Image.new("L", (10, 10)))

    def test_binary_difference_percent_measures_changed_pixels(self):
        first = Image.fromarray(np.array([[0, 0], [255, 255]], dtype=np.uint8))
        second = Image.fromarray(np.array([[0, 255], [255, 255]], dtype=np.uint8))
        self.assertEqual(binary_difference_percent(first, second), 25.0)

    def test_sharpening_methods_preserve_size_and_rgb_mode(self):
        rgb = self.image.convert("RGB")
        for result in (apply_unsharp(rgb), apply_laplacian(rgb)):
            self.assertEqual(result.size, rgb.size)
            self.assertEqual(result.mode, "RGB")

    def test_fit_image_uses_viewport_bounds_and_preserves_aspect_ratio(self):
        image = Image.new("RGB", (1000, 500))
        fitted = fit_image(image, (300, 400))
        self.assertEqual(fitted.size, (300, 150))

    def test_fit_image_can_enlarge_small_images_for_preview(self):
        image = Image.new("RGB", (100, 50))
        fitted = fit_image(image, (300, 400), allow_upscale=True)
        self.assertEqual(fitted.size, (300, 150))

    def test_sample_generator_creates_five_images(self):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as temp_dir:
            output = generate_samples(temp_dir)
            self.assertEqual(len(list(Path(output).glob("*.png"))), 5)


if __name__ == "__main__":
    unittest.main()
