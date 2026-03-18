from django.contrib import admin
from .models import Event, TicketType, Ticket


class TicketTypeInline(admin.TabularInline):
    model = TicketType
    extra = 1


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'date', 'venue', 'is_active')
    list_filter = ('is_active',)
    inlines = [TicketTypeInline]


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('code', 'ticket_type', 'buyer_name', 'quantity', 'total', 'status', 'created_at')
    list_filter = ('status', 'ticket_type__event')
    search_fields = ('buyer_name', 'buyer_email', 'code')
    readonly_fields = ('code', 'qr_image')
