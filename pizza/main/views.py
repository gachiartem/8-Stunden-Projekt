from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import TemplateView, DetailView, ListView
from django.http import HttpResponse
from django.template.response import TemplateResponse
from django.views.decorators.http import require_POST
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from .models import Category, Product, Size, ProductSize, ProductReview, NewsletterSubscriber
from django.db.models import Q, Count  
from django.contrib import messages





class IndexView(TemplateView):
    template_name = 'main/base.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        categories = Category.objects.annotate(total_products=Count('products'))
        default_category = get_default_recommended_category()

        seafood_pizza = Product.objects.filter(
            slug='seafood-pizza'
        ).prefetch_related(
            'product_sizes',
            'product_sizes__size'
        ).first()

        seafood_pizza_size = None

        if seafood_pizza:
            seafood_pizza_size = seafood_pizza.product_sizes.filter(
                stock__gt=0
            ).order_by('price').first()

        if default_category:
            recommended_products = Product.objects.filter(
                category=default_category
            ).order_by('-created_at')[:4]
            recommended_category_slug = default_category.slug
            recommended_category_name = default_category.name
        else:
            recommended_products = Product.objects.none()
            recommended_category_slug = ''
            recommended_category_name = 'товари'

        context.update({
            'categories': categories,
            'current_category': None,
            'recommended_products': recommended_products,
            'recommended_category_slug': recommended_category_slug,
            'recommended_category_name': recommended_category_name,

            'seafood_pizza': seafood_pizza,
            'seafood_pizza_size': seafood_pizza_size,
        })

        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        if request.headers.get('HX-Request'):
            return TemplateResponse(request, 'main/home_content.html', context)
        return TemplateResponse(request, self.template_name, context)

def get_default_recommended_category():
    return (
        Category.objects.filter(slug__in=['pizza', 'pizzas']).first()
        or Category.objects.annotate(total_products=Count('products'))
        .filter(total_products__gt=0)
        .first()
    )

class CatalogView(TemplateView):
    template_name = 'main/base.html'

    FILTER_MAPPING = {
        'min_price': lambda queryset, value: queryset.filter(product_sizes__price__gte=value),
        'max_price': lambda queryset, value: queryset.filter(product_sizes__price__lte=value),
        'size': lambda queryset, value: queryset.filter(product_sizes__size__name=value),
        'description': lambda queryset, value: queryset.filter(description__icontains=value),
    }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        category_slug = kwargs.get('category_slug')
        categories = Category.objects.annotate(total_products=Count('products'))
        products = Product.objects.all().order_by('-created_at')
        current_category = None

        if category_slug:
            current_category = get_object_or_404(Category, slug=category_slug)
            products = products.filter(category=current_category)

        query = self.request.GET.get('q')
        if query:
            products = products.filter(
                Q(name__icontains=query) | Q(description__icontains=query)
            )

        products_for_sizes = products

        filter_params = {}
        for param, filter_func in self.FILTER_MAPPING.items():
            value = self.request.GET.get(param)
            if value:
                products = filter_func(products, value)
                filter_params[param] = value
            else:
                filter_params[param] = ''

        filter_params['q'] = query or ''

        if current_category:
            recommended_category_slug = current_category.slug
            recommended_category_name = current_category.name
            recommended_products = products.distinct()[:4]
        else:
            default_category = get_default_recommended_category()

            if default_category:
                recommended_category_slug = default_category.slug
                recommended_category_name = default_category.name
                recommended_products = Product.objects.filter(
                    category=default_category
                ).order_by('-created_at')[:4]
            else:
                recommended_category_slug = ''
                recommended_category_name = 'товари'
                recommended_products = Product.objects.none()

        size_ids = ProductSize.objects.filter(
            product__in=products_for_sizes,
            size__isnull=False
        ).values_list('size_id', flat=True).distinct()

        available_sizes = Size.objects.filter(id__in=size_ids).order_by('name')

        context.update({
            'categories': categories,
            'products': products.distinct(),
            'recommended_products': recommended_products,
            'recommended_category_slug': recommended_category_slug,
            'recommended_category_name': recommended_category_name,
            'current_category': category_slug,
            'current_category_obj': current_category,
            'filter_params': filter_params,
            'sizes': available_sizes,
            'search_query': query or '',
        })

        if self.request.GET.get('show_search') == 'true':
            context['show_search'] = True
        elif self.request.GET.get('reset_search') == 'true':
            context['reset_search'] = True

        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)

        if request.headers.get('HX-Request'):
            if context.get('show_search'):
                return TemplateResponse(request, 'main/search_input.html', context)

            elif context.get('reset_search'):
                return TemplateResponse(request, 'main/search_button.html', {})

            if request.GET.get('format') == 'html':
                return TemplateResponse(request, 'main/recommended_products.html', context)

            template = 'main/filter_modal.html' if request.GET.get('show_filters') == 'true' else 'main/catalog.html'
            return TemplateResponse(request, template, context)

        return TemplateResponse(request, self.template_name, context)
    
class ProductDetailView(DetailView):
    model = Product
    template_name = 'main/base.html'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.get_object()
        context['categories'] = Category.objects.annotate(total_products=Count('products'))
        context['related_products'] = Product.objects.filter(
            category=product.category
        ).exclude(id=product.id)[:4]
        context['current_category'] = product.category.slug
        return context

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(**kwargs)
        if request.headers.get('HX-Request'):
            return TemplateResponse(request, 'main/product_detail.html', context)
        return TemplateResponse(request, 'main/product_detail.html', context)
       

class PizzaListView(ListView):
    model = Product
    template_name = 'main/pizzas.html'
    context_object_name = 'pizzas'

    def get_queryset(self):
        return Product.objects.filter(category__slug='pizzas')

@require_POST
def subscribe_newsletter(request):
    email = request.POST.get('email', '').strip().lower()

    if not email:
        return HttpResponse(
            '<p class="subscribe-message subscribe-error">Введіть email.</p>'
        )

    try:
        validate_email(email)
    except ValidationError:
        return HttpResponse(
            '<p class="subscribe-message subscribe-error">Некоректний email.</p>'
        )

    subscriber, created = NewsletterSubscriber.objects.get_or_create(
        email=email,
        defaults={'is_active': True}
    )

    if not created:
        if subscriber.is_active:
            return HttpResponse(
                '<p class="subscribe-message subscribe-info">Ви вже підписані.</p>'
            )

        subscriber.is_active = True
        subscriber.save()

    return HttpResponse(
        '<p class="subscribe-message subscribe-success">Дякуємо! Ви підписалися на оновлення.</p>'
    )

@login_required(login_url='users:login')
def add_product_review(request, slug):
    product = get_object_or_404(Product, slug=slug)

    if request.method != 'POST':
        return redirect(reverse('main:product_detail', kwargs={'slug': product.slug}) + '#reviews-section')

    rating = request.POST.get('rating')
    text = request.POST.get('text', '').strip()

    try:
        rating = int(rating)
    except (TypeError, ValueError):
        messages.error(request, 'Оберіть оцінку від 1 до 5.')
        return redirect(reverse('main:product_detail', kwargs={'slug': product.slug}) + '#reviews-section')

    if rating < 1 or rating > 5:
        messages.error(request, 'Оцінка має бути від 1 до 5.')
        return redirect(reverse('main:product_detail', kwargs={'slug': product.slug}) + '#reviews-section')

    if not text:
        messages.error(request, 'Напишіть короткий відгук.')
        return redirect(reverse('main:product_detail', kwargs={'slug': product.slug}) + '#reviews-section')

    ProductReview.objects.update_or_create(
        product=product,
        user=request.user,
        defaults={
            'rating': rating,
            'text': text,
        }
    )

    messages.success(request, 'Ваш відгук збережено.')

    return redirect(reverse('main:product_detail', kwargs={'slug': product.slug}) + '#reviews-section')

def get_product_review_context(request, product):
    existing_review = None

    if request.user.is_authenticated:
        existing_review = ProductReview.objects.filter(
            product=product,
            user=request.user
        ).first()

    return {
        'existing_review': existing_review,
    }

from main.models import Product


def index(request):
    seafood_pizza = Product.objects.filter(
        slug='seafood-pizza'
    ).prefetch_related(
        'product_sizes',
        'product_sizes__size'
    ).first()

    seafood_pizza_size = None

    if seafood_pizza:
        seafood_pizza_size = seafood_pizza.product_sizes.filter(
            stock__gt=0
        ).order_by('price').first()

    context = {
        'seafood_pizza': seafood_pizza,
        'seafood_pizza_size': seafood_pizza_size,
    }

    return render(request, 'main/index.html', context)

def index(request):
    seafood_pizza = Product.objects.filter(
        slug='seafood-pizza'
    ).prefetch_related(
        'product_sizes',
        'product_sizes__size'
    ).first()

    seafood_pizza_size = None

    if seafood_pizza:
        seafood_pizza_size = seafood_pizza.product_sizes.filter(
            stock__gt=0
        ).order_by('price').first()

    context = {
        'seafood_pizza': seafood_pizza,
        'seafood_pizza_size': seafood_pizza_size,
    }

    return render(request, 'main/index.html', context)