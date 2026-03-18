import uuid
import qrcode
from io import BytesIO
from django.db import models
from django.core.files import File
from django.conf import settings


class Event(models.Model):
    name = models.CharField('Nombre', max_length=200)
    description = models.TextField('Descripción', blank=True)
    date = models.DateTimeField('Fecha y hora')
    venue = models.CharField('Lugar', max_length=200)
    image = models.ImageField('Imagen', upload_to='events/', blank=True, null=True)
    is_active = models.BooleanField('Activo', default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Evento'
        verbose_name_plural = 'Eventos'
        ordering = ['-date']

    def __str__(self):
        return self.name


class TicketType(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='ticket_types')
    name = models.CharField('Tipo', max_length=100)
    price = models.DecimalField('Precio', max_digits=10, decimal_places=2)
    capacity = models.PositiveIntegerField('Capacidad')
    sold = models.PositiveIntegerField('Vendidos', default=0)
    is_active = models.BooleanField('Activo', default=True)

    class Meta:
        verbose_name = 'Tipo de Entrada'
        verbose_name_plural = 'Tipos de Entrada'

    def __str__(self):
        return f'{self.event} - {self.name}'

    @property
    def available(self):
        return self.capacity - self.sold

    @property
    def is_sold_out(self):
        return self.available <= 0


class Ticket(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pendiente'
        CONFIRMED = 'confirmed', 'Confirmada'
        USED = 'used', 'Usada'
        CANCELLED = 'cancelled', 'Cancelada'

    code = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    ticket_type = models.ForeignKey(TicketType, on_delete=models.PROTECT, related_name='tickets')
    buyer_name = models.CharField('Nombre del comprador', max_length=200)
    buyer_email = models.CharField('Email', max_length=200)
    buyer_phone = models.CharField('Teléfono', max_length=30, blank=True)
    quantity = models.PositiveIntegerField('Cantidad', default=1)
    unit_price = models.DecimalField('Precio unitario', max_digits=10, decimal_places=2)
    total = models.DecimalField('Total', max_digits=10, decimal_places=2)
    payment_method = models.CharField('Medio de pago', max_length=50, default='efectivo')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.CONFIRMED)
    qr_image = models.ImageField('QR', upload_to='tickets/qr/', blank=True, null=True)
    buyer_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='tickets_purchased'
    )
    sold_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='tickets_sold'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Entrada'
        verbose_name_plural = 'Entradas'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.ticket_type} - {self.buyer_name} ({self.code})'

    def save(self, *args, **kwargs):
        if not self.unit_price:
            self.unit_price = self.ticket_type.price
        if not self.total:
            self.total = self.unit_price * self.quantity
        super().save(*args, **kwargs)
        if not self.qr_image:
            self._generate_qr()

    def _generate_qr(self):
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(str(self.code))
        qr.make(fit=True)
        img = qr.make_image(fill_color='black', back_color='white')
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        self.qr_image.save(f'qr_{self.code}.png', File(buffer), save=True)
