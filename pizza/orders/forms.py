from django import forms
from django.core.validators import RegexValidator
from django.utils.html import strip_tags


class OrderForm(forms.Form):
    first_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'auth-input',
            'placeholder': 'Імʼя'
        })
    )

    last_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'auth-input',
            'placeholder': 'Прізвище'
        })
    )

    email = forms.EmailField(
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'auth-input',
            'placeholder': 'Email',
            'readonly': 'readonly'
        })
    )

    company = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'auth-input',
            'placeholder': 'Компанія'
        })
    )

    address1 = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'auth-input',
            'placeholder': 'Адреса, рядок 1'
        })
    )

    address2 = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'auth-input',
            'placeholder': 'Адреса, рядок 2'
        })
    )

    city = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'auth-input',
            'placeholder': 'Місто'
        })
    )

    province = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'auth-input',
            'placeholder': 'Область / регіон'
        })
    )

    postal_code = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'auth-input',
            'placeholder': 'Поштовий індекс'
        })
    )

    phone = forms.CharField(
        max_length=15,
        required=False,
        validators=[
            RegexValidator(
                regex=r'^\+?\d{9,15}$',
                message='Введіть коректний номер телефону.'
            )
        ],
        widget=forms.TextInput(attrs={
            'class': 'auth-input',
            'placeholder': 'Телефон'
        })
    )

    delivery_instructions = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'auth-input order-textarea',
            'placeholder': 'Коментар до замовлення',
            'rows': 4
        })
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        if user and user.is_authenticated:
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['email'].initial = user.email
            self.fields['company'].initial = getattr(user, 'company', '')
            self.fields['address1'].initial = getattr(user, 'address1', '')
            self.fields['address2'].initial = getattr(user, 'address2', '')
            self.fields['city'].initial = getattr(user, 'city', '')
            self.fields['province'].initial = getattr(user, 'province', '')
            self.fields['postal_code'].initial = getattr(user, 'postal_code', '')
            self.fields['phone'].initial = getattr(user, 'phone', '')

    def clean(self):
        cleaned_data = super().clean()

        fields_to_clean = [
            'first_name',
            'last_name',
            'company',
            'address1',
            'address2',
            'city',
            'province',
            'postal_code',
            'phone',
            'delivery_instructions',
        ]

        for field in fields_to_clean:
            value = cleaned_data.get(field)

            if isinstance(value, str):
                cleaned_data[field] = strip_tags(value).strip()

        return cleaned_data