# /contact/forms.py

from django import forms
from .models import ContactMessage

class ContactMessageForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['first_name', 'last_name', 'email', 'phone', 'message']
        widgets = {
            'first_name': forms.TextInput(attrs={'placeholder': 'Enter First Name'}),
            'last_name':  forms.TextInput(attrs={'placeholder': 'Enter Last Name'}),
            'email':      forms.EmailInput(attrs={'placeholder': 'Enter Email Address'}),
            'phone':      forms.TextInput(attrs={'placeholder': 'Enter Your Phone Number', 'maxlength': '10'}),
            'message':    forms.Textarea(attrs={'rows': 6, 'placeholder': 'Enter Your Message'}),
        }

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        if phone and not phone.isdigit():
            raise forms.ValidationError("Phone must contain digits only.")
        if phone and len(phone) not in (10, 11, 12, 13, 14, 15):
            # allow basic length range; primary India 10
            raise forms.ValidationError("Please enter a valid phone number.")
        return phone
