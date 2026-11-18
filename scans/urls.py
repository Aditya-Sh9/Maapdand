from django.urls import path

from . import views

urlpatterns = [
    path("check/text/", views.check_text, name="check_text"),
    path("upload/", views.upload_images, name="upload_images"),
    path("scan/<int:pk>/review/", views.scan_review, name="scan_review"),
    path("scan/<int:pk>/", views.scan_result, name="scan_result"),
    path("scan/<int:pk>/report/", views.scan_report, name="scan_report"),
    path("scans/", views.scan_history, name="scan_history"),
]
