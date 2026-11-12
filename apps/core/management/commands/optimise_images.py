"""
Shrink photos uploaded before automatic resizing existed.

    python manage.py optimise_images           # list what would change
    python manage.py optimise_images --apply   # back up originals, then shrink

Originals are copied to MEDIA_ROOT/originals/ (same folder structure) before
anything is replaced, so the command can always be undone by hand.
"""

import shutil
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from PIL import Image, ImageOps, UnidentifiedImageError

from apps.catalog.models import ProductImage
from apps.companies.models import Company
from apps.content.models import LeadershipMessage, SiteSettings
from apps.core.images import (
    LOGO_SIZE,
    PORTRAIT_SIZE,
    PRODUCT_PHOTO_SIZE,
    SAVE_OPTIONS,
    needs_work,
)
from apps.team.models import Employee

IMAGE_FIELDS = [
    (ProductImage, "image", PRODUCT_PHOTO_SIZE),
    (Company, "logo", LOGO_SIZE),
    (SiteSettings, "logo", LOGO_SIZE),
    (LeadershipMessage, "photo", PORTRAIT_SIZE),
    (Employee, "photo", PORTRAIT_SIZE),
]

BACKUP_FOLDER = "originals"


class Command(BaseCommand):
    help = "Turn uploaded photos upright and shrink oversized ones (dry run unless --apply)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Replace the files (originals are backed up first).",
        )

    def handle(self, *args, apply=False, **options):
        media_root = Path(settings.MEDIA_ROOT)
        changed = saved_bytes = 0

        for model, field_name, max_size in IMAGE_FIELDS:
            names = (
                model.objects.exclude(**{field_name: ""})
                .exclude(**{f"{field_name}__isnull": True})
                .values_list(field_name, flat=True)
                .distinct()
            )
            for name in names:
                path = media_root / name
                if not path.is_file():
                    self.stderr.write(f"Missing file: {name}")
                    continue
                result = self.optimise(path, max_size, media_root, apply)
                if result is None:
                    continue
                before, after = result
                changed += 1
                saved_bytes += before - after
                self.stdout.write(
                    f"{name}: {before // 1024} KB -> {after // 1024} KB"
                )

        verb = "Optimised" if apply else "Would optimise"
        self.stdout.write(
            self.style.SUCCESS(
                f"{verb} {changed} image(s), saving {saved_bytes // 1024} KB."
            )
        )
        if changed and not apply:
            self.stdout.write("Run again with --apply to replace the files.")

    def optimise(self, path, max_size, media_root, apply):
        """Return (old size, new size) for an image that needs work, else None."""
        try:
            with Image.open(path) as image:
                image_format = image.format
                if image_format not in SAVE_OPTIONS:
                    return None
                if not needs_work(image, max_size):
                    return None
                upright = ImageOps.exif_transpose(image)
                upright.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                if image_format == "JPEG" and upright.mode not in ("RGB", "L"):
                    upright = upright.convert("RGB")

                before = path.stat().st_size
                temporary = path.with_name(path.name + ".tmp")
                upright.save(temporary, format=image_format, **SAVE_OPTIONS[image_format])
        except (UnidentifiedImageError, Image.DecompressionBombError, OSError) as error:
            self.stderr.write(f"Skipped {path.name}: {error}")
            return None

        after = temporary.stat().st_size
        if after >= before:
            temporary.unlink()
            return None
        if apply:
            backup = media_root / BACKUP_FOLDER / path.relative_to(media_root)
            backup.parent.mkdir(parents=True, exist_ok=True)
            if not backup.exists():
                shutil.copy2(path, backup)
            temporary.replace(path)
        else:
            temporary.unlink()
        return before, after
