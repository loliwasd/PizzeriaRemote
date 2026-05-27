from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
import re
from datetime import date

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError('Пользователь с таким именем уже существует')
        return username
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('Пользователь с таким email уже существует')
        return email

from .models import Review

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['pizza', 'rating', 'text']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Ваш отзыв...'}),
            'rating': forms.Select(choices=[(i, f'{i} ★') for i in range(1, 6)]),
        }

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    birth_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        help_text="ДД.ММ.ГГГГ"
    )
    phone = forms.CharField(max_length=20, required=False, help_text="+375 (29) XXX-XX-XX")
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'birth_date', 'phone']
    
    def clean_birth_date(self):
        birth_date = self.cleaned_data.get('birth_date')
        today = date.today()
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        if age < 18:
            raise forms.ValidationError("Вам должно быть не менее 18 лет для регистрации")
        return birth_date
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            import re
            pattern = r'^\+375 \(29\) \d{3}-\d{2}-\d{2}$'
            if not re.match(pattern, phone):
                raise forms.ValidationError("Телефон должен быть в формате +375 (29) XXX-XX-XX")
        return phone
    
    def save(self, commit=True):
        user = super().save(commit=True)
        profile = Profile.objects.create(
            user=user,
            birth_date=self.cleaned_data['birth_date'],
            phone=self.cleaned_data.get('phone', '')
        )
        return user