from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib import messages
from django.contrib.auth.decorators import login_required

User = get_user_model()

def register_view(request):
    if request.method == "POST":
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        email = request.POST['email']
        password1 = request.POST['password1']
        password2 = request.POST['password2']

        if password1 != password2:
            messages.error(request, "Passwords do not match")
            return redirect('accounts:register')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists")
            return redirect('accounts:register')

        user = User.objects.create_user(
            email=email,
            password=password1,
            first_name=first_name,
            last_name=last_name
        )
        user.save()

        messages.success(request, "Account created successfully")
        return redirect('accounts:login')

    return render(request, 'accounts/register.html')
def login_view(request):
    # If user is already authenticated → redirect to home
    if request.user.is_authenticated:
        return redirect('main:home')

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = authenticate(request, email=email, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, "Welcome back! You're now signed in.")
            
            # Handle ?next= parameter (very important!)
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('main:home')
        else:
            messages.error(request, "Invalid email or password. Please try again.")

    # GET request or failed POST → show the form
    return render(request, 'accounts/login.html', {
        # Optional context if you want to pre-fill or show something
        # 'next': request.GET.get('next', '')
    })


def logout_view(request):
    logout(request)
    messages.success(request, "You have been successfully logged out.")
    return redirect('main:home')

