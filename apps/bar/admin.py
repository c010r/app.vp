from django.contrib import admin
from .models import CashRegister, CashSession, BarCategory, BarProduct, Sale, SaleItem


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0
    readonly_fields = ('subtotal',)


@admin.register(CashRegister)
class CashRegisterAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'is_active')


@admin.register(CashSession)
class CashSessionAdmin(admin.ModelAdmin):
    list_display = ('register', 'opened_by', 'opened_at', 'status', 'opening_amount', 'closing_amount')
    list_filter = ('status', 'register')
    readonly_fields = ('opened_at', 'closed_at')


@admin.register(BarProduct)
class BarProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'stock', 'is_active')
    list_filter = ('category', 'is_active')
    list_editable = ('price', 'stock')


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('pk', 'session', 'total', 'payment_method', 'created_by', 'created_at')
    list_filter = ('payment_method', 'session__register')
    inlines = [SaleItemInline]
    readonly_fields = ('created_at',)
