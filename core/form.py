from django import forms
from .models import Pessoa


class PessoaForm(forms.ModelForm):
    class Meta:
        model = Pessoa
        fields = "__all__"


class DeletarForm(forms.Form):
    pass


class ReValidarForm(forms.Form):
    pass

