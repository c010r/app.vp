from django import forms
from .models import CashSession, Sale, SaleItem, BarProduct, BarCategory


class OpenSessionForm(forms.ModelForm):
    class Meta:
        model = CashSession
        fields = ('opening_amount', 'notes')
        widgets = {
            'opening_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
        labels = {'opening_amount': 'Monto inicial en caja', 'notes': 'Observaciones'}


class CloseSessionForm(forms.ModelForm):
    class Meta:
        model = CashSession
        fields = ('closing_amount', 'notes')
        widgets = {
            'closing_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
        labels = {'closing_amount': 'Monto contado al cierre', 'notes': 'Observaciones'}


class SaleForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = ('payment_method', 'notes')
        widgets = {
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.TextInput(attrs={'class': 'form-control'}),
        }


class BarProductForm(forms.ModelForm):
    class Meta:
        model = BarProduct
        fields = ('category', 'name', 'price', 'stock', 'is_active')
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class BarCategoryForm(forms.ModelForm):
    class Meta:
        model = BarCategory
        fields = ('name',)
        widgets = {'name': forms.TextInput(attrs={'class': 'form-control'})}
