from django.urls import path
from .views import (
    AnalyticsView,
    RevenueProfitGraphView,
    ReportsCSVExportView,
    ReportsPDFExportView,
)
urlpatterns = [
    path('analytics/', AnalyticsView.as_view()),
    path("graph/", RevenueProfitGraphView.as_view()),
    path("export/csv/", ReportsCSVExportView.as_view()),
    path("export/pdf/", ReportsPDFExportView.as_view()),
]



