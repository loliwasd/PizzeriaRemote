from django.urls import path, re_path, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('news/', views.news_list, name='news_list'),
    path('glossary/', views.glossary, name='glossary'),
    path('contacts/', views.contacts, name='contacts'),
    path('vacancies/', views.vacancies, name='vacancies'),
    path('reviews/', views.reviews, name='reviews'),
    path('promocodes/', views.promocodes, name='promocodes'),
    path('pizzas/', views.pizza_list, name='pizza_list'),
    path('privacy/', views.privacy, name='privacy'),
    path('cart/', views.cart_view, name='cart'),
    path('add-to-cart/<int:pizza_id>/', views.add_to_cart, name='add_to_cart'),
    path('remove-from-cart/<str:key>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('order-success/<int:order_id>/', views.order_success, name='order_success'),
    path('stats/', views.stats, name='stats'),
    path('calendar/', views.calendar_view, name='calendar'),
    
    re_path(r'^calendar/(?P<year>\d{4})/(?P<month>\d{1,2})/$', views.calendar_view, name='calendar_month'),
    
    path('set-timezone/', views.set_user_timezone, name='set_timezone'),
    
    # Авторизация
    path('login/', auth_views.LoginView.as_view(template_name='pizzeria/login.html'), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),
]

if not settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)