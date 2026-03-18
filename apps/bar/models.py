from django.db import models
from django.conf import settings


class CashRegister(models.Model):
    name = models.CharField('Nombre', max_length=100)
    location = models.CharField('Ubicación', max_length=100, blank=True)
    is_active = models.BooleanField('Activa', default=True)

    class Meta:
        verbose_name = 'Caja'
        verbose_name_plural = 'Cajas'

    def __str__(self):
        return self.name

    @property
    def current_session(self):
        return self.sessions.filter(status=CashSession.Status.OPEN).first()


class CashSession(models.Model):
    class Status(models.TextChoices):
        OPEN = 'open', 'Abierta'
        CLOSED = 'closed', 'Cerrada'

    register = models.ForeignKey(CashRegister, on_delete=models.PROTECT, related_name='sessions')
    opened_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='sessions_opened'
    )
    closed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='sessions_closed'
    )
    opened_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    opening_amount = models.DecimalField('Monto apertura', max_digits=10, decimal_places=2, default=0)
    closing_amount = models.DecimalField('Monto cierre', max_digits=10, decimal_places=2, null=True, blank=True)
    notes = models.TextField('Observaciones', blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.OPEN)

    class Meta:
        verbose_name = 'Sesión de Caja'
        verbose_name_plural = 'Sesiones de Caja'
        ordering = ['-opened_at']

    def __str__(self):
        return f'{self.register} - {self.opened_at.strftime("%d/%m/%Y %H:%M")}'

    @property
    def total_sales(self):
        return self.sales.aggregate(
            total=models.Sum('total')
        )['total'] or 0


class BarCategory(models.Model):
    name = models.CharField('Nombre', max_length=100)

    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'

    def __str__(self):
        return self.name


class BarProduct(models.Model):
    category = models.ForeignKey(BarCategory, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField('Nombre', max_length=200)
    price = models.DecimalField('Precio', max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField('Stock', default=0)
    is_active = models.BooleanField('Activo', default=True)

    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['category', 'name']

    def __str__(self):
        return self.name


class Sale(models.Model):
    class PaymentMethod(models.TextChoices):
        CASH = 'efectivo', 'Efectivo'
        DEBIT = 'debito', 'Débito'
        CREDIT = 'credito', 'Crédito'
        TRANSFER = 'transferencia', 'Transferencia'

    session = models.ForeignKey(CashSession, on_delete=models.PROTECT, related_name='sales')
    total = models.DecimalField('Total', max_digits=10, decimal_places=2)
    payment_method = models.CharField(
        'Medio de pago', max_length=20,
        choices=PaymentMethod.choices, default=PaymentMethod.CASH
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='bar_sales'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.CharField('Notas', max_length=200, blank=True)

    class Meta:
        verbose_name = 'Venta'
        verbose_name_plural = 'Ventas'
        ordering = ['-created_at']

    def __str__(self):
        return f'Venta #{self.pk} - ${self.total}'


class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(BarProduct, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField('Cantidad')
    unit_price = models.DecimalField('Precio unitario', max_digits=10, decimal_places=2)
    subtotal = models.DecimalField('Subtotal', max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        self.subtotal = self.unit_price * self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.product} x{self.quantity}'
