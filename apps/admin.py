from django.contrib import admin
from django.contrib.admin import ModelAdmin, StackedInline
from django.utils.html import format_html
from mptt.admin import DraggableMPTTAdmin

from apps.models import Category, Product, ProductImage, User, SiteSettings

admin.site.site_header = "Alijahon Admin"
admin.site.index_title = "Welcome to Alijahon Portal"
admin.site.register(User)


@admin.register(Category)
class CategoryAdmin(DraggableMPTTAdmin):
    exclude = 'slug',

    # list_display = 'id', 'name', 'image_photo', 'product_count'

    @admin.display(empty_value="?")
    def image_photo(self, obj):
        photo = obj.image.url
        return format_html("<img src='{}' style='width: 50px' />", photo)

    @admin.display(empty_value="?")
    def product_count(self, obj):
        return obj.products.count()


class ProductImageInline(StackedInline):
    model = ProductImage


@admin.register(Product)
class ProductAdmin(ModelAdmin):
    exclude = 'slug',
    inlines = ProductImageInline,
    list_display = 'name', 'is_exists'
    search_fields = 'name', 'price',
    ordering = '-created_at',
    list_filter = 'quantity',

    @admin.display(empty_value="?")
    def is_exists(self, obj):
        icon_url = 'https://img.icons8.com/?size=100&id=9fp9k4lPT8us&format=png&color=000000'
        if not obj.quantity:
            icon_url = 'https://img.icons8.com/?size=100&id=63688&format=png&color=000000'
        return format_html("<img src='{}' style='width: 30px' />", icon_url)


@admin.register(SiteSettings)
class SiteSettingsModelAdmin(ModelAdmin):
    pass
