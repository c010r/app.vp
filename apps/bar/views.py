import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import CashRegister, CashSession, BarProduct, BarCategory, Sale, SaleItem
from .forms import OpenSessionForm, CloseSessionForm, BarProductForm, BarCategoryForm


def cashier_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_cashier:
            return redirect('accounts:login')
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
@cashier_required
def dashboard(request):
    registers = CashRegister.objects.filter(is_active=True)
    open_sessions = CashSession.objects.filter(status=CashSession.Status.OPEN).select_related(
        'register', 'opened_by'
    )
    return render(request, 'bar/dashboard.html', {
        'registers': registers,
        'open_sessions': open_sessions,
    })


@login_required
@cashier_required
def open_session(request, register_pk):
    register = get_object_or_404(CashRegister, pk=register_pk, is_active=True)

    if register.current_session:
        messages.warning(request, f'La caja "{register.name}" ya tiene una sesión abierta.')
        return redirect('bar:dashboard')

    form = OpenSessionForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        session = form.save(commit=False)
        session.register = register
        session.opened_by = request.user
        session.save()
        messages.success(request, f'Caja "{register.name}" abierta correctamente.')
        return redirect('bar:pos', session_pk=session.pk)

    return render(request, 'bar/open_session.html', {'form': form, 'register': register})


@login_required
@cashier_required
def close_session(request, session_pk):
    session = get_object_or_404(CashSession, pk=session_pk, status=CashSession.Status.OPEN)
    form = CloseSessionForm(request.POST or None, instance=session)

    if request.method == 'POST' and form.is_valid():
        session = form.save(commit=False)
        session.status = CashSession.Status.CLOSED
        session.closed_by = request.user
        session.closed_at = timezone.now()
        session.save()
        messages.success(request, 'Caja cerrada correctamente.')
        return redirect('bar:session_summary', session_pk=session.pk)

    total_sales = session.total_sales
    return render(request, 'bar/close_session.html', {
        'form': form,
        'session': session,
        'total_sales': total_sales,
    })


@login_required
@cashier_required
def pos(request, session_pk):
    """Punto de venta (POS) de la barra."""
    session = get_object_or_404(CashSession, pk=session_pk, status=CashSession.Status.OPEN)
    categories = BarCategory.objects.prefetch_related('barproduct_set')
    products = BarProduct.objects.filter(is_active=True, stock__gt=0).select_related('category')
    recent_sales = session.sales.order_by('-created_at')[:10]

    return render(request, 'bar/pos.html', {
        'session': session,
        'categories': categories,
        'products': products,
        'recent_sales': recent_sales,
    })


@login_required
@cashier_required
@require_POST
def create_sale(request, session_pk):
    """Endpoint AJAX para registrar una venta."""
    session = get_object_or_404(CashSession, pk=session_pk, status=CashSession.Status.OPEN)

    try:
        data = json.loads(request.body)
        items = data.get('items', [])
        payment_method = data.get('payment_method', 'efectivo')

        if not items:
            return JsonResponse({'error': 'No hay productos en la venta.'}, status=400)

        with transaction.atomic():
            total = 0
            sale_items = []
            for item in items:
                product = get_object_or_404(BarProduct, pk=item['product_id'])
                qty = int(item['quantity'])
                if product.stock < qty:
                    return JsonResponse(
                        {'error': f'Stock insuficiente para {product.name}.'}, status=400
                    )
                subtotal = product.price * qty
                total += subtotal
                sale_items.append((product, qty, product.price, subtotal))

            sale = Sale.objects.create(
                session=session,
                total=total,
                payment_method=payment_method,
                created_by=request.user,
            )
            for product, qty, unit_price, subtotal in sale_items:
                SaleItem.objects.create(
                    sale=sale, product=product, quantity=qty,
                    unit_price=unit_price, subtotal=subtotal,
                )
                product.stock -= qty
                product.save()

        return JsonResponse({'success': True, 'sale_id': sale.pk, 'total': str(sale.total)})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def session_summary(request, session_pk):
    session = get_object_or_404(CashSession, pk=session_pk)
    sales = session.sales.prefetch_related('items__product').order_by('-created_at')
    return render(request, 'bar/session_summary.html', {
        'session': session,
        'sales': sales,
    })


# ── Admin de Productos de Barra ───────────────────────────────────────────────

@login_required
def product_list(request):
    if not request.user.is_admin:
        return redirect('bar:dashboard')
    products = BarProduct.objects.select_related('category').order_by('category__name', 'name')
    return render(request, 'bar/product_list.html', {'products': products})


@login_required
def product_create(request):
    if not request.user.is_admin:
        return redirect('bar:dashboard')
    form = BarProductForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Producto creado.')
        return redirect('bar:product_list')
    return render(request, 'bar/product_form.html', {'form': form, 'action': 'Crear'})


@login_required
def product_update(request, pk):
    if not request.user.is_admin:
        return redirect('bar:dashboard')
    product = get_object_or_404(BarProduct, pk=pk)
    form = BarProductForm(request.POST or None, instance=product)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Producto actualizado.')
        return redirect('bar:product_list')
    return render(request, 'bar/product_form.html', {'form': form, 'action': 'Editar'})
