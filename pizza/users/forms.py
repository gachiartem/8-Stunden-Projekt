from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.validators import RegexValidator
from django.utils.html import strip_tags


User = get_user_model()


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'auth-input',
            'placeholder': 'Email'
        })
    )

    first_name = forms.CharField(
        required=True,
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'auth-input',
            'placeholder': 'Імʼя'
        })
    )

    last_name = forms.CharField(
        required=True,
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'auth-input',
            'placeholder': 'Прізвище'
        })
    )

    password1 = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'auth-input',
            'placeholder': 'Пароль'
        })
    )

    password2 = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'auth-input',
            'placeholder': 'Повторіть пароль'
        })
    )

    class Meta:
        model = User
        fields = (
            'first_name',
            'last_name',
            'email',
            'password1',
            'password2',
        )

    def clean_email(self):
        email = self.cleaned_data.get('email')

        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Користувач з таким email вже існує.')

        return email

    def save(self, commit=True):
        user = super().save(commit=False)

        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']

        if commit:
            user.save()

        return user


class CustomUserLoginForm(AuthenticationForm):
    username = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'auth-input',
            'placeholder': 'Email'
        })
    )

    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={
            'class': 'auth-input',
            'placeholder': 'Пароль'
        })
    )

    def clean(self):
        email = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if email and password:
            self.user_cache = authenticate(
                self.request,
                username=email,
                password=password
            )

            if self.user_cache is None:
                raise forms.ValidationError('Невірний email або пароль.')

            if not self.user_cache.is_active:
                raise forms.ValidationError('Цей акаунт неактивний.')

        return self.cleaned_data


class CustomUserUpdateForm(forms.ModelForm):
    phone = forms.CharField(
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

    first_name = forms.CharField(
        required=True,
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'auth-input',
            'placeholder': 'Імʼя'
        })
    )

    last_name = forms.CharField(
        required=True,
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'auth-input',
            'placeholder': 'Прізвище'
        })
    )

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'auth-input',
            'placeholder': 'Email'
        })
    )

    class Meta:
        model = User
        fields = (
            'first_name',
            'last_name',
            'email',
            'company',
            'address1',
            'address2',
            'city',
            'province',
            'postal_code',
            'phone',
        )

        widgets = {
            'company': forms.TextInput(attrs={
                'class': 'auth-input',
                'placeholder': 'Компанія'
            }),
            'address1': forms.TextInput(attrs={
                'class': 'auth-input',
                'placeholder': 'Адреса, рядок 1'
            }),
            'address2': forms.TextInput(attrs={
                'class': 'auth-input',
                'placeholder': 'Адреса, рядок 2'
            }),
            'city': forms.TextInput(attrs={
                'class': 'auth-input',
                'placeholder': 'Місто'
            }),
            'province': forms.TextInput(attrs={
                'class': 'auth-input',
                'placeholder': 'Область / регіон'
            }),
            'postal_code': forms.TextInput(attrs={
                'class': 'auth-input',
                'placeholder': 'Поштовий індекс'
            }),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')

        if User.objects.filter(email=email).exclude(id=self.instance.id).exists():
            raise forms.ValidationError('Користувач з таким email вже існує.')

        return email

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')

        if phone == '':
            return None

        if phone and User.objects.filter(phone=phone).exclude(id=self.instance.id).exists():
            raise forms.ValidationError('Користувач з таким телефоном вже існує.')

        return phone

    def clean(self):
        cleaned_data = super().clean()

        for field in [
            'company',
            'address1',
            'address2',
            'city',
            'province',
            'postal_code',
            'phone',
        ]:
            if cleaned_data.get(field):
                cleaned_data[field] = strip_tags(cleaned_data[field])

        return cleaned_data