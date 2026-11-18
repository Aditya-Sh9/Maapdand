"""Clean up a photo before OCR, and judge whether it is good enough to read.

Only Pillow is used (already a dependency), so there is nothing extra to install.
"""
from PIL import Image, ImageFilter, ImageOps, ImageStat

# Tesseract reads small text badly, so very small images are enlarged to about this width.
TARGET_WIDTH = 2000
# Longest side below this (pixels) means the text is too small to read. A starting guess; tune on real labels.
MIN_SIDE_PX = 800
# Edge-variance below this means the photo is blurry. Also a guess to tune on real labels.
MIN_SHARPNESS = 60.0


def load_image(path):
    """Open an image and apply its EXIF rotation (phone photos are often stored sideways)."""
    img = Image.open(path)
    return ImageOps.exif_transpose(img)


def preprocess(img):
    """Grayscale -> enlarge if small -> stretch contrast -> sharpen. Returns a new image."""
    gray = ImageOps.grayscale(img)
    if gray.width < TARGET_WIDTH:
        scale = TARGET_WIDTH / gray.width
        gray = gray.resize((TARGET_WIDTH, int(gray.height * scale)), Image.LANCZOS)
    gray = ImageOps.autocontrast(gray, cutoff=1)
    return gray.filter(ImageFilter.SHARPEN)


def assess_quality(img):
    """Return (score 0..1, ok, reasons). Judged on the original, not the enlarged copy,
    because enlarging makes any image look smoother than it really is."""
    reasons = []
    # Longest side, so a wide crop of one label strip is not rejected for being short.
    if max(img.size) < MIN_SIDE_PX:
        reasons.append("Image resolution is too low.")

    # Sharp photos have strong edges, so the edge-filtered image varies a lot.
    edges = ImageOps.grayscale(img).filter(ImageFilter.FIND_EDGES)
    # Pillow leaves the 1px border unfiltered, which would fake "edges" on a blank image.
    edges = edges.crop((1, 1, edges.width - 1, edges.height - 1))
    sharpness = ImageStat.Stat(edges).var[0]
    if sharpness < MIN_SHARPNESS:
        reasons.append("Image looks blurry.")

    score = min(sharpness / (MIN_SHARPNESS * 3), 1.0)
    return round(score, 2), not reasons, reasons
