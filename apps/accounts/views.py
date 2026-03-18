from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.shortcuts import redirect, render
from .models import User
from .forms import LoginForm, UserForm, RegisterForm


class CustomLoginView(LoginView):
    form_class = LoginForm
    template_name = 'accounts/login.html'

    def get_success_url(self):
        user = self.request.user
        if user.is_cashier and not user.is_ticket_admin:
            return reverse_lazy('bar:dashboard')
        if user.is_ticket_admin:
            return reverse_lazy('tickets:admin_list')
        return reverse_lazy('tickets:my_tickets')


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('accounts:login')


def register(request):
    if request.user.is_authenticated:
        return redirect('tickets:public_list')
    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect('tickets:public_list')
    return render(request, 'accounts/register.html', {'form': form})


# ── Admin de usuarios ─────────────────────────────────────────────────────────

class UserListView(LoginRequiredMixin, ListView):
    model = User
    template_name = 'accounts/user_list.html'
    context_object_name = 'users'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_admin:
            return redirect('/')
        return super().dispatch(request, *args, **kwargs)


class UserCreateView(LoginRequiredMixin, CreateView):
    model = User
    form_class = UserForm
    template_name = 'accounts/user_form.html'
    success_url = reverse_lazy('accounts:user_list')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_admin:
            return redirect('/')
        return super().dispatch(request, *args, **kwargs)


class UserUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserForm
    template_name = 'accounts/user_form.html'
    success_url = reverse_lazy('accounts:user_list')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_admin:
            return redirect('/')
        return super().dispatch(request, *args, **kwargs)
