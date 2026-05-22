from django.shortcuts import render, redirect
from django.utils import timezone
from .models import News, Contact, Glossary, Vacancy, PromoCode, Review, Pizza
from django.db.models import Q
from django.contrib.auth import login
from .forms import RegisterForm
import requests

def current_time(request):
    return timezone.localtime(timezone.now()).strftime("%H:%M:%S")

def home(request):
    latest_news = News.objects.order_by('-created_at').first()
    weather = get_weather()
    location = get_pizzeria_location()
    
    return render(request, 'pizzeria/home.html', {
        'latest_news': latest_news,
        'temperature': weather['temperature'],
        'wind_speed': weather['wind_speed'],
        'weather_advice': weather['advice'],
        'pizzeria_location': location,
        'current_time': current_time(request)
    })

def about(request):
    return render(request, 'pizzeria/about.html', {
        'current_time': current_time(request)
    })

def news_list(request):
    news = News.objects.all().order_by('-created_at')
    return render(request, 'pizzeria/news_list.html', {
        'news_list': news,
        'current_time': current_time(request)
    })

def glossary(request):
    terms = Glossary.objects.all()  
    return render(request, 'pizzeria/glossary.html', {
        'terms': terms,             
        'current_time': current_time(request)
    })

def contacts(request):
    contacts_list = Contact.objects.all()
    return render(request, 'pizzeria/contacts.html', {
        'contacts': contacts_list,
        'current_time': current_time(request)
    })

def vacancies(request):
    vacancies_list = Vacancy.objects.all()
    return render(request, 'pizzeria/vacancies.html', {
        'vacancies': vacancies_list,
        'current_time': current_time(request)
    })

from .forms import ReviewForm

def reviews(request):
    reviews_list = Review.objects.all().order_by('-created_at')
    
    if request.method == 'POST' and request.user.is_authenticated:
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.save()
            return redirect('reviews')
    else:
        form = ReviewForm()
    
    return render(request, 'pizzeria/reviews.html', {
        'reviews': reviews_list,
        'form': form,
        'current_time': current_time(request)
    })

def promocodes(request):
    active_codes = PromoCode.objects.filter(is_active=True, valid_to__gte=timezone.now())
    expired_codes = PromoCode.objects.filter(is_active=False) | PromoCode.objects.filter(valid_to__lt=timezone.now())
    return render(request, 'pizzeria/promocodes.html', {
        'active_codes': active_codes,
        'expired_codes': expired_codes,
        'current_time': current_time(request)
    })

def privacy(request):
    return render(request, 'pizzeria/privacy.html', {
        'current_time': current_time(request)
    })

def pizza_list(request):
    pizzas = Pizza.objects.filter(is_available=True)
    
    # Поиск
    search_query = request.GET.get('q', '')
    if search_query:
        pizzas = pizzas.filter(Q(name__icontains=search_query) | Q(ingredients__icontains=search_query))
    
    # Сортировка
    sort_by = request.GET.get('sort', 'name')
    if sort_by in ['name', 'price_small', 'price_medium', 'price_large']:
        pizzas = pizzas.order_by(sort_by)
    
    return render(request, 'pizzeria/pizza_list.html', {
        'pizzas': pizzas,
        'search_query': search_query,
        'sort_by': sort_by,
        'current_time': current_time(request)
    })

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # автоматический вход после регистрации
            return redirect('home')
    else:
        form = RegisterForm()
    return render(request, 'pizzeria/register.html', {
        'form': form,
        'current_time': current_time(request)
    })

from django.contrib.auth import logout
from django.shortcuts import redirect

def logout_view(request):
    logout(request)
    return redirect('home')

from django.http import JsonResponse
from .models import Pizza, Order, OrderItem, PromoCode
from django.utils import timezone

def cart_view(request):
    """Просмотр корзины"""
    cart = request.session.get('cart', {})
    cart_items = []
    total = 0
    
    for pizza_id, item in cart.items():
        try:
            pizza = Pizza.objects.get(id=int(pizza_id))
            price = item.get('price', 0)
            quantity = item.get('quantity', 1)
            subtotal = price * quantity
            total += subtotal
            cart_items.append({
                'pizza': pizza,
                'size': item.get('size', 'medium'),
                'quantity': quantity,
                'price': price,
                'subtotal': subtotal,
            })
        except Pizza.DoesNotExist:
            continue
    
    return render(request, 'pizzeria/cart.html', {
        'cart_items': cart_items,
        'total': total,
        'current_time': current_time(request)
    })

def add_to_cart(request, pizza_id):
    """Добавление пиццы в корзину"""
    if request.method == 'POST':
        size = request.POST.get('size', 'medium')
        quantity = int(request.POST.get('quantity', 1))
        
        pizza = Pizza.objects.get(id=pizza_id)
        
        # Определяем цену в зависимости от размера
        if size == 'small':
            price = float(pizza.price_small)
        elif size == 'medium':
            price = float(pizza.price_medium)
        else:
            price = float(pizza.price_large)
        
        cart = request.session.get('cart', {})
        key = f"{pizza_id}_{size}"
        
        if key in cart:
            cart[key]['quantity'] += quantity
        else:
            cart[key] = {
                'pizza_id': pizza_id,
                'size': size,
                'quantity': quantity,
                'price': price,
            }
        
        request.session['cart'] = cart
        return redirect('cart')
    
    return redirect('pizza_list')

def remove_from_cart(request, key):
    """Удаление из корзины"""
    cart = request.session.get('cart', {})
    if key in cart:
        del cart[key]
        request.session['cart'] = cart
    return redirect('cart')

def checkout(request):
    """Оформление заказа"""
    if not request.user.is_authenticated:
        return redirect('login')
    
    cart = request.session.get('cart', {})
    if not cart:
        return redirect('cart')
    
    if request.method == 'POST':
        delivery_date = request.POST.get('delivery_date')
        promo_code = request.POST.get('promo_code')
        
        # Создаём заказ
        order = Order.objects.create(
            user=request.user,
            delivery_date=delivery_date,
            status='new'
        )
        
        total = 0
        for key, item in cart.items():
            pizza = Pizza.objects.get(id=item['pizza_id'])
            price = item['price']
            quantity = item['quantity']
            
            OrderItem.objects.create(
                order=order,
                pizza=pizza,
                size=item['size'],
                quantity=quantity,
                price=price
            )
            total += price * quantity
        
        # Применяем промокод
        discount = 0
        if promo_code:
            try:
                code = PromoCode.objects.get(
                    code=promo_code,
                    is_active=True,
                    valid_to__gte=timezone.now()
                )
                discount = total * code.discount_percent / 100
                order.promo_code = code
                code.used_count += 1
                code.save()
            except PromoCode.DoesNotExist:
                pass
        
        order.total_price = total - discount
        order.save()
        
        # Очищаем корзину
        request.session['cart'] = {}
        
        return redirect('order_success', order_id=order.id)
    
    return render(request, 'pizzeria/checkout.html', {
        'cart_items': cart_view(request).context_data['cart_items'],
        'total': cart_view(request).context_data['total'],
        'current_time': current_time(request)
    })

def order_success(request, order_id):
    """Страница успешного заказа"""
    order = Order.objects.get(id=order_id, user=request.user)
    return render(request, 'pizzeria/order_success.html', {
        'order': order,
        'current_time': current_time(request)
    })


# APIs
def get_weather():
    """Получение текущей погоды в Минске"""
    try:
        # Координаты Минска
        lat = 53.9045
        lon = 27.5615
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        response = requests.get(url, timeout=5)
        data = response.json()
        
        weather = data['current_weather']
        temperature = weather['temperature']
        wind_speed = weather['windspeed']
        
        # Совет дня на основе температуры
        if temperature > 20:
            advice = "☀️ Отличная погода! Закажите пиццу на доставку и наслаждайтесь солнцем!"
        elif temperature > 10:
            advice = "🌤️ Тёплый день. Самое время для пиццы с друзьями!"
        elif temperature > 0:
            advice = "🍂 Прохладно. Согрейтесь горячей пиццей!"
        else:
            advice = "❄️ Холодно! Пицца с доставкой — лучший выбор!"
        
        return {
            'temperature': temperature,
            'wind_speed': wind_speed,
            'advice': advice
        }
    except Exception as e:
        print(f"Weather API error: {e}")
        return {
            'temperature': 18,
            'wind_speed': 5,
            'advice': "🍕 Закажите нашу фирменную пиццу!"
        }
    

def get_pizzeria_location():
    """Получение координат пиццерии по адресу"""
    try:
        address = "ул. Ленина, 20, Минск, Беларусь"
        url = f"https://nominatim.openstreetmap.org/search?q={address}&format=json&limit=1"
        response = requests.get(url, headers={'User-Agent': 'PizzeriaApp/1.0'}, timeout=5)
        data = response.json()
        
        if data:
            return {
                'lat': float(data[0]['lat']),
                'lon': float(data[0]['lon']),
                'display_name': data[0]['display_name']
            }
        return None
    except Exception as e:
        print(f"Geocoding API error: {e}")
        return None


from django.db.models import Count, Sum
from .models import OrderItem
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64

def stats(request):
    # Статистика по пиццам — считаем количество и сумму вручную
    pizza_stats = []
    pizzas = Pizza.objects.all()
    
    for pizza in pizzas:
        items = OrderItem.objects.filter(pizza=pizza)
        total_quantity = items.aggregate(total=Sum('quantity'))['total'] or 0
        # Сумму считаем: цена * количество (цены берём из пиццы, они фиксированные)
        total_revenue = 0
        for item in items:
            if item.size == 'small':
                total_revenue += item.quantity * item.pizza.price_small
            elif item.size == 'medium':
                total_revenue += item.quantity * item.pizza.price_medium
            else:
                total_revenue += item.quantity * item.pizza.price_large
        
        if total_quantity > 0:
            pizza_stats.append({
                'pizza__name': pizza.name,
                'total_quantity': total_quantity,
                'total_revenue': total_revenue,
            })
    
    # Сортируем по количеству
    pizza_stats.sort(key=lambda x: x['total_quantity'], reverse=True)
    
    # Общая статистика
    total_orders = Order.objects.count()
    total_revenue = sum(item['total_revenue'] for item in pizza_stats)
    avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
    
    # Строим график
    chart_data = None
    if pizza_stats:
        names = [item['pizza__name'] for item in pizza_stats[:10]]
        quantities = [item['total_quantity'] for item in pizza_stats[:10]]
        
        plt.figure(figsize=(10, 6))
        plt.bar(names, quantities, color='#d32f2f')
        plt.xlabel('Пиццы')
        plt.ylabel('Количество заказов')
        plt.title('Популярность пицц (топ-10)')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        chart_data = f"data:image/png;base64,{image_base64}"
    
    return render(request, 'pizzeria/stats.html', {
        'pizza_stats': pizza_stats,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'avg_order_value': avg_order_value,
        'chart': chart_data,
        'current_time': current_time(request)
    })


import pytz
from datetime import datetime, timedelta
import calendar

def get_user_timezone(request):
    """Определение таймзоны пользователя (по умолчанию Europe/Minsk)"""
    # Можно получить из сессии или из IP (для простоты — по умолчанию)
    user_tz = request.session.get('user_timezone', 'Europe/Minsk')
    return pytz.timezone(user_tz)

def get_current_datetime_in_user_tz(request):
    """Текущая дата/время в таймзоне пользователя"""
    user_tz = get_user_timezone(request)
    now_utc = datetime.now(pytz.UTC)
    now_local = now_utc.astimezone(user_tz)
    return now_local

def get_text_calendar(request, year=None, month=None):
    """Текстовый календарь на заданный месяц"""
    user_tz = get_user_timezone(request)
    now_local = get_current_datetime_in_user_tz(request)
    
    if year is None:
        year = now_local.year
    if month is None:
        month = now_local.month
    
    # Создаём календарь
    cal = calendar.monthcalendar(year, month)
    
    # Названия дней недели
    month_names = {
        1: 'Январь', 2: 'Февраль', 3: 'Март', 4: 'Апрель',
        5: 'Май', 6: 'Июнь', 7: 'Июль', 8: 'Август',
        9: 'Сентябрь', 10: 'Октябрь', 11: 'Ноябрь', 12: 'Декабрь'
    }
    
    # Формируем HTML календаря
    html = f'<h3>{month_names[month]} {year}</h3>'
    html += '<table style="border-collapse: collapse; width: 100%;">'
    html += '<tr style="background: #d32f2f; color: white;">'
    for day_name in ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']:
        html += f'<th style="padding: 8px; text-align: center;">{day_name}</th>'
    html += '</tr>'
    
    for week in cal:
        html += '<tr>'
        for day in week:
            if day == 0:
                html += '<td style="padding: 8px; text-align: center; background: #f0f0f0;"></td>'
            else:
                # Если это сегодняшний день — выделяем
                if day == now_local.day and month == now_local.month and year == now_local.year:
                    html += f'<td style="padding: 8px; text-align: center; background: #ffeb3b; font-weight: bold;">{day}</td>'
                else:
                    html += f'<td style="padding: 8px; text-align: center;">{day}</td>'
        html += '</tr>'
    
    html += '</table>'
    return html

def set_user_timezone(request):
    """Установка таймзоны пользователя (из POST-запроса)"""
    if request.method == 'POST':
        tz = request.POST.get('timezone')
        if tz in pytz.all_timezones:
            request.session['user_timezone'] = tz
    return redirect('home')

def calendar_view(request, year=None, month=None):
    """Страница с текстовым календарём"""
    if year:
        year = int(year)
    if month:
        month = int(month)
    
    calendar_html = get_text_calendar(request, year, month)
    now_local = get_current_datetime_in_user_tz(request)
    
    # Получаем список доступных таймзон (первые 10 для выпадающего списка)
    common_timezones = [
        'Europe/Minsk', 'Europe/Moscow', 'Europe/London', 
        'Europe/Berlin', 'America/New_York', 'Asia/Tokyo',
        'Asia/Shanghai', 'Australia/Sydney', 'Africa/Cairo', 'America/Los_Angeles'
    ]
    
    return render(request, 'pizzeria/calendar.html', {
        'calendar_html': calendar_html,
        'current_datetime': now_local.strftime('%d.%m.%Y %H:%M:%S'),
        'current_timezone': request.session.get('user_timezone', 'Europe/Minsk'),
        'timezones': common_timezones,
        'year': year or now_local.year,
        'month': month or now_local.month,
        'current_time': current_time(request)
    })