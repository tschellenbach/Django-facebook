from django import forms
from django.contrib.auth.models import User


class SignupForm(forms.Form):

    username = forms.CharField()
    email = forms.EmailField()
    first_name = forms.CharField()
    password1 = forms.CharField()

    def clean(self):
        data = self.cleaned_data
        data['username'] = 'Test form'
        data['password1'] = 'password'
        return data