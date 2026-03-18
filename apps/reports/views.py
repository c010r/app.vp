from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q
from django.db.models.functions import TruncDate, TruncMonth
from django.utils import timezone
from datetime import timedelta, date
import json

from apps.tickets.models import Ticket, Event
from apps.bar.models import Sale, CashSession, SaleItem
from apps.inventory.models import Product, StockMovement


def reports_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_ticket_admin:
            return redirect('accounts:login')
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
@reports_required
def dashboard(request):
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    # Resumen general
    tickets_today = Ticket.objects.filter(
        created_at__date=today, status=Ticket.Status.CONFIRMED
    ).aggregate(count=Count('id'), revenue=Sum('total'))

    bar_today = Sale.objects.filter(
        created_at__date=today
    ).aggregate(count=Count('id'), revenue=Sum('total'))

    low_stock_count = sum(1 for p in Product.objects.filter(is_active=True) if p.is_low_stock)

    # Ventas por día (últimos 7 días) - Entradas
    ticket_daily = list(
        Ticket.objects.filter(created_at__date__gte=week_ago, status=Ticket.Status.CONFIRMED)
        .annotate(day=TruncDate('created_at'))
        .values('day')
        .annotate(total=Sum('total'), count=Count('id'))
        .order_by('day')
    )

    # Ventas por día (últimos 7 días) - Barra
    bar_daily = list(
        Sale.objects.filter(created_at__date__gte=week_ago)
        .annotate(day=TruncDate('created_at'))
        .values('day')
        .annotate(total=Sum('total'), count=Count('id'))
        .order_by('day')
    )

    # Top productos de barra
    top_bar_products = (
        SaleItem.objects
        .filter(sale__created_at__date__gte=month_ago)
        .values('product__name')
        .annotate(total_qty=Sum('quantity'), total_revenue=Sum('subtotal'))
        .order_by('-total_revenue')[:10]
    )

    # Top eventos
    top_events = (
        Ticket.objects
        .filter(status=Ticket.Status.CONFIRMED)
        .values('ticket_type__event__name')
        .annotate(total_tickets=Sum('quantity'), total_revenue=Sum('total'))
        .order_by('-total_revenue')[:5]
    )

    chart_labels = [str(r['day']) for r in ticket_daily]
    chart_ticket_data = [float(r['total'] or 0) for r in ticket_daily]

    bar_labels = [str(r['day']) for r in bar_daily]
    chart_bar_data = [float(r['total'] or 0) for r in bar_daily]

    return render(request, 'reports/dashboard.html', {
        'tickets_today': tickets_today,
        'bar_today': bar_today,
        'low_stock_count': low_stock_count,
        'top_bar_products': top_bar_products,
        'top_events': top_events,
        'chart_labels': json.dumps(chart_labels),
        'chart_ticket_data': json.dumps(chart_ticket_data),
        'bar_labels': json.dumps(bar_labels),
        'chart_bar_data': json.dumps(chart_bar_data),
    })


@login_required
@reports_required
def tickets_report(request):
    date_from = request.GET.get('from', str(date.today() - timedelta(days=30)))
    date_to = request.GET.get('to', str(date.today()))

    tickets = (
        Ticket.objects
        .filter(created_at__date__gte=date_from, created_at__date__lte=date_to)
        .select_related('ticket_type__event', 'sold_by')
        .order_by('-created_at')
    )

    summary = tickets.aggregate(
        total_tickets=Sum('quantity'),
        total_revenue=Sum('total'),
        count=Count('id'),
    )

    by_event = (
        tickets.values('ticket_type__event__name')
        .annotate(qty=Sum('quantity'), revenue=Sum('total'))
        .order_by('-revenue')
    )

    return render(request, 'reports/tickets_report.html', {
        'tickets': tickets,
        'summary': summary,
        'by_event': by_event,
        'date_from': date_from,
        'date_to': date_to,
    })


@login_required
@reports_required
def bar_report(request):
    date_from = request.GET.get('from', str(date.today() - timedelta(days=30)))
    date_to = request.GET.get('to', str(date.today()))

    sessions = (
        CashSession.objects
        .filter(opened_at__date__gte=date_from, opened_at__date__lte=date_to)
        .select_related('register', 'opened_by', 'closed_by')
        .prefetch_related('sales')
        .order_by('-opened_at')
    )

    sales = Sale.objects.filter(
        created_at__date__gte=date_from, created_at__date__lte=date_to
    )
    summary = sales.aggregate(
        total_revenue=Sum('total'),
        count=Count('id'),
    )

    by_payment = (
        sales.values('payment_method')
        .annotate(total=Sum('total'), count=Count('id'))
        .order_by('-total')
    )

    top_products = (
        SaleItem.objects
        .filter(sale__created_at__date__gte=date_from, sale__created_at__date__lte=date_to)
        .values('product__name')
        .annotate(qty=Sum('quantity'), revenue=Sum('subtotal'))
        .order_by('-revenue')[:15]
    )

    return render(request, 'reports/bar_report.html', {
        'sessions': sessions,
        'summary': summary,
        'by_payment': by_payment,
        'top_products': top_products,
        'date_from': date_from,
        'date_to': date_to,
    })


@login_required
@reports_required
def inventory_report(request):
    products = Product.objects.select_related('category').filter(is_active=True).order_by('category__name', 'name')
    total_value = sum(p.stock_value for p in products)
    low_stock = [p for p in products if p.is_low_stock]

    recent_movements = StockMovement.objects.select_related(
        'product', 'created_by'
    ).order_by('-created_at')[:50]

    return render(request, 'reports/inventory_report.html', {
        'products': products,
        'total_value': total_value,
        'low_stock': low_stock,
        'recent_movements': recent_movements,
    })
