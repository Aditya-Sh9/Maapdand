from django.urls import path

from . import views

urlpatterns = [
    path("rules/", views.rule_list, name="rule_list"),
]
