import shutil
import tempfile
from io import BytesIO, StringIO
from pathlib import Path

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from PIL import Image

from apps.catalog.models import ProductImage
from apps.content.models import LeadershipMessage
from apps.core.images import EXIF_ORIENTATION, PORTRAIT_SIZE, PRODUCT_PHOTO_SIZE
from apps.core.testing import make_category, make_company, make_product

TEMP_MEDIA_ROOT = tempfile.mkdtemp(prefix="image-tests-")


def jpeg_upload(size, name="photo.jpg", orientation=None):
    image = Image.new("RGB", size, "teal")
    exif = Image.Exif()
    if orientation:
        exif[EXIF_ORIENTATION] = orientation
    buffer = BytesIO()
    image.save(buffer, format="JPEG", exif=exif)
    return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/jpeg")


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class UploadOptimisationTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.product = make_product(
            "Dialyzer", make_category("Dialysis"), make_company("Bain Medical")
        )

    def test_large_phone_photo_is_scaled_down(self):
        photo = ProductImage.objects.create(
            product=self.product, image=jpeg_upload((4000, 3000))
        )

        with Image.open(photo.image.path) as saved:
            self.assertEqual(saved.size, (PRODUCT_PHOTO_SIZE, 1200))
            self.assertEqual(saved.format, "JPEG")

    def test_sideways_photo_is_turned_upright(self):
        # Orientation 6: the camera was turned; the picture must be rotated 90°.
        message = LeadershipMessage.objects.create(
            name="CEO", designation="Chief Executive Officer", message="Hello",
            photo=jpeg_upload((800, 600), orientation=6),
        )

        with Image.open(message.photo.path) as saved:
            self.assertEqual(saved.size, (600, 800))
            self.assertEqual(saved.getexif().get(EXIF_ORIENTATION, 1), 1)

    def test_small_upright_photo_is_stored_unchanged(self):
        upload = jpeg_upload((640, 480))
        original_bytes = upload.read()
        upload.seek(0)

        photo = ProductImage.objects.create(product=self.product, image=upload)

        self.assertEqual(Path(photo.image.path).read_bytes(), original_bytes)

    def test_existing_files_are_not_reprocessed_on_later_saves(self):
        photo = ProductImage.objects.create(
            product=self.product, image=jpeg_upload((640, 480))
        )
        name = photo.image.name

        photo.alt_text = "Dialyzer"
        photo.save()

        self.assertEqual(photo.image.name, name)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class OptimiseImagesCommandTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        # Simulate a photo uploaded before automatic resizing existed.
        folder = Path(TEMP_MEDIA_ROOT) / "leadership"
        folder.mkdir(parents=True, exist_ok=True)
        self.path = folder / "old-ceo.jpg"
        Image.new("RGB", (3000, 3000), "navy").save(self.path, format="JPEG")
        LeadershipMessage.objects.create(
            name="CEO", designation="CEO", message="Hi", photo="leadership/old-ceo.jpg"
        )

    def run_command(self, *args):
        output = StringIO()
        call_command("optimise_images", *args, stdout=output, stderr=StringIO())
        return output.getvalue()

    def test_dry_run_changes_nothing(self):
        before = self.path.read_bytes()

        output = self.run_command()

        self.assertIn("Would optimise 1 image(s)", output)
        self.assertEqual(self.path.read_bytes(), before)

    def test_apply_backs_up_then_shrinks(self):
        before = self.path.read_bytes()

        self.run_command("--apply")

        backup = Path(TEMP_MEDIA_ROOT) / "originals" / "leadership" / "old-ceo.jpg"
        self.assertEqual(backup.read_bytes(), before)
        with Image.open(self.path) as shrunk:
            self.assertEqual(shrunk.size, (PORTRAIT_SIZE, PORTRAIT_SIZE))
        self.assertIn("Would optimise 0", self.run_command())
