from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, F, Count, DecimalField
from django.db.models.functions import TruncDay
from django.utils.timezone import now
from datetime import timedelta

from business.models import Sale, Product, Notification
from admin_panel.models import BusinessUser


def get_business(user):
    try:
        return BusinessUser.objects.get(user=user).business
    except BusinessUser.DoesNotExist:
        from business.models import Business
        return Business.objects.get(owner=user)


class DashboardSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        business = get_business(request.user)
        today = now().date()
        week_ago = now() - timedelta(days=7)

        # total stock value (quantity * cost_price per product)
        stock_value = Product.objects.filter(business=business).aggregate(
            total=Sum(F('quantity') * F('cost_price'), output_field=DecimalField())
        )['total'] or 0

        # today's sales total
        today_sales = Sale.objects.filter(
            product__business=business,
            created_at__date=today
        ).aggregate(total=Sum('total_price'))['total'] or 0
        # yesterday's sales total

        yesterday = today - timedelta(days=1)
        yesterday_sales = Sale.objects.filter(
            product__business=business,
            created_at__date=yesterday
        ).aggregate(total=Sum('total_price'))['total'] or 0

        # calculate percentage change
        if yesterday_sales > 0:
            sales_change = ((float(today_sales) - float(yesterday_sales)) / float(yesterday_sales)) * 100
        else:
            sales_change = None  # no yesterday data to compare against

        # products sold today (sum of quantities)
        products_sold_today = Sale.objects.filter(
            product__business=business,
            created_at__date=today
        ).aggregate(total=Sum('quantity'))['total'] or 0

        # transactions today (number of sales records)
        transactions_today = Sale.objects.filter(
            product__business=business,
            created_at__date=today
        ).count()

        # low stock items
        low_stock_count = Product.objects.filter(
            business=business,
            quantity__lte=F('min_stock_level')
        ).count()

        # weekly sales — last 7 days grouped by day
        weekly_sales = (
            Sale.objects.filter(
                product__business=business,
                created_at__gte=week_ago
            )
            .annotate(day=TruncDay('created_at'))
            .values('day')
            .annotate(total=Sum('total_price'))
            .order_by('day')
        )

        weekly_data = [
            {
                'day': entry['day'].strftime('%a'),  # Mon, Tue etc
                'date': entry['day'].strftime('%d %b'),
                'sales': float(entry['total'])
            }
            for entry in weekly_sales
        ]

        #  sales by category
        category_sales = (
            Sale.objects.filter(product__business=business)
            .values('product__category__name')
            .annotate(total=Sum('total_price'))
            .order_by('-total')[:6]
        )

        category_data = [
            {
                'name': entry['product__category__name'] or 'Uncategorised',
                'value': float(entry['total'])
            }
            for entry in category_sales
        ]

        # top selling products (by quantity sold)
        top_products = (
            Sale.objects.filter(product__business=business)
            .values('product__name')
            .annotate(
                total_qty=Sum('quantity'),
                total_revenue=Sum('total_price')
            )
            .order_by('-total_qty')[:5]
        )

        top_products_data = [
            {
                'name': entry['product__name'],
                'quantity_sold': entry['total_qty'],
                'revenue': float(entry['total_revenue'])
            }
            for entry in top_products
        ]

        # recent sales (last 5)
        recent_sales = Sale.objects.filter(
            product__business=business
        ).select_related('product').order_by('-created_at')[:5]

        recent_sales_data = [
            {
                'product': s.product.name,
                'quantity': s.quantity,
                'total': float(s.total_price),
                'created_at': s.created_at.isoformat(),
            }
            for s in recent_sales
        ]

        # stock alerts (unread notifications)
        alerts = Notification.objects.filter(
            business=business,
            is_read=False
        ).select_related('product').order_by('-created_at')[:5]

        alerts_data = [
            {
                'id': a.id,
                'type': a.type,
                'message': a.message,
                'product_id': a.product.id,
                'product_name': a.product.name,
                'created_at': a.created_at.isoformat(),
            }
            for a in alerts
        ]

        return Response({
            'stats': {
                'stock_value': float(stock_value),
                'today_sales': float(today_sales),
                'yesterday_sales': float(yesterday_sales),
                'sales_change': round(sales_change, 1) if sales_change is not None else None,
                'products_sold_today': products_sold_today,
                'transactions_today': transactions_today,
                'low_stock_count': low_stock_count,
            },
            'weekly_sales': weekly_data,
            'category_sales': category_data,
            'top_products': top_products_data,
            'recent_sales': recent_sales_data,
            'alerts': alerts_data,
        })
