from django.urls import path
from .views import login_request, verify_otp, logout_view, my_account

urlpatterns = [
    path('login/', login_request, name='login_page'),
    path('verify-otp/', verify_otp, name='verify_otp'),
    path('logout/', logout_view, name='logout'),
    path('my-account/', my_account, name='my_account'),
]
