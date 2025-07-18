from django.shortcuts import render, redirect
from .models import *
from hospital.models import Hospital
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.db import IntegrityError
from django.contrib.auth.models import Group
from django.contrib.auth import authenticate, login, logout
# Create your views here.

def notification(request):
    return render(request, 'notification.html')


def user_profile(request):
    user = request.user
    return render(request, 'accounts/user_profile.html', {'user': user})


def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            return redirect(user_profile)  
        else:
            messages.error(request, 'Invalid email or password.')

    return render(request, 'accounts/login.html')

def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect(login_view)  



def staff_list_view(request):
    users = CustomUser.objects.exclude(account_type='patient').select_related('hospital')
    context = {
        'users': users,
    }
    return render(request, 'accounts/staff_list.html', context)


def add_user_view(request):
    hospitals = Hospital.objects.all()
    groups = Group.objects.all()  # Fetch all groups dynamically

    if request.method == 'POST':
        email = request.POST.get('email')
        username = request.POST.get('username')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        account_type = request.POST.get('account_type')
        hospital_id = request.POST.get('hospital')

        if not email or not username or not password1 or not password2 or not account_type or not hospital_id:
            messages.error(request, "Please fill in all required fields.")
            return render(request, 'accounts/register.html', {'hospitals': hospitals, 'groups': groups})

        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return render(request, 'accounts/register.html', {'hospitals': hospitals, 'groups': groups})

        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, "A user with this email already exists.")
            return render(request, 'accounts/register.html', {'hospitals': hospitals, 'groups': groups})

        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return render(request, 'accounts/register.html', {'hospitals': hospitals, 'groups': groups})

        try:
            user = CustomUser(
                email=email,
                username=username,
                patient_name=request.POST.get('patient_name'),
                hospital_id=hospital_id,
                account_type=account_type,
                gender=request.POST.get('gender'),
                phone_number=request.POST.get('phone_number'),
                residence=request.POST.get('residence'),
                town=request.POST.get('town'),
                county=request.POST.get('county'),
                country=request.POST.get('country'),
                password=make_password(password1)
            )
            user.save()
            print(f"User created: {user}")
            # Assign user to selected group
            try:
                group = Group.objects.get(name=account_type)
                user.groups.add(group)
            except Group.DoesNotExist:
                messages.warning(request, "User created, but group not found for assignment.")

            messages.success(request, "User created successfully.")
            return redirect('patient_list')

        except IntegrityError:
            messages.error(request, "There was an error creating the user.")
            return render(request, 'accounts/register.html', {'hospitals': hospitals, 'groups': groups})

    return render(request, 'accounts/register.html', {'hospitals': hospitals, 'groups': groups})