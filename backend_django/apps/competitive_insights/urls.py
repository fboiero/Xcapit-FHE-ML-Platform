"""
Competitive insights URL configuration.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CompanyMetricViewSet, CompetitiveReportViewSet, IndustryBenchmarkViewSet

router = DefaultRouter()
router.register(r"benchmarks", IndustryBenchmarkViewSet, basename="benchmark")
router.register(r"metrics", CompanyMetricViewSet, basename="company-metric")
router.register(r"reports", CompetitiveReportViewSet, basename="competitive-report")

urlpatterns = [
    path("", include(router.urls)),
]
