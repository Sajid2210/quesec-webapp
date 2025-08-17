from django import forms

class EmailLoginForm(forms.Form):
    email = forms.EmailField()

class OTPVerifyForm(forms.Form):
    otp = forms.CharField(max_length=6)
