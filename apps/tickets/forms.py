from django import forms
from .models import Event, TicketType, Ticket


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ('name', 'description', 'date', 'venue', 'image', 'is_active')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'venue': forms.TextInput(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class TicketTypeForm(forms.ModelForm):
    class Meta:
        model = TicketType
        fields = ('name', 'price', 'capacity', 'is_active')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'capacity': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class PurchaseForm(forms.Form):
    PAYMENT_CHOICES = [
        ('efectivo', 'Efectivo'),
        ('debito', 'Débito'),
        ('credito', 'Crédito'),
        ('transferencia', 'Transferencia'),
    ]

    buyer_name = forms.CharField(
        label='Nombre completo',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    buyer_email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
    )
    buyer_phone = forms.CharField(
        label='Teléfono',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    quantity = forms.IntegerField(
        label='Cantidad',
        min_value=1,
        initial=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
    )
    payment_method = forms.ChoiceField(
        label='Medio de pago',
        choices=PAYMENT_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    def __init__(self, ticket_type=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ticket_type = ticket_type

    def clean_quantity(self):
        qty = self.cleaned_data['quantity']
        if self.ticket_type and qty > self.ticket_type.available:
            raise forms.ValidationError(
                f'Solo hay {self.ticket_type.available} entradas disponibles.'
            )
        return qty
