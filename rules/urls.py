from django.urls import path

from . import views

urlpatterns = [
    path("rules/", views.rule_list, name="rule_list"),
    path("documents/", views.document_list, name="document_list"),
    path("documents/<slug:slug>/", views.document_file, name="document_file"),
]
