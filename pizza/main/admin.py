from django.contrib import admin
from .models import Category, Size , Product , \
    ProductImage, ProductSize, NewsletterSubscriber, ProductReview


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

class ProductSizeInline(admin.TabularInline):
    model = ProductSize
    extra = 1


class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price']
    list_filter = ['category']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline, ProductSizeInline]


class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


class SizeAdmin(admin.ModelAdmin):
    list_display = ['name']

class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ('email', 'created_at', 'is_active')
    search_fields = ('email',)
    list_filter = ('is_active', 'created_at')

admin.site.register(Category, CategoryAdmin)
admin.site.register(Size, SizeAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(NewsletterSubscriber)

admin.site.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = (
        'product',
        'user',
        'rating',
        'short_text',
        'created_at',
        'updated_at',
    )
    list_filter = (
        'rating',
        'created_at',
        'updated_at',
        'product',
    )
    search_fields = (
        'product__name',
        'user__email',
        'user__first_name',
        'user__last_name',
        'text',
    )
    autocomplete_fields = ('product', 'user')
    readonly_fields = ('created_at', 'updated_at')
    fields = (
        'product',
        'user',
        'rating',
        'text',
        'created_at',
        'updated_at',
    )

    def short_text(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text

    short_text.short_description = 'Відгук'
