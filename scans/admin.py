from django.contrib import admin

from .models import ExtractedField, LabelImage, Product, Scan

admin.site.register(Product)
admin.site.register(LabelImage)
admin.site.register(Scan)
admin.site.register(ExtractedField)
