from django.urls import path

from . import views

urlpatterns = [
    path("", views.check_text, name="check_text"),
    path("scan/<int:pk>/", views.scan_result, name="scan_result"),
]
