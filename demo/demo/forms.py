from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Config


class SignUpForm(UserCreationForm):
    email = forms.EmailField(max_length=254, help_text='Required. Inform a valid email address.')
    benchmark = forms.ChoiceField(choices=[('b1', 'tpcc'), ('b2', 'tpch')], widget=forms.Select())
    class Meta:
        model = User
        fields = ('username', 'email', 'benchmark', 'password1', 'password2')

class TpccForm(forms.Form):
    shared_buffers = forms.ChoiceField(choices=[('1', '3'), ('2', '9'), ('3', '27')], widget=forms.Select(), 
    help_text="Sets the amount of memory the database server uses for shared memory buffers.", 
    initial="128MB")
    effective_io_concurrency = forms.ChoiceField(choices=[('1', '1'), ('2', '2')], widget=forms.Select(),
    help_text="Sets the number of concurrent disk I/O operations that PostgreSQL expects can be executed simultaneously",
    initial="3")

