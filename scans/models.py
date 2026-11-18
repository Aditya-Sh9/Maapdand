from django.conf import settings
from django.db import models

from rules.verdicts import Verdict


class Product(models.Model):
    """A product is a set of label images (front, back, side...)."""
    name = models.CharField(max_length=200, blank=True)
    class Category(models.TextChoices):
        # Decides which extra rules apply later (food -> FSSAI, cosmetics -> veg/non-veg dot).
        FOOD = "food", "Food"
        COSMETICS = "cosmetics", "Cosmetics"
        OTHER = "other", "Other"

    category = models.CharField(max_length=100, choices=Category.choices, blank=True)
    is_imported = models.BooleanField(null=True, blank=True)  # null = unknown
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name or f"Product {self.pk}"


class LabelImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="labels/")
    quality_score = models.FloatField(null=True, blank=True)
    quality_ok = models.BooleanField(null=True, blank=True)
    ocr_text = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Scan(models.Model):
    """One run of the checks. Phase 1 only uses text mode (product is empty)."""

    class InputMode(models.TextChoices):
        IMAGE = "image", "Image"
        TEXT = "text", "Text"

    product = models.ForeignKey(Product, null=True, blank=True, on_delete=models.SET_NULL)
    input_mode = models.CharField(max_length=10, choices=InputMode.choices, default=InputMode.TEXT)
    raw_text = models.TextField(blank=True)
    overall_verdict = models.CharField(max_length=20, choices=Verdict.choices, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Scan {self.pk} ({self.overall_verdict or 'pending'})"


class ExtractedField(models.Model):
    """A value found on the label. We keep the original and any human correction."""
    scan = models.ForeignKey(Scan, on_delete=models.CASCADE, related_name="fields")
    field_name = models.CharField(max_length=50)
    value = models.TextField()
    confidence = models.FloatField(default=1.0)
    bbox = models.JSONField(null=True, blank=True)  # box on the image, used from Phase 3
    source_image = models.ForeignKey(LabelImage, null=True, blank=True, on_delete=models.SET_NULL)
    corrected_value = models.TextField(blank=True)

    @property
    def final_value(self):
        return self.corrected_value or self.value

    def __str__(self):
        return f"{self.field_name}={self.value[:30]}"
