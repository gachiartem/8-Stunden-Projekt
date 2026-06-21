from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    can_delete = False

    fields = (
        'image_preview',
        'product',
        'size',
        'quantity',
        'price',
        'item_total',
    )

    readonly_fields = (
        'image_preview',
        'item_total',
    )

    def image_preview(self, obj):
        if obj and obj.pk and obj.product and obj.product.main_image:
            return format_html(
                '<img src="{}" style="max-height: 90px; max-width: 90px; object-fit: contain;" />',
                obj.product.main_image.url
            )

        return mark_safe('<span style="color: gray;">Немає зображення</span>')

    image_preview.short_description = 'Фото'

    def item_total(self, obj):
        if obj and obj.pk:
            return obj.get_total_price()

        return '-'

    item_total.short_description = 'Сума'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'email',
        'total_price',
        'payment_provider',
        'status',
        'created_at',
        'updated_at',
    )

    list_filter = (
        'status',
        'payment_provider',
        'created_at',
        'updated_at',
    )

    search_fields = (
        'email',
        'first_name',
        'last_name',
        'phone',
        'city',
        'postal_code',
    )

    date_hierarchy = 'created_at'

    readonly_fields = (
        'created_at',
        'updated_at',
        'total_price',
        'stripe_payment_intent_id',
    )

    inlines = [OrderItemInline]

    fieldsets = (
        ('Інформація про замовлення', {
            'fields': (
                'user',
                'first_name',
                'last_name',
                'email',
                'company',
                'phone',
            )
        }),

        ('Адреса доставки', {
            'fields': (
                'address1',
                'address2',
                'city',
                'province',
                'postal_code',
                'delivery_instructions',
            )
        }),

        ('Оплата та статус', {
            'fields': (
                'status',
                'payment_provider',
                'stripe_payment_intent_id',
                'total_price',
            )
        }),

        ('Дати', {
            'fields': (
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',),
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + (
                'user',
                'first_name',
                'last_name',
                'email',
                'company',
                'phone',
                'address1',
                'address2',
                'city',
                'province',
                'postal_code',
                'delivery_instructions',
            )

        return self.readonly_fields