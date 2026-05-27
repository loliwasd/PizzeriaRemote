from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import re
from datetime import date

class Pizza(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название")
    description = models.TextField(verbose_name="Описание")
    price_small = models.DecimalField(max_digits=6, decimal_places=2, verbose_name="Цена малая")
    price_medium = models.DecimalField(max_digits=6, decimal_places=2, verbose_name="Цена средняя")
    price_large = models.DecimalField(max_digits=6, decimal_places=2, verbose_name="Цена большая")
    image = models.ImageField(upload_to='pizzas/', blank=True, null=True, verbose_name="Фото")
    ingredients = models.TextField(verbose_name="Ингредиенты")
    is_available = models.BooleanField(default=True, verbose_name="Доступна")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Пицца"
        verbose_name_plural = "Пиццы"


class PromoCode(models.Model):
    code = models.CharField(max_length=50, unique=True, verbose_name="Код")
    discount_percent = models.PositiveIntegerField(default=0, verbose_name="Скидка %")
    valid_from = models.DateTimeField(verbose_name="Действует с")
    valid_to = models.DateTimeField(verbose_name="Действует до")
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    usage_limit = models.PositiveIntegerField(default=1, verbose_name="Лимит использований")
    used_count = models.PositiveIntegerField(default=0, verbose_name="Использовано")

    def __str__(self):
        return f"{self.code} ({self.discount_percent}%)"

    class Meta:
        verbose_name = "Промокод"
        verbose_name_plural = "Промокоды"


class Order(models.Model):
    STATUS_CHOICES = [
        ('new', 'Новый'),
        ('cooking', 'Готовится'),
        ('delivering', 'Доставляется'),
        ('completed', 'Выполнен'),
        ('cancelled', 'Отменён'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Клиент")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    delivery_date = models.DateField(verbose_name="Дата доставки")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new', verbose_name="Статус")
    promo_code = models.ForeignKey(PromoCode, on_delete=models.SET_NULL, blank=True, null=True, verbose_name="Промокод")
    
    @property
    def subtotal(self):
        """Сумма без скидки"""
        return sum(item.total_price for item in self.items.all())
    
    @property
    def discount_amount(self):
        """Сумма скидки"""
        if self.promo_code and self.promo_code.is_active:
            return self.subtotal * self.promo_code.discount_percent / 100
        return 0
    
    @property
    def total_price(self):
        """Итоговая сумма со скидкой"""
        return self.subtotal - self.discount_amount

    def __str__(self):
        return f"Заказ #{self.id} - {self.user.username}"

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"


class OrderItem(models.Model):
    SIZE_CHOICES = [
        ('small', 'Малая'),
        ('medium', 'Средняя'),
        ('large', 'Большая'),
    ]
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name="Заказ")
    pizza = models.ForeignKey(Pizza, on_delete=models.CASCADE, verbose_name="Пицца")
    size = models.CharField(max_length=10, choices=SIZE_CHOICES, verbose_name="Размер")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Количество")
    
    @property
    def price(self):
        """Цена в зависимости от размера"""
        if self.size == 'small':
            return self.pizza.price_small
        elif self.size == 'medium':
            return self.pizza.price_medium
        else:
            return self.pizza.price_large
    
    @property
    def total_price(self):
        return self.price * self.quantity

    def __str__(self):
        return f"{self.pizza.name} x{self.quantity} ({self.get_size_display()})"

    class Meta:
        verbose_name = "Позиция заказа"
        verbose_name_plural = "Позиции заказов"


class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    pizza = models.ForeignKey(Pizza, on_delete=models.CASCADE, verbose_name="Пицца")
    rating = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)], verbose_name="Оценка")
    text = models.TextField(verbose_name="Текст отзыва")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата")

    def __str__(self):
        return f"{self.user.username} - {self.pizza.name} - {self.rating}★"

    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"


class News(models.Model):
    title = models.CharField(max_length=200, verbose_name="Заголовок")
    short_description = models.CharField(max_length=300, verbose_name="Краткое описание")
    content = models.TextField(verbose_name="Полное содержание")
    image = models.ImageField(upload_to='news/', blank=True, null=True, verbose_name="Картинка")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата публикации")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Новость"
        verbose_name_plural = "Новости"


class Glossary(models.Model):
    term = models.CharField(max_length=100, unique=True, verbose_name="Термин")
    definition = models.TextField(verbose_name="Определение")
    added_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата добавления")

    def __str__(self):
        return self.term

    class Meta:
        verbose_name = "Термин"
        verbose_name_plural = "Термины"


class Contact(models.Model):
    name = models.CharField(max_length=100, verbose_name="Имя")
    position = models.CharField(max_length=100, verbose_name="Должность")
    phone = models.CharField(max_length=20, verbose_name="Телефон")
    email = models.EmailField(verbose_name="Email")
    photo = models.ImageField(upload_to='contacts/', blank=True, null=True, verbose_name="Фото")

    def __str__(self):
        return f"{self.name} - {self.position}"

    class Meta:
        verbose_name = "Контакт"
        verbose_name_plural = "Контакты"


class Vacancy(models.Model):
    title = models.CharField(max_length=100, verbose_name="Должность")
    description = models.TextField(verbose_name="Описание")
    salary = models.CharField(max_length=100, verbose_name="Зарплата")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Вакансия"
        verbose_name_plural = "Вакансии"


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    birth_date = models.DateField(verbose_name="Дата рождения")
    phone = models.CharField(max_length=20, verbose_name="Телефон", blank=True)
    
    @property
    def age(self):
        today = date.today()
        return today.year - self.birth_date.year - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))
    
    def clean(self):
        if self.age < 18:
            raise ValidationError("Возраст должен быть не менее 18 лет")
    
    def __str__(self):
        return f"{self.user.username} ({self.age} лет)"
    
    class Meta:
        verbose_name = "Профиль"
        verbose_name_plural = "Профили"