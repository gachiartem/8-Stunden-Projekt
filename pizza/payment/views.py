import stripe

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.response import TemplateResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from cart.views import CartMixin
from orders.models import Order


stripe.api_key = settings.STRIPE_SECRET_KEY
stripe_endpoint_secret = settings.STRIPE_WEBBOOK_SECRET


def create_stripe_checkout_session(order, request):
    line_items = []

    for item in order.items.select_related('product', 'size', 'size__size'):
        if item.size and item.size.size:
            product_name = f'{item.product.name} — {item.size.size.name}'
        else:
            product_name = item.product.name

        line_items.append({
            'price_data': {
                'currency': 'uah',
                'product_data': {
                    'name': product_name,
                },
                'unit_amount': int(item.price * 100),
            },
            'quantity': item.quantity,
        })

    checkout_session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=line_items,
        mode='payment',

        success_url=request.build_absolute_uri(
            '/payment/stripe/success/'
        ) + '?session_id={CHECKOUT_SESSION_ID}',

        cancel_url=request.build_absolute_uri(
            f'/payment/stripe/cancel/?order_id={order.id}'
        ),

        metadata={
            'order_id': str(order.id),
        }
    )

    order.payment_provider = 'stripe'
    order.save(update_fields=['payment_provider'])

    return checkout_session


@csrf_exempt
@require_POST
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

    try:
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            stripe_endpoint_secret
        )

    except ValueError:
        return HttpResponse(status=400)

    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)

    if event.type == 'checkout.session.completed':
        session = event.data.object

        order_id = session.metadata.order_id

        try:
            order = Order.objects.get(id=order_id)

            order.status = 'processing'
            order.stripe_payment_intent_id = session.payment_intent
            order.save(update_fields=[
                'status',
                'stripe_payment_intent_id',
            ])

        except Order.DoesNotExist:
            return HttpResponse(status=400)

    return HttpResponse(status=200)

@login_required(login_url='users:login')
def stripe_success(request):
    session_id = request.GET.get('session_id')

    if not session_id:
        return redirect('main:index')

    session = stripe.checkout.Session.retrieve(session_id)

    order_id = session.metadata.order_id

    order = get_object_or_404(
        Order,
        id=order_id,
        user=request.user
    )

    order.status = 'processing'
    order.stripe_payment_intent_id = session.payment_intent
    order.save(update_fields=[
        'status',
        'stripe_payment_intent_id',
    ])

    cart = CartMixin().get_cart(request)
    cart.clear()

    context = {
        'order': order,
    }

    return render(request, 'payment/stripe_success.html', context)

@login_required(login_url='users:login')
def stripe_cancel(request):
    order_id = request.GET.get('order_id')

    if not order_id:
        return redirect('orders:checkout')

    order = get_object_or_404(
        Order,
        id=order_id,
        user=request.user
    )

    order.status = 'cancelled'
    order.save(update_fields=['status'])

    context = {
        'order': order,
    }

    if request.headers.get('HX-Request'):
        return TemplateResponse(
            request,
            'payment/stripe_cancel_content.html',
            context
        )

    return render(request, 'payment/stripe_cancel.html', context)