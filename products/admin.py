from django.contrib import admin

from .models import Category, Product, ProductImage, Tag


class ProductImageInline(admin.TabularInline):

    model = ProductImage

    extra = 1


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "name",
        "slug",
    )

    search_fields = ("name",)

    prepopulated_fields = {
        "slug": ("name",)
    }


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "name",
        "slug",
        "seller",
        "category",
        "price",
        "stock",
        "is_available",
        "created_at",
    )

    list_editable = ("is_available", "stock", "price")

    list_filter = (
        "is_available",
        "category",
    )

    search_fields = (
        "name",
        "description",
    )

    prepopulated_fields = {
        "slug": ("name",)
    }

    filter_horizontal = ("tags",)
    inlines = [ProductImageInline]


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):

    list_display = ("id", "name", "slug")

    search_fields = ("name",)

    prepopulated_fields = {
        "slug": ("name",)
    }