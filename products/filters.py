import django_filters
from django.db.models import Q

from .models import Product


class ProductFilter(django_filters.FilterSet):
    """FilterSet for the product list page.

    Replaces the hand-rolled filter logic in ProductListView.get_queryset()
    with a declarative, reusable filter definition.
    """

    q = django_filters.CharFilter(
        method="filter_search",
        label="Search",
    )

    category = django_filters.CharFilter(
        field_name="category__slug",
        lookup_expr="exact",
        label="Category",
    )

    tag = django_filters.CharFilter(
        field_name="tags__slug",
        lookup_expr="exact",
        label="Tag",
    )

    min_price = django_filters.NumberFilter(
        field_name="price",
        lookup_expr="gte",
        label="Min price",
    )

    max_price = django_filters.NumberFilter(
        field_name="price",
        lookup_expr="lte",
        label="Max price",
    )

    min_rating = django_filters.NumberFilter(
        method="filter_min_rating",
        label="Minimum rating",
    )

    class Meta:
        model = Product
        fields = [
            "q",
            "category",
            "tag",
            "min_price",
            "max_price",
            "min_rating",
        ]

    def filter_search(self, queryset, name, value):
        """Search across name, description, tags, and category name."""
        if not value:
            return queryset
        terms = [t.strip() for t in value.split() if t.strip()]
        if not terms:
            return queryset
        q_objects = Q()
        for term in terms:
            q_objects |= Q(name__icontains=term)
            q_objects |= Q(description__icontains=term)
            q_objects |= Q(tags__name__icontains=term)
            q_objects |= Q(category__name__icontains=term)
        return queryset.filter(q_objects).distinct()

    def filter_min_rating(self, queryset, name, value):
        """Filter products with average rating >= value."""
        from django.db.models import Avg
        try:
            val = float(value)
        except (ValueError, TypeError):
            return queryset
        return queryset.annotate(
            avg_rating=Avg("reviews__rating")
        ).filter(avg_rating__gte=val)
