import random
from datetime import datetime, timedelta

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib import messages
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags

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
        request.session['signup_otp_expiry'] = (
            datetime.now() + timedelta(minutes=5)
        ).isoformat()

        subject = "Your OTP Code"
        from_email = "localbite512@gmail.com"
        to = [email]

        html_content = f"""
        <div style="font-family: Arial, sans-serif; padding: 24px; background: #f8fafc;">
            <div style="max-width: 520px; margin: auto; background: white; padding: 32px; border-radius: 16px; border: 1px solid #e5e7eb;">
                <h2 style="margin: 0 0 16px; color: #111827;">Verify your LocalBite account</h2>
                <p style="color: #4b5563; font-size: 15px; margin-bottom: 20px;">
                    Use the OTP below to complete your signup:
                </p>
                <div style="margin: 24px 0; text-align: center;">
                    <span style="display: inline-block; font-size: 32px; font-weight: 700; letter-spacing: 6px; color: #00cc99;">
                        {otp}
                    </span>
                </div>
                <p style="color: #6b7280; font-size: 14px; margin-top: 20px;">
                    This code expires in 5 minutes.
                </p>
                <p style="color: #9ca3af; font-size: 12px; margin-top: 24px;">
                    If you did not request this, you can ignore this email.
                </p>
            </div>
        </div>
        """

        text_content = strip_tags(html_content)

        msg = EmailMultiAlternatives(subject, text_content, from_email, to)
        msg.attach_alternative(html_content, "text/html")
        msg.send()

        messages.success(request, "OTP sent to your email.")
        return redirect('accounts:verify_signup_otp')

    return render(request, 'accounts/register.html')


def verify_signup_otp(request):
    if request.method == "POST":
        entered_otp = request.POST.get("otp", "").strip()
        saved_otp = request.session.get("signup_otp")
        signup_data = request.session.get("signup_data")
        expiry = request.session.get("signup_otp_expiry")

        if not saved_otp or not signup_data or not expiry:
            messages.error(request, "OTP session expired. Please register again.")
            return redirect("accounts:register")

        if datetime.now() > datetime.fromisoformat(expiry):
            request.session.pop("signup_otp", None)
            request.session.pop("signup_otp_expiry", None)
            messages.error(request, "OTP expired. Please request a new one.")
            return redirect("accounts:verify_signup_otp")

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
            request.session.pop("signup_otp_expiry", None)

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
    request.session["signup_otp_expiry"] = (
        datetime.now() + timedelta(minutes=5)
    ).isoformat()

    subject = "Your New LocalBite OTP Code"
    from_email = "localbite512@gmail.com"
    to = [signup_data["email"]]

    html_content = f"""
    <div style="font-family: Arial, sans-serif; padding: 24px; background: #f8fafc;">
        <div style="max-width: 520px; margin: auto; background: white; padding: 32px; border-radius: 16px; border: 1px solid #e5e7eb;">
            <h2 style="margin: 0 0 16px; color: #111827;">Your new LocalBite OTP</h2>
            <p style="color: #4b5563; font-size: 15px; margin-bottom: 20px;">
                Use this new OTP to continue your signup:
            </p>
            <div style="margin: 24px 0; text-align: center;">
                <span style="display: inline-block; font-size: 32px; font-weight: 700; letter-spacing: 6px; color: #00cc99;">
                    {otp}
                </span>
            </div>
            <p style="color: #6b7280; font-size: 14px; margin-top: 20px;">
                This code expires in 5 minutes.
            </p>
        </div>
    </div>
    """

    text_content = strip_tags(html_content)

    msg = EmailMultiAlternatives(subject, text_content, from_email, to)
    msg.attach_alternative(html_content, "text/html")
    msg.send()

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