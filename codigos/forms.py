from django import forms
from .models import Items, calculoFlotilla
from django.contrib.auth.models import User


class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'password', 'confirm_password']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            raise forms.ValidationError("Passwords do not match")
        else:
            return cleaned_data
        
class loginForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)

# forms para agregar codigos
class CodigoForm(forms.ModelForm):
    class Meta:
        model = Items
        fields = '__all__'
        labels = {
            # nombre de las campos del modelo : etiqueta que se mostrara en el formulario
            'Codigo': 'Codigo',
            'nombre': 'Nombre',
            'categoria': 'Categoria',
        }
        widgets = {
            # widgets para los campos del modelo y sus atributos
            'categoria': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'incendio, robo, etc...'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'codo ranurado 3"'}),
            'codigo': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'A15001'}),
        }
   
