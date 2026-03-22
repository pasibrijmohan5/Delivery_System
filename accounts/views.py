import random
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings

User = get_user_model()


def register_view(request):
    if request.method == "POST":
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if password1 != password2:
            messages.error(request, "Passwords do not match")
            return redirect('accounts:register')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists")
            return redirect('accounts:register')

        otp = str(random.randint(100000, 999999))

        request.session['signup_data'] = {
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'password': password1,
        }
        request.session['signup_otp'] = otp

        send_mail(
            subject="Your LocalBite OTP Code",
            message=f"Your OTP for signup is: {otp}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )

        messages.success(request, "OTP sent to your email.")
        return redirect('accounts:verify_signup_otp')

    return render(request, 'accounts/register.html')


def verify_signup_otp(request):
    if request.method == "POST":
        entered_otp = request.POST.get("otp", "").strip()
        saved_otp = request.session.get("signup_otp")
        signup_data = request.session.get("signup_data")

        if not saved_otp or not signup_data:
            messages.error(request, "OTP session expired. Please register again.")
            return redirect("accounts:register")

        if entered_otp == saved_otp:
            user = User.objects.create_user(
                email=signup_data["email"],
                password=signup_data["password"],
                first_name=signup_data["first_name"],
                last_name=signup_data["last_name"],
            )
            user.save()

            request.session.pop("signup_otp", None)
            request.session.pop("signup_data", None)

            messages.success(request, "Account created successfully")
            return redirect("accounts:login")

        messages.error(request, "Invalid OTP. Please try again.")

    return render(request, "accounts/verify_signup_otp.html")


def resend_signup_otp(request):
    signup_data = request.session.get("signup_data")

    if not signup_data:
        messages.error(request, "Session expired. Please register again.")
        return redirect("accounts:register")

    otp = str(random.randint(100000, 999999))
    request.session["signup_otp"] = otp

    send_mail(
        subject="Your New LocalBite OTP Code",
        message=f"Your new OTP is: {otp}",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[signup_data["email"]],
        fail_silently=False,
    )

    messages.success(request, "A new OTP has been sent.")
    return redirect("accounts:verify_signup_otp")


def login_view(request):
    if request.user.is_authenticated:
        return redirect('main:home')

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = authenticate(request, email=email, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, "Welcome back! You're now signed in.")

            next_url = request.POST.get('next') or request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('main:home')
        else:
            messages.error(request, "Invalid email or password. Please try again.")

    return render(request, 'accounts/login.html')


def logout_view(request):
    logout(request)
    messages.success(request, "You have been successfully logged out.")
    return redirect('main:home')