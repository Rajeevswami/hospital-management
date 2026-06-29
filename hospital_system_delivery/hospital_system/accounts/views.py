from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from core.decorators import role_required
from .forms import StaffCreationForm, LoginForm
from .models import User


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:home')

    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = authenticate(
            request,
            username=form.cleaned_data['username'],
            password=form.cleaned_data['password'],
        )
        if user is not None and user.is_active:
            login(request, user)
            return redirect('dashboard:home')
        messages.error(request, 'Invalid username or password.')
    return render(request, 'accounts/login.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    return redirect('accounts:login')


@login_required
@role_required('ADMIN')
def staff_list(request):
    staff = User.objects.exclude(role='ADMIN').order_by('role', 'first_name')
    return render(request, 'accounts/staff_list.html', {'staff': staff})


@login_required
@role_required('ADMIN')
def staff_create(request):
    form = StaffCreationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Staff account created successfully.')
        return redirect('accounts:staff_list')
    return render(request, 'accounts/staff_form.html', {'form': form})
