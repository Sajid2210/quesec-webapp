# /contact/views.py

from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import ContactMessageForm

def contact_view(request):
    if request.method == 'POST':
        form = ContactMessageForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Thank you! Your message has been sent.")
            return redirect('contact:contact')  # namespaced URL
        else:
            messages.error(request, "Please fix the errors and try again.")
    else:
        form = ContactMessageForm()

    return render(request, 'pages/contact.html', {'form': form})
