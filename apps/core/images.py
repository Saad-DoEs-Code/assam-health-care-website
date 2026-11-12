"""
Shrinking of uploaded photos.

Photos taken on a phone are often 4000 pixels wide and several megabytes,
far more than any page shows, and slow to load on mobile data. They also
store their rotation separately (EXIF), so some browsers show them sideways.
Each image field calls optimise_upload() when a new file is saved: the photo
is turned upright and scaled down to fit max_size, keeping its format.
"""

from io import BytesIO
from pathlib import Path

from django.core.files.base import ContentFile
from PIL import Image, ImageOps, UnidentifiedImageError

# Longest side, in pixels, for each kind of upload. About twice the largest
# size each image is shown at, for sharp results on high-resolution screens.
PRODUCT_PHOTO_SIZE = 1600
PORTRAIT_SIZE = 1200
LOGO_SIZE = 600

# EXIF tag that says how a camera photo must be rotated to appear upright.
EXIF_ORIENTATION = 0x0112

SAVE_OPTIONS = {
    "JPEG": {"quality": 85, "optimize": True, "progressive": True},
    "PNG": {"optimize": True},
    "WEBP": {"quality": 85},
}


def needs_work(image, max_size):
    """True when an image is larger than max_size or stored rotated."""
    rotated = image.getexif().get(EXIF_ORIENTATION, 1) != 1
    return rotated or max(image.size) > max_size


def optimise_upload(field_file, max_size):
    """
    Turn a newly uploaded image upright and scale it down to max_size.

    Files already in storage are left alone, as are formats other than
    JPEG, PNG and WebP and anything Pillow cannot read; the form's own
    validation has already decided whether the file is acceptable.
    """
    if not field_file or getattr(field_file, "_committed", True):
        return

    try:
        field_file.seek(0)
        with Image.open(field_file) as image:
            image_format = image.format
            if image_format not in SAVE_OPTIONS:
                return
            if not needs_work(image, max_size):
                return
            upright = ImageOps.exif_transpose(image)
            upright.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            if image_format == "JPEG" and upright.mode not in ("RGB", "L"):
                upright = upright.convert("RGB")
            output = BytesIO()
            upright.save(output, format=image_format, **SAVE_OPTIONS[image_format])
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError):
        field_file.seek(0)
        return

    name = Path(field_file.name).name
    field_file.save(name, ContentFile(output.getvalue()), save=False)
