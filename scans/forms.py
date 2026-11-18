from django import forms

from .models import Product


class UploadForm(forms.Form):
    """The text fields on the upload page. The image files are read straight from
    request.FILES in the view, because Django's form field takes one file by default."""

    name = forms.CharField(max_length=200, required=False, label="Product name (optional)")
    category = forms.ChoiceField(
        choices=Product.Category.choices + [("", "Not sure")], required=False, initial="",
        widget=forms.RadioSelect,  # shown as pill buttons; one tap on a phone
    )
    is_imported = forms.ChoiceField(
        choices=[("no", "No"), ("yes", "Yes"), ("", "Not sure")], required=False, initial="",
        label="Is it imported?", widget=forms.RadioSelect,
    )
    use_anyway = forms.BooleanField(
        required=False, label="Use these images anyway. I understand the reading may be less accurate."
    )

    def imported_value(self):
        """Turn the dropdown text into True / False / None (unknown)."""
        return {"yes": True, "no": False}.get(self.cleaned_data["is_imported"])
