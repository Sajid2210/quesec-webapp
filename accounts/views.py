from django.shortcuts import render, redirect
from .models import CustomUser, EmailOTP
from .forms import EmailLoginForm, OTPVerifyForm
from django.contrib import messages
from django.contrib.auth import login, logout
from django.core.mail import send_mail
from django.contrib.auth.decorators import login_required
from django.conf import settings
import logging
import random
from orders.models import Order

logger = logging.getLogger(__name__)

def login_request(request):
    if request.method == 'POST':
        form = EmailLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = CustomUser.objects.get(email=email)
            except CustomUser.DoesNotExist:
                messages.error(request, "Email not registered.")
                return redirect('login_page')

            otp = str(random.randint(100000, 999999))
            EmailOTP.objects.create(user=user, otp_code=otp)

            # --- Never crash on email failure ---
            try:
                send_mail(
                    subject="Your Quesec OTP Login Code",
                    message=f"Your OTP is: {otp}",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=False,
                )
                messages.info(request, "OTP sent to your email.")
            except Exception as e:
                logger.error("OTP email send failed: %s", e)
                print(f"[DEV ONLY] OTP for {user.email}: {otp}")
                messages.warning(
                    request,
                    "We couldn't send the email right now. Please check console for OTP in development."
                )

            request.session['otp_user_id'] = user.id
            return redirect('verify_otp')
    else:
        form = EmailLoginForm()

    return render(request, 'login.html', {'form': form})


def verify_otp(request):
    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        user_id = request.session.get('otp_user_id')

        if not user_id:
            messages.error(request, "Session expired. Please login again.")
            return redirect('login_page')

        try:
            user = CustomUser.objects.get(id=user_id)
            latest_otp = EmailOTP.objects.filter(user=user).order_by('-created_at').first()

            if latest_otp and latest_otp.otp_code == entered_otp:
                login(request, user)
                messages.success(request, "Logged in successfully.")
                request.session.pop('otp_user_id', None)
                return redirect('home')
            else:
                messages.error(request, "Invalid OTP. Please try again.")
                return render(request, 'verify_otp.html')

        except CustomUser.DoesNotExist:
            messages.error(request, "Invalid user.")
            return redirect('login_page')

    return render(request, 'verify_otp.html')


def logout_view(request):
    logout(request)
    return redirect('home')


@login_required(login_url='login_page')
def my_account(request):
    """
    Sirf logged-in user ke orders fetch honge.
    """
    orders = (
        Order.objects.filter(user=request.user)
        .order_by('-created_at')
        .select_related()
        .prefetch_related('items__product')
    )
    total_orders = orders.count()

    context = {
        "orders": orders,
        "total_orders": total_orders,
    }
    return render(request, 'my-account.html', context)
