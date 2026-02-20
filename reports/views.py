from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, F
from django.db.models.functions import TruncMonth

from .services import get_analytics
from .utils import get_date_range

import csv
from django.http import HttpResponse

from reportlab.pdfgen import canvas
from business.models import Sale
from admin_panel.models import BusinessUser


class AnalyticsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        business = user.business  # 1 business=specific user

        range_key = request.query_params.get("range")
        start_date = get_date_range(range_key)

        data = get_analytics(
            business=business,
            start_date=start_date
        )

        return Response(data)

class RevenueProfitGraphView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        range_key = request.GET.get("range", "6m")
        start_date = get_date_range(range_key)

        data = (
            Sale.objects.filter(
                product__business=request.user.business,
                created_at__gte=start_date
            )
            .annotate(month=TruncMonth("created_at"))
            .values("month")
            .annotate(
                revenue=Sum(F("quantity") * F("unit_price")),
                profit=Sum(
                    F("quantity") *
                    (F("unit_price") - F("product__cost_price"))
                )
            )
            .order_by("month")
        )

        return Response(list(data))


class ReportsCSVExportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        sales = Sale.objects.filter(product__business=request.user.business)

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="sales_report.csv"'

        writer = csv.writer(response)
        writer.writerow(["Product", "Quantity", "Unit Price", "Total", "Date"])

        for sale in sales:
            writer.writerow([
                sale.product.name,
                sale.quantity,
                sale.unit_price,
                sale.quantity * sale.unit_price,
                sale.created_at
            ])

        return response


class ReportsPDFExportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = 'attachment; filename="sales_report.pdf"'

        p = canvas.Canvas(response)
        p.drawString(100, 800, "Sales Report")

        y = 760
        sales = Sale.objects.filter(product__business=request.user.business)

        for sale in sales:
            line = f"{sale.product.name} | {sale.quantity} | {sale.unit_price}"
            p.drawString(100, y, line)
            y -= 20

        p.showPage()
        p.save()
        return response
