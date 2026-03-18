from django.db import models
from django.conf import settings


class Category(models.Model):
    name = models.CharField('Nombre', max_length=100)
    description = models.CharField('Descripción', max_length=200, blank=True)

    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['name']

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField('Nombre', max_length=200)
    description = models.TextField('Descripción', blank=True)
    sku = models.CharField('SKU', max_length=50, unique=True, blank=True)
    unit = models.CharField('Unidad', max_length=30, default='unidad')
    unit_cost = models.DecimalField('Costo unitario', max_digits=10, decimal_places=2, default=0)
    unit_price = models.DecimalField('Precio de venta', max_digits=10, decimal_places=2, default=0)
    stock = models.PositiveIntegerField('Stock actual', default=0)
    min_stock = models.PositiveIntegerField('Stock mínimo', default=5)
    is_active = models.BooleanField('Activo', default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['category', 'name']

    def __str__(self):
        return self.name

    @property
    def is_low_stock(self):
        return self.stock <= self.min_stock

    @property
    def stock_value(self):
        return self.stock * self.unit_cost


class StockMovement(models.Model):
    class MovementType(models.TextChoices):
        IN = 'in', 'Entrada'
        OUT = 'out', 'Salida'
        ADJUSTMENT = 'adjustment', 'Ajuste'

    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='movements')
    movement_type = models.CharField('Tipo', max_length=15, choices=MovementType.choices)
    quantity = models.IntegerField('Cantidad')
    stock_before = models.PositiveIntegerField('Stock anterior')
    stock_after = models.PositiveIntegerField('Stock posterior')
    unit_cost = models.DecimalField('Costo unitario', max_digits=10, decimal_places=2, default=0)
    reason = models.CharField('Motivo', max_length=200)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='stock_movements'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Movimiento de Stock'
        verbose_name_plural = 'Movimientos de Stock'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_movement_type_display()} - {self.product} ({self.quantity})'

    def save(self, *args, **kwargs):
        if not self.pk:
            self.stock_before = self.product.stock
            if self.movement_type == self.MovementType.IN:
                self.product.stock += self.quantity
            elif self.movement_type == self.MovementType.OUT:
                self.product.stock -= self.quantity
            else:
                self.product.stock = self.quantity
            self.stock_after = self.product.stock
            self.product.save()
        super().save(*args, **kwargs)
