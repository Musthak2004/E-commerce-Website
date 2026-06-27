import stripe
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import send_mail
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.generic import DetailView

from orders.models import Order

from .models import Payment


stripe.api_key = settings.STRIPE_SECRET_KEY


@login_required
def payment_create(request, order_id):

    order = get_object_or_404(
        Order,
        pk=order_id,
        user=request.user,
    )

    if order.status not in ("PENDING", "CONFIRMED"):
        messages.error(request, "This order is not available for payment.")
        return redirect("orders:order_detail", order_id=order.id)

    if hasattr(order, "payment"):
        payment = order.payment
        if payment.status == "COMPLETED":
            messages.info(request, "This order has already been paid.")
            return redirect("payments:payment_detail", pk=payment.id)
        if payment.stripe_session_id:
            return redirect("payments:payment_detail", pk=payment.id)

    total_cents = int(float(order.total_price) * 100)

    if total_cents < 50:
        messages.error(request, "Order total must be at least $0.50.")
        return redirect("orders:order_detail", order_id=order.id)

    try:
        session = stripe.checkout.Session.create(
            mode="payment",
            client_reference_id=str(order.id),
            customer_email=request.user.email,
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": f"Order #{order.id} — ShopEase",
                    },
                    "unit_amount": total_cents,
                },
                "quantity": 1,
            }],
            metadata={
                "order_id": str(order.id),
            },
            success_url=request.build_absolute_uri(
                f"/payments/success/{order.id}/"
            ),
            cancel_url=request.build_absolute_uri(
                f"/orders/{order.id}/"
            ),
        )

        payment, created = Payment.objects.get_or_create(
            order=order,
            defaults={
                "amount": order.total_price,
                "payment_method": "CARD",
                "stripe_session_id": session.id,
                "status": "PENDING",
            },
        )

        if not created:
            payment.stripe_session_id = session.id
            payment.save(update_fields=["stripe_session_id"])

        return redirect(session.url, code=303)

    except stripe.error.StripeError as e:
        messages.error(request, f"Payment error: {e.user_message or 'Please try again.'}")
        return redirect("orders:order_detail", order_id=order.id)


@login_required
def payment_success(request, order_id):

    order = get_object_or_404(
        Order,
        pk=order_id,
        user=request.user,
    )

    try:
        payment = order.payment
    except Payment.DoesNotExist:
        messages.error(request, "No payment found for this order.")
        return redirect("orders:order_detail", order_id=order.id)

    if payment.stripe_session_id:
        try:
            session = stripe.checkout.Session.retrieve(payment.stripe_session_id)
            if session.payment_status == "paid" and payment.status != "COMPLETED":
                payment.status = "COMPLETED"
                payment.transaction_id = session.payment_intent
                payment.paid_at = timezone.now()
                payment.save(update_fields=["status", "transaction_id", "paid_at"])
                order.status = "CONFIRMED"
                order.save(update_fields=["status"])
                send_mail(
                    subject=f"Payment Received — Order #{order.id}",
                    message=(
                        f"Hi {order.user.email},\n\n"
                        f"Payment for order #{order.id} has been received.\n"
                        f"Amount: ${payment.amount}\n"
                        f"Transaction: {payment.transaction_id}\n\n"
                        f"Your order is now being processed.\n"
                        f"Thank you for shopping with ShopEase!"
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[order.user.email],
                    fail_silently=True,
                )
                messages.success(request, "Payment completed successfully!")
        except stripe.error.StripeError as e:
            messages.error(request, f"Could not verify payment with Stripe: {e.user_message or 'try again later.'}")

    return redirect("payments:payment_detail", pk=payment.id)


class PaymentDetailView(LoginRequiredMixin, DetailView):

    model = Payment

    template_name = "payments/payment_detail.html"

    context_object_name = "payment"

    def get_queryset(self):
        return super().get_queryset().filter(
            order__user=self.request.user
        )


@csrf_exempt
@require_POST
def stripe_webhook(request):

    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except (ValueError, stripe.error.SignatureVerificationError):
        return HttpResponse(status=400)

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        order_id = session.get("metadata", {}).get("order_id")

        if order_id:
            try:
                payment = Payment.objects.get(
                    order_id=order_id,
                    stripe_session_id=session["id"],
                )
                if payment.status != "COMPLETED":
                    payment.status = "COMPLETED"
                    payment.transaction_id = session.get("payment_intent")
                    payment.paid_at = timezone.now()
                    payment.save(update_fields=["status", "transaction_id", "paid_at"])

                    order = payment.order
                    order.status = "CONFIRMED"
                    order.save(update_fields=["status"])

                    send_mail(
                        subject=f"Payment Received — Order #{order.id}",
                        message=(
                            f"Hi {order.user.email},\n\n"
                            f"Payment for order #{order.id} has been received.\n"
                            f"Amount: ${payment.amount}\n"
                            f"Transaction: {payment.transaction_id}\n\n"
                            f"Your order is now being processed.\n"
                            f"Thank you for shopping with ShopEase!"
                        ),
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[order.user.email],
                        fail_silently=True,
                    )
            except Payment.DoesNotExist:
                pass

    return HttpResponse(status=200)
