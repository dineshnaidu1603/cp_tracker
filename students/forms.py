from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate
from .models import CustomUser

class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(label="Email")  # Change the label to 'Email'

    def clean(self):
        email = self.cleaned_data.get("username")  # Get email instead of username
        password = self.cleaned_data.get("password")

        if email and password:
            self.user_cache = authenticate(email=email, password=password)
            if self.user_cache is None:
                raise forms.ValidationError("Invalid email or password.")
        return self.cleaned_data
