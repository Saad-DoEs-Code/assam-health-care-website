import uuid
from pathlib import Path

from django import forms

from apps.inquiries.forms import HoneypotMixin, validate_phone_number

from .models import JobApplication

MAX_RESUME_SIZE = 5 * 1024 * 1024  # 5 MB
ALLOWED_RESUME_EXTENSIONS = (".pdf", ".doc", ".docx")

# Leading bytes of each allowed format, so a renamed executable or image is
# rejected even if its extension looks right. .doc is the legacy OLE format;
# .docx is a ZIP archive.
RESUME_SIGNATURES = {
    ".pdf": (b"%PDF",),
    ".doc": (b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1",),
    ".docx": (b"PK\x03\x04",),
}


class JobApplicationForm(HoneypotMixin, forms.ModelForm):
    class Meta:
        model = JobApplication
        fields = ["name", "email", "phone", "city", "cover_letter", "resume"]

        labels = {
            "name": "Full name",
            "cover_letter": "Cover letter",
            "resume": "CV / résumé",
        }

        help_texts = {
            "resume": "PDF or Word document, up to 5 MB.",
        }

        widgets = {
            "name": forms.TextInput(attrs={"autocomplete": "name"}),
            "email": forms.EmailInput(attrs={"autocomplete": "email"}),
            "phone": forms.TextInput(
                attrs={
                    "type": "tel",
                    "autocomplete": "tel",
                    "placeholder": "e.g. 0300-1234567",
                }
            ),
            "city": forms.TextInput(attrs={"autocomplete": "address-level2"}),
            "cover_letter": forms.Textarea(
                attrs={
                    "rows": 6,
                    "maxlength": 5000,
                    "placeholder": "Briefly describe your experience and why you are interested in this role.",
                }
            ),
            "resume": forms.ClearableFileInput(
                attrs={"accept": ".pdf,.doc,.docx"}
            ),
        }

    def clean_phone(self):
        return validate_phone_number(self.cleaned_data["phone"].strip())

    def clean_cover_letter(self):
        cover_letter = self.cleaned_data.get("cover_letter", "")
        if len(cover_letter) > 5000:
            raise forms.ValidationError(
                "Please keep your cover letter under 5,000 characters."
            )
        return cover_letter

    def clean_resume(self):
        resume = self.cleaned_data.get("resume")
        if not resume:
            return resume

        extension = Path(resume.name).suffix.lower()
        if extension not in ALLOWED_RESUME_EXTENSIONS:
            raise forms.ValidationError(
                "Upload your CV as a PDF or Word (.doc, .docx) file."
            )

        if resume.size > MAX_RESUME_SIZE:
            raise forms.ValidationError("Your CV must be 5 MB or smaller.")

        header = resume.read(8)
        resume.seek(0)
        if not header.startswith(RESUME_SIGNATURES[extension]):
            raise forms.ValidationError(
                "This file does not appear to be a valid PDF or Word document."
            )

        # Store under a random name so uploaded CVs cannot be found by
        # guessing applicants' names.
        resume.name = f"{uuid.uuid4().hex}{extension}"
        return resume
