from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum
from django.shortcuts import render

from accounts.models import CustomUser
from orders.models import Order
from products.models import Product
from .models import ContactMessage, NewsletterSubscriber


@staff_member_required
def admin_dashboard(request):
    total_users = CustomUser.objects.count()
    total_products = Product.objects.count()
    total_orders = Order.objects.count()
    total_revenue = Order.objects.filter(
        status__in=["CONFIRMED", "SHIPPED", "DELIVERED"]
    ).aggregate(total=Sum("total_price"))["total"] or 0
    pending_messages = ContactMessage.objects.count()
    newsletter_subscribers = NewsletterSubscriber.objects.count()

    context = {
        "total_users": total_users,
        "total_products": total_products,
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "pending_messages": pending_messages,
        "newsletter_subscribers": newsletter_subscribers,
        "title": "Dashboard",
    }
    return render(request, "admin/dashboard.html", context)
