from .models import Category


def site_categories(request):
    return {
        'categories': Category.objects.all().order_by('id')
    }