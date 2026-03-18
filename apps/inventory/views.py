from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Product, Category, StockMovement
from .forms import ProductForm, CategoryForm, StockMovementForm


def inventory_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_ticket_admin:
            return redirect('accounts:login')
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
@inventory_required
def product_list(request):
    q = request.GET.get('q', '')
    category_id = request.GET.get('category', '')
    low_stock = request.GET.get('low_stock', '')

    products = Product.objects.select_related('category').filter(is_active=True)

    if q:
        products = products.filter(Q(name__icontains=q) | Q(sku__icontains=q))
    if category_id:
        products = products.filter(category_id=category_id)
    if low_stock:
        products = [p for p in products if p.is_low_stock]

    categories = Category.objects.all()
    return render(request, 'inventory/product_list.html', {
        'products': products,
        'categories': categories,
        'q': q,
        'selected_category': category_id,
    })


@login_required
@inventory_required
def product_create(request):
    form = ProductForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Producto creado correctamente.')
        return redirect('inventory:product_list')
    return render(request, 'inventory/product_form.html', {'form': form, 'action': 'Crear'})


@login_required
@inventory_required
def product_update(request, pk):
    product = get_object_or_404(Product, pk=pk)
    form = ProductForm(request.POST or None, instance=product)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Producto actualizado.')
        return redirect('inventory:product_list')
    return render(request, 'inventory/product_form.html', {'form': form, 'action': 'Editar', 'product': product})


@login_required
@inventory_required
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    movements = product.movements.order_by('-created_at')[:30]
    return render(request, 'inventory/product_detail.html', {
        'product': product,
        'movements': movements,
    })


@login_required
@inventory_required
def stock_movement(request, pk):
    product = get_object_or_404(Product, pk=pk)
    form = StockMovementForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        movement = form.save(commit=False)
        movement.product = product
        movement.created_by = request.user
        movement.save()
        messages.success(request, f'Movimiento registrado. Stock actual: {product.stock}')
        return redirect('inventory:product_detail', pk=product.pk)
    return render(request, 'inventory/stock_movement.html', {'form': form, 'product': product})


@login_required
@inventory_required
def movement_list(request):
    movements = StockMovement.objects.select_related('product', 'created_by').order_by('-created_at')[:100]
    return render(request, 'inventory/movement_list.html', {'movements': movements})
