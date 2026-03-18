from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'admin', 'Administrador'
        TICKET_ADMIN = 'ticket_admin', 'Admin de Entradas'
        CASHIER = 'cashier', 'Cajero/Barman'
        VIEWER = 'viewer', 'Solo Lectura'

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.VIEWER)
    phone = models.CharField(max_length=20, blank=True)

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def __str__(self):
        return f'{self.get_full_name() or self.username} ({self.get_role_display()})'

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN or self.is_superuser

    @property
    def is_ticket_admin(self):
        return self.role in (self.Role.ADMIN, self.Role.TICKET_ADMIN) or self.is_superuser

    @property
    def is_cashier(self):
        return self.role in (self.Role.ADMIN, self.Role.CASHIER) or self.is_superuser
