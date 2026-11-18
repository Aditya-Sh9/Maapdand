from django import forms

from .models import Product


class UploadForm(forms.Form):
    """The text fields on the upload page. The image files are read straight from
    request.FILES in the view, because Django's form field takes one file by default."""

    name = forms.CharField(max_length=200, required=False, label="Product name (optional)")
    category = forms.ChoiceField(
        choices=[("", "Not sure")] + Product.Category.choices, required=False
    )
    is_imported = forms.ChoiceField(
        choices=[("", "Not sure"), ("yes", "Yes"), ("no", "No")], required=False,
        label="Imported product?",
    )
    use_anyway = forms.BooleanField(
        required=False, label="Use images even if the quality check complains"
    )

    def imported_value(self):
        """Turn the dropdown text into True / False / None (unknown)."""
        return {"yes": True, "no": False}.get(self.cleaned_data["is_imported"])
