from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.template.response import TemplateResponse
from django.utils.decorators import method_decorator
from django.views.generic import View

from .forms import OrderForm
from .models import Order, OrderItem
from cart.views import CartMixin
from payment.views import create_stripe_checkout_session


@method_decorator(login_required(login_url='users:login'), name='dispatch')
class CheckoutView(CartMixin, View):
    def get_cart_items(self, cart):
        return cart.items.select_related(
            'product',
            'product_size',
            'product_size__size'
        ).order_by('-added_at')

    def get(self, request):
        cart = self.get_cart(request)

        if cart.total_items == 0:
            context = {
                'message': 'Ваш кошик порожній.'
            }

            if request.headers.get('HX-Request'):
                return TemplateResponse(request, 'orders/empty_cart.html', context)

            return redirect('main:index')

        cart_items = self.get_cart_items(cart)
        total_price = cart.subtotal

        form = OrderForm(user=request.user)

        context = {
            'form': form,
            'cart': cart,
            'cart_items': cart_items,
            'total_price': total_price,
        }

        if request.headers.get('HX-Request'):
            return TemplateResponse(request, 'orders/checkout_content.html', context)

        return render(request, 'orders/checkout.html', context)

    def post(self, request):
        cart = self.get_cart(request)

        if cart.total_items == 0:
            context = {
                'message': 'Ваш кошик порожній.'
            }

            if request.headers.get('HX-Request'):
                return TemplateResponse(request, 'orders/empty_cart.html', context)

            return redirect('main:index')

        cart_items = self.get_cart_items(cart)
        total_price = cart.subtotal

        payment_provider = request.POST.get('payment_provider')

        if payment_provider != 'stripe':
            context = {
                'form': OrderForm(request.POST, user=request.user),
                'cart': cart,
                'cart_items': cart_items,
                'total_price': total_price,
                'error_message': 'Оберіть спосіб оплати.',
            }

            if request.headers.get('HX-Request'):
                return TemplateResponse(request, 'orders/checkout_content.html', context)

            return render(request, 'orders/checkout.html', context)

        form_data = request.POST.copy()

        if not form_data.get('email'):
            form_data['email'] = request.user.email

        form = OrderForm(form_data, user=request.user)

        if not form.is_valid():
            context = {
                'form': form,
                'cart': cart,
                'cart_items': cart_items,
                'total_price': total_price,
                'error_message': 'Перевірте правильність заповнення форми.',
            }

            if request.headers.get('HX-Request'):
                return TemplateResponse(request, 'orders/checkout_content.html', context)

            return render(request, 'orders/checkout.html', context)

        order = Order.objects.create(
            user=request.user,
            first_name=form.cleaned_data['first_name'],
            last_name=form.cleaned_data['last_name'],
            email=form.cleaned_data['email'],
            company=form.cleaned_data.get('company'),
            address1=form.cleaned_data.get('address1'),
            address2=form.cleaned_data.get('address2'),
            city=form.cleaned_data.get('city'),
            province=form.cleaned_data.get('province'),
            postal_code=form.cleaned_data.get('postal_code'),
            phone=form.cleaned_data.get('phone'),
            delivery_instructions=form.cleaned_data.get('delivery_instructions'),
            total_price=total_price,
            payment_provider=payment_provider,
            status='pending',
        )

        for item in cart_items:
            item_price = Decimal('0.00')

            if item.product_size:
                item_price = item.product_size.price
            elif item.product and item.product.min_price:
                item_price = item.product.min_price

            OrderItem.objects.create(
                order=order,
                product=item.product,
                size=item.product_size,
                quantity=item.quantity,
                price=item_price,
            )

        try:
            checkout_session = create_stripe_checkout_session(order, request)

            if request.headers.get('HX-Request'):
                response = HttpResponse(status=200)
                response['HX-Redirect'] = checkout_session.url
                return response

            return redirect(checkout_session.url)

        except Exception as error:
            order.delete()

            context = {
                'form': form,
                'cart': cart,
                'cart_items': cart_items,
                'total_price': total_price,
                'error_message': f'Помилка оплати: {str(error)}',
            }

            if request.headers.get('HX-Request'):
                return TemplateResponse(request, 'orders/checkout_content.html', context)

            return render(request, 'orders/checkout.html', context)


@login_required(login_url='users:login')
def order_success(request):
    return render(request, 'orders/success.html')



@login_required(login_url='users:login')
def order_history(request):
    orders = Order.objects.filter(
        user=request.user
    ).prefetch_related(
        'items',
        'items__product',
        'items__size',
        'items__size__size'
    ).order_by('-created_at')

    context = {
        'orders': orders,
    }

    if request.headers.get('HX-Request'):
        return TemplateResponse(
            request,
            'orders/order_history_content.html',
            context
        )

    return render(request, 'orders/order_history.html', context)