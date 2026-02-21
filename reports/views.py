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
from business.models import Sale, Business
from admin_panel.models import BusinessUser


def get_business(user):
    # works for every role
    try:
        return BusinessUser.objects.get(user=user).business
    except BusinessUser.DoesNotExist:
        return Business.objects.get(owner=user)


class AnalyticsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        business = get_business(request.user)
        range_key = request.query_params.get("range")
        start_date = get_date_range(range_key)
        data = get_analytics(business=business, start_date=start_date)
        return Response(data)


class RevenueProfitGraphView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        business = get_business(request.user)
        range_key = request.GET.get("range", "6m")
        start_date = get_date_range(range_key)

        data = (
            Sale.objects.filter(
                product__business=business,
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
        business = get_business(request.user)
        sales = Sale.objects.filter(
            product__business=business
        ).order_by('-created_at')

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
                sale.created_at.strftime('%d %b %Y, %H:%M'),
            ])

        return response


class ReportsPDFExportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        business = get_business(request.user)
        sales = Sale.objects.filter(
            product__business=business
        ).order_by('-created_at')

        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = 'attachment; filename="sales_report.pdf"'

        p = canvas.Canvas(response)
        p.setFont("Helvetica-Bold", 16)
        p.drawString(100, 800, f"Sales Report — {business.name}")
        p.setFont("Helvetica", 10)
        p.drawString(100, 780, f"Generated: {__import__('django.utils.timezone', fromlist=['now']).now().strftime('%d %b %Y, %H:%M')}")

        # table header
        y = 750
        p.setFont("Helvetica-Bold", 10)
        p.drawString(100, y, "Product")
        p.drawString(280, y, "Qty")
        p.drawString(330, y, "Unit Price")
        p.drawString(430, y, "Total")
        p.drawString(510, y, "Date")
        y -= 15
        p.line(100, y, 560, y)
        y -= 15

        p.setFont("Helvetica", 9)
        for sale in sales:
            if y < 60:
                p.showPage()
                y = 800
                p.setFont("Helvetica", 9)
            p.drawString(100, y, sale.product.name[:25])
            p.drawString(280, y, str(sale.quantity))
            p.drawString(330, y, f"KES {sale.unit_price}")
            p.drawString(430, y, f"KES {sale.quantity * sale.unit_price}")
            p.drawString(510, y, sale.created_at.strftime('%d %b %Y'))
            y -= 18

        p.showPage()
        p.save()
        return response