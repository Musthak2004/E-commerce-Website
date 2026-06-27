from django.db import models
from django.db.models import Avg

from accounts.models import CustomUser


class Category(models.Model):

    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ("name",)

    def __str__(self):
        return self.name

class Tag(models.Model):

    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name


class Product(models.Model):

    seller = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="products"
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name="products"
    )

    tags = models.ManyToManyField(
        Tag,
        blank=True,
        related_name="products"
    )

    name = models.CharField(max_length=255)

    slug = models.SlugField(unique=True)

    description = models.TextField(blank=True)

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    stock = models.PositiveIntegerField(default=0)

    is_available = models.BooleanField(default=True)

    image = models.ImageField(
        upload_to="products/",
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = (
            models.Index(fields=("seller",)),
            models.Index(fields=("category",)),
            models.Index(fields=("is_available",)),
        )

    def __str__(self):
        return self.name

    @property
    def average_rating(self):
        result = self.reviews.aggregate(avg=Avg("rating"))
        return result["avg"]

    @property
    def review_count(self):
        return self.reviews.count()

class ProductImage(models.Model):

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="images",
        db_index=True,
    )

    image = models.ImageField(upload_to="product_images/")

    class Meta:
        ordering = ("id",)
        verbose_name = "Product Image"
        verbose_name_plural = "Product Images"

    def __str__(self):
        return f"Image of {self.product.name}"