from django.contrib import admin
from .models import Pizza, Order, OrderItem, PromoCode, Review, News, Glossary, Contact, Vacancy

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
    readonly_fields = ('price', 'total_price')

@admin.register(Pizza)
class PizzaAdmin(admin.ModelAdmin):
    list_display = ('name', 'price_small', 'price_medium', 'price_large', 'is_available')
    list_filter = ('is_available',)
    search_fields = ('name',)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'created_at', 'delivery_date', 'status', 'subtotal', 'discount_amount', 'total_price')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username',)
    readonly_fields = ('subtotal', 'discount_amount', 'total_price')
    inlines = [OrderItemInline]

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'pizza', 'size', 'quantity', 'price', 'total_price')
    list_filter = ('size',)

@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_percent', 'is_active', 'valid_from', 'valid_to')
    list_filter = ('is_active',)

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'pizza', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')

@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at')
    search_fields = ('title',)

@admin.register(Glossary)
class GlossaryAdmin(admin.ModelAdmin):
    list_display = ('term', 'added_at')
    search_fields = ('term',)

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'position', 'phone', 'email')

@admin.register(Vacancy)
class VacancyAdmin(admin.ModelAdmin):
    list_display = ('title', 'salary')

from .models import Profile

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'birth_date', 'age', 'phone')
    list_filter = ('birth_date',)
    readonly_fields = ('age',)
    
    def age(self, obj):
        return obj.age
    age.short_description = "Возраст"