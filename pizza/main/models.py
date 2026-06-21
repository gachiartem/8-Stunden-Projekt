from django.db import models
from django.utils.text import slugify
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Avg
from django.utils.html import strip_tags


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.CharField(max_length=100, unique=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


    def __str__(self):
        return self.name
    

class Size(models.Model):
    name = models.CharField(max_length=20)


    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=100)
    slug = models.CharField(max_length=100, unique=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE,
                                 related_name='products')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    ingredients = models.TextField(blank=True, verbose_name='Склад')
    description = models.TextField(blank=True)
    main_image = models.ImageField(upload_to='products/main')
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateField(auto_now=True)

    @property
    def min_price(self):
        first_size = self.product_sizes.order_by('price').first()
        if first_size:
            return first_size.price
        return self.price
    
    
    @property
    def average_rating(self):
        result = self.reviews.aggregate(avg=Avg('rating'))
        avg = result.get('avg')

        if avg:
            return round(avg, 1)

        return 0


    @property
    def review_count(self):
        return self.reviews.count()


    @property
    def rounded_rating(self):
        if not self.average_rating:
            return 0

        return min(5, max(0, int(self.average_rating + 0.5)))


    @property
    def filled_hearts(self):
        return '★' * self.rounded_rating


    @property
    def empty_hearts(self):
        return '✩' * (5 - self.rounded_rating)


    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


    def __str__(self):
        return self.name


class ProductReview(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='reviews'
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='product_reviews'
    )

    rating = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5)
        ]
    )

    text = models.TextField(
        max_length=1000
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('product', 'user')
        ordering = ['-updated_at']
        verbose_name = 'Відгук про товар'
        verbose_name_plural = 'Відгуки про товари'

    def clean(self):
        super().clean()

        if self.text:
            self.text = strip_tags(self.text)

    @property
    def filled_hearts(self):
        return '★' * self.rating

    @property
    def empty_hearts(self):
        return '✩' * (5 - self.rating)

    def __str__(self):
        return f'{self.product.name} — {self.rating}/5'
    


class ProductSize(models.Model):

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='product_sizes'
    )
    size = models.ForeignKey(
        Size,
        on_delete=models.CASCADE
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    stock = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.product.name} — {self.size.name} — {self.price} ₴"

class ProductImage(models.Model):
    product = models.ForeignKey('Product', on_delete=models.CASCADE,
                                related_name='images')
    image = models.ImageField(upload_to='product/extra/')

class NewsletterSubscriber(models.Model):
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Підписник"
        verbose_name_plural = "Підписники"

    def __str__(self):
        return self.email