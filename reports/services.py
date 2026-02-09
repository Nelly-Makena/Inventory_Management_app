from django.db.models import Sum, F, DecimalField
from django.db.models.functions import TruncMonth

from business.models import Sale


def get_analytics(business, start_date):
    sales = (
        Sale.objects
        .filter(business=business, created_at__gte=start_date)
        .select_related('product')
    )

    total_revenue = sales.aggregate(
        revenue=Sum(
            F('quantity') * F('product__unit_price'),
            output_field=DecimalField()
        )
    )['revenue'] or 0

    total_cost = sales.aggregate(
        cost=Sum(
            F('quantity') * F('product__cost_price'),
            output_field=DecimalField()
        )
    )['cost'] or 0

    net_profit = total_revenue - total_cost

    profit_margin = (
        (net_profit / total_revenue) * 100
        if total_revenue > 0 else 0
    )

    monthly = (
        sales
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(
            revenue=Sum(
                F('quantity') * F('product__unit_price'),
                output_field=DecimalField()
            ),
            profit=Sum(
                F('quantity') *
                (F('product__unit_price') - F('product__cost_price')),
                output_field=DecimalField()
            )
        )
        .order_by('month')
    )

    return {
        "total_revenue": float(total_revenue),
        "net_profit": float(net_profit),
        "profit_margin": round(float(profit_margin), 2),
        "monthly": list(monthly),
    }
