import datetime
import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from apps.careers.forms import MAX_RESUME_SIZE
from apps.careers.models import Job, JobApplication

TEMP_MEDIA_ROOT = tempfile.mkdtemp()


def make_job(title, **kwargs):
    defaults = {
        "slug": title.lower().replace(" ", "-"),
        "description": f"{title} description",
        "is_published": True,
    }
    defaults.update(kwargs)
    return Job.objects.create(title=title, **defaults)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class CareersTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        today = timezone.localdate()
        cls.open_job = make_job(
            "Sales Officer", location="Multan",
            requirements="Graduate", responsibilities="Visit hospitals",
        )
        cls.future_deadline = make_job(
            "Area Manager", application_deadline=today + datetime.timedelta(days=5)
        )
        cls.draft = make_job("Draft Role", is_published=False)
        cls.expired = make_job(
            "Expired Role", application_deadline=today - datetime.timedelta(days=1)
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def application_data(self, **overrides):
        data = {
            "name": "Ali Raza",
            "email": "ali@example.com",
            "phone": "0301-7654321",
            "city": "Multan",
            "cover_letter": "I have five years of medical sales experience.",
            "website": "",
        }
        data.update(overrides)
        return data

    def test_only_open_published_jobs_are_listed(self):
        response = self.client.get(reverse("job_list"))
        self.assertContains(response, "Sales Officer")
        self.assertContains(response, "Area Manager")
        self.assertNotContains(response, "Draft Role")
        self.assertNotContains(response, "Expired Role")

    def test_no_openings_message(self):
        Job.objects.update(is_published=False)
        response = self.client.get(reverse("job_list"))
        self.assertContains(response, "No open positions right now")

    def test_detail_page_shows_job_information(self):
        response = self.client.get(self.open_job.get_absolute_url())
        self.assertContains(response, "Visit hospitals")
        self.assertContains(response, "Graduate")
        self.assertContains(response, 'enctype="multipart/form-data"')

    def test_draft_and_expired_jobs_return_404(self):
        for job in (self.draft, self.expired):
            with self.subTest(job=job.title):
                self.assertEqual(self.client.get(job.get_absolute_url()).status_code, 404)

    def test_valid_application_with_pdf_is_saved(self):
        resume = SimpleUploadedFile("My CV.pdf", b"%PDF-1.4 test", content_type="application/pdf")
        response = self.client.post(
            self.open_job.get_absolute_url(),
            self.application_data(resume=resume),
        )

        self.assertRedirects(response, reverse("job_application_success"))
        application = JobApplication.objects.get()
        self.assertEqual(application.job, self.open_job)
        self.assertEqual(application.name, "Ali Raza")
        # Stored under a random name, not the applicant's file name.
        self.assertTrue(application.resume.name.startswith("careers/resumes/"))
        self.assertNotIn("My CV", application.resume.name)
        self.assertTrue(application.resume.name.endswith(".pdf"))

    def test_application_without_resume_is_accepted(self):
        response = self.client.post(self.open_job.get_absolute_url(), self.application_data())
        self.assertRedirects(response, reverse("job_application_success"))
        self.assertEqual(JobApplication.objects.count(), 1)

    def test_required_fields_and_phone_are_validated(self):
        response = self.client.post(
            self.open_job.get_absolute_url(),
            self.application_data(name="", email="not-an-email", phone="abc"),
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This field is required")
        self.assertContains(response, "Enter a valid email address")
        self.assertContains(response, "Enter a valid phone number")
        self.assertEqual(JobApplication.objects.count(), 0)

    def test_disallowed_file_type_is_rejected(self):
        resume = SimpleUploadedFile("cv.exe", b"MZ\x90\x00", content_type="application/octet-stream")
        response = self.client.post(
            self.open_job.get_absolute_url(), self.application_data(resume=resume)
        )
        self.assertContains(response, "Upload your CV as a PDF or Word")
        self.assertEqual(JobApplication.objects.count(), 0)

    def test_renamed_file_with_wrong_content_is_rejected(self):
        resume = SimpleUploadedFile("cv.pdf", b"<html>not a pdf</html>")
        response = self.client.post(
            self.open_job.get_absolute_url(), self.application_data(resume=resume)
        )
        self.assertContains(response, "does not appear to be a valid")
        self.assertEqual(JobApplication.objects.count(), 0)

    def test_oversized_file_is_rejected(self):
        resume = SimpleUploadedFile("cv.pdf", b"%PDF" + b"0" * MAX_RESUME_SIZE)
        response = self.client.post(
            self.open_job.get_absolute_url(), self.application_data(resume=resume)
        )
        self.assertContains(response, "5 MB or smaller")
        self.assertEqual(JobApplication.objects.count(), 0)

    def test_cannot_apply_to_expired_job(self):
        response = self.client.post(self.expired.get_absolute_url(), self.application_data())
        self.assertEqual(response.status_code, 404)
        self.assertEqual(JobApplication.objects.count(), 0)

    def test_honeypot_application_is_discarded(self):
        response = self.client.post(
            self.open_job.get_absolute_url(),
            self.application_data(website="spam"),
        )
        self.assertRedirects(response, reverse("job_application_success"))
        self.assertEqual(JobApplication.objects.count(), 0)
