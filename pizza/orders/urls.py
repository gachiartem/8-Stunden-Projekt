from django.urls import path
from .views import CheckoutView, order_success, order_history

app_name = 'orders'

urlpatterns = [
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('success/', order_success, name='success'),
    path('history/', order_history, name='history'),
]