from django import forms
from .models import CatMenu, NavMenu

class CatMenuForm(forms.ModelForm):
    class Meta:
        model = CatMenu
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(CatMenuForm, self).__init__(*args, **kwargs)
        # Sirf un menus ko dikhao jo khud kisi ke child nahi hain
        self.fields['parent'].queryset = CatMenu.objects.filter(parent__isnull=True)

    class Media:
        js = ('admin/js/catmenu_toggle.js',)

class NavMenuForm(forms.ModelForm):
    class Meta:
        model = NavMenu
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(NavMenuForm, self).__init__(*args, **kwargs)
        # Sirf un menus ko dikhao jo khud kisi ke child nahi hain
        self.fields['parent'].queryset = NavMenu.objects.filter(parent__isnull=True)

    class Media:
        js = ('admin/js/catmenu_toggle.js',)