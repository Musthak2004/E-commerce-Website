from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.viewsets import ReadOnlyModelViewSet

from products.models import Product

from .serializers import ProductListSerializer


class ProductPagination(PageNumberPagination):
    page_size = 12
    page_size_query_param = "page_size"
    max_page_size = 48


class ProductViewSet(ReadOnlyModelViewSet):
    queryset = Product.objects.filter(is_available=True).select_related("category")
    serializer_class = ProductListSerializer
    pagination_class = ProductPagination
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = "slug"
