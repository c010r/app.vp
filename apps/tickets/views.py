from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.views.generic import ListView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db.models import Sum, Count
from .models import Event, TicketType, Ticket
from .forms import EventForm, TicketTypeForm, PurchaseForm


# ── Vistas Públicas (sin login) ───────────────────────────────────────────────

def public_event_list(request):
    events = Event.objects.filter(is_active=True).prefetch_related('ticket_types')
    return render(request, 'tickets/public_list.html', {'events': events})


def public_event_detail(request, pk):
    event = get_object_or_404(Event, pk=pk, is_active=True)
    ticket_types = event.ticket_types.filter(is_active=True)
    return render(request, 'tickets/public_detail.html', {
        'event': event,
        'ticket_types': ticket_types,
    })


# ── Compra (requiere login) ───────────────────────────────────────────────────

@login_required
def purchase_ticket(request, ticket_type_id):
    ticket_type = get_object_or_404(TicketType, pk=ticket_type_id, is_active=True)

    if ticket_type.is_sold_out:
        messages.error(request, 'Lo sentimos, este tipo de entrada esta agotado.')
        return redirect('tickets:public_event_detail', pk=ticket_type.event.pk)

    initial = {
        'buyer_name': request.user.get_full_name(),
        'buyer_email': request.user.email,
        'buyer_phone': request.user.phone,
    }
    form = PurchaseForm(ticket_type=ticket_type, data=request.POST or None, initial=initial)

    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            qty = form.cleaned_data['quantity']
            ticket = Ticket.objects.create(
                ticket_type=ticket_type,
                buyer_name=form.cleaned_data['buyer_name'],
                buyer_email=form.cleaned_data['buyer_email'],
                buyer_phone=form.cleaned_data.get('buyer_phone', ''),
                quantity=qty,
                unit_price=ticket_type.price,
                total=ticket_type.price * qty,
                payment_method=form.cleaned_data['payment_method'],
                sold_by=request.user,
                buyer_user=request.user,
            )
            ticket_type.sold += qty
            ticket_type.save()
        return redirect('tickets:purchase_success', pk=ticket.pk)

    return render(request, 'tickets/purchase.html', {
        'form': form,
        'ticket_type': ticket_type,
    })


def purchase_success(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    return render(request, 'tickets/purchase_success.html', {'ticket': ticket})


# ── Mis Entradas (cliente logueado) ──────────────────────────────────────────

@login_required
def my_tickets(request):
    tickets = Ticket.objects.filter(
        buyer_user=request.user
    ).select_related('ticket_type__event').order_by('-created_at')
    return render(request, 'tickets/my_tickets.html', {'tickets': tickets})


@login_required
def my_ticket_detail(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk, buyer_user=request.user)
    return render(request, 'tickets/my_ticket_detail.html', {'ticket': ticket})


# ── Vistas Admin ──────────────────────────────────────────────────────────────

class AdminEventListView(LoginRequiredMixin, ListView):
    model = Event
    template_name = 'tickets/admin_list.html'
    context_object_name = 'events'
    queryset = Event.objects.prefetch_related('ticket_types').order_by('-date')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_ticket_admin:
            return redirect('tickets:public_list')
        return super().dispatch(request, *args, **kwargs)


class AdminEventCreateView(LoginRequiredMixin, CreateView):
    model = Event
    form_class = EventForm
    template_name = 'tickets/event_form.html'
    success_url = reverse_lazy('tickets:admin_list')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_ticket_admin:
            return redirect('tickets:public_list')
        return super().dispatch(request, *args, **kwargs)


class AdminEventUpdateView(LoginRequiredMixin, UpdateView):
    model = Event
    form_class = EventForm
    template_name = 'tickets/event_form.html'
    success_url = reverse_lazy('tickets:admin_list')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_ticket_admin:
            return redirect('tickets:public_list')
        return super().dispatch(request, *args, **kwargs)


@login_required
def ticket_type_create(request, event_pk):
    event = get_object_or_404(Event, pk=event_pk)
    if not request.user.is_ticket_admin:
        return redirect('tickets:public_list')
    form = TicketTypeForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        tt = form.save(commit=False)
        tt.event = event
        tt.save()
        messages.success(request, 'Tipo de entrada creado.')
        return redirect('tickets:admin_list')
    return render(request, 'tickets/ticket_type_form.html', {'form': form, 'event': event})


@login_required
def ticket_type_update(request, pk):
    if not request.user.is_ticket_admin:
        return redirect('tickets:public_list')
    tt = get_object_or_404(TicketType, pk=pk)
    form = TicketTypeForm(request.POST or None, instance=tt)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Tipo de entrada actualizado.')
        return redirect('tickets:admin_list')
    return render(request, 'tickets/ticket_type_form.html', {'form': form, 'event': tt.event, 'editing': True})


@login_required
def admin_ticket_list(request):
    if not request.user.is_ticket_admin:
        return redirect('tickets:public_list')

    event_id = request.GET.get('event', '')
    status = request.GET.get('status', '')
    q = request.GET.get('q', '')

    tickets = Ticket.objects.select_related('ticket_type__event', 'sold_by', 'buyer_user').order_by('-created_at')

    if event_id:
        tickets = tickets.filter(ticket_type__event_id=event_id)
    if status:
        tickets = tickets.filter(status=status)
    if q:
        tickets = tickets.filter(buyer_name__icontains=q) | tickets.filter(buyer_email__icontains=q)

    events = Event.objects.all()
    summary = tickets.aggregate(total_revenue=Sum('total'), total_qty=Sum('quantity'), count=Count('id'))

    return render(request, 'tickets/admin_ticket_list.html', {
        'tickets': tickets,
        'events': events,
        'summary': summary,
        'selected_event': event_id,
        'selected_status': status,
        'q': q,
    })


@login_required
def mark_ticket_used(request, pk):
    if not request.user.is_ticket_admin:
        return redirect('tickets:public_list')
    ticket = get_object_or_404(Ticket, pk=pk)
    ticket.status = Ticket.Status.USED
    ticket.save()
    messages.success(request, f'Entrada marcada como usada.')
    return redirect('tickets:admin_ticket_list')


@login_required
def checkin_view(request):
    """Vista de check-in: busca entradas por codigo."""
    if not request.user.is_ticket_admin:
        return redirect('tickets:public_list')

    ticket = None
    code = request.GET.get('code', '').strip()

    if code:
        try:
            ticket = Ticket.objects.select_related('ticket_type__event').get(code=code)
        except Ticket.DoesNotExist:
            messages.error(request, f'No se encontro ninguna entrada con el codigo: {code}')

    if request.method == 'POST':
        ticket_pk = request.POST.get('ticket_pk')
        action = request.POST.get('action')
        t = get_object_or_404(Ticket, pk=ticket_pk)
        if action == 'use':
            t.status = Ticket.Status.USED
            t.save()
            messages.success(request, f'Entrada de {t.buyer_name} marcada como USADA.')
        elif action == 'cancel':
            t.status = Ticket.Status.CANCELLED
            t.save()
            messages.warning(request, f'Entrada cancelada.')
        return redirect('tickets:checkin')

    return render(request, 'tickets/checkin.html', {'ticket': ticket, 'code': code})


@login_required
def admin_event_detail(request, pk):
    """Detalle de evento con estadisticas."""
    if not request.user.is_ticket_admin:
        return redirect('tickets:public_list')
    event = get_object_or_404(Event, pk=pk)
    ticket_types = event.ticket_types.annotate(
        revenue=Sum('tickets__total'),
        buyers=Count('tickets'),
    )
    recent_tickets = Ticket.objects.filter(
        ticket_type__event=event
    ).select_related('ticket_type', 'buyer_user').order_by('-created_at')[:20]

    total_revenue = event.ticket_types.aggregate(
        total=Sum('tickets__total')
    )['total'] or 0
    total_sold = event.ticket_types.aggregate(
        total=Sum('sold')
    )['total'] or 0

    return render(request, 'tickets/admin_event_detail.html', {
        'event': event,
        'ticket_types': ticket_types,
        'recent_tickets': recent_tickets,
        'total_revenue': total_revenue,
        'total_sold': total_sold,
    })
