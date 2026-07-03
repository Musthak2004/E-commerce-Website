from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.db.models import Max, Prefetch
from django.template.loader import render_to_string
from django.utils import timezone

from cart.models import AbandonedCartReminder, Cart, CartItem


class Command(BaseCommand):
    help = (
        "Find abandoned carts and send recovery reminder emails. "
        "Carts with items last modified more than --hours ago, "
        "where no order was placed since, receive a reminder."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--hours",
            type=int,
            default=6,
            help="Hours of inactivity before a cart is considered abandoned (default: 6).",
        )
        parser.add_argument(
            "--type",
            type=str,
            default="FIRST",
            choices=["FIRST", "SECOND", "FINAL"],
            help="Reminder type to send (default: FIRST).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="List carts that would get a reminder without sending anything.",
        )

    def handle(self, *args, **options):
        hours = options["hours"]
        reminder_type = options["type"]
        dry_run = options["dry_run"]

        cutoff = timezone.now() - timedelta(hours=hours)

        self.stdout.write(
            f"Checking carts inactive since {cutoff.isoformat()} "
            f"({hours} hour{'s' if hours != 1 else ''}) …"
        )

        # Carts with items whose last item was added before cutoff
        stale_carts = Cart.objects.filter(
            items__isnull=False,
        ).annotate(
            last_activity=Max("items__created_at"),
        ).filter(
            last_activity__lte=cutoff,
        ).select_related(
            "user",
        ).prefetch_related(
            Prefetch(
                "items",
                queryset=CartItem.objects.select_related("product"),
            ),
        )

        # Exclude carts that already received this reminder type
        reminded_ids = set(
            AbandonedCartReminder.objects.filter(
                reminder_type=reminder_type,
            ).values_list("cart_id", flat=True)
        )
        stale_carts = [c for c in stale_carts if c.id not in reminded_ids]

        # Exclude carts with a recent order (after last activity)
        from orders.models import Order
        candidates = []
        for cart in stale_carts:
            last_activity = cart.last_activity
            has_recent_order = Order.objects.filter(
                user=cart.user,
                created_at__gte=last_activity,
            ).exists()
            if not has_recent_order:
                candidates.append(cart)

        self.stdout.write(f"Found {len(candidates)} abandoned cart(s) to process.")

        if dry_run:
            for cart in candidates:
                items_summary = ", ".join(
                    f"{item.quantity}x {item.product.name}"
                    for item in cart.items.all()
                )
                self.stdout.write(
                    f"  [DRY-RUN] Would notify {cart.user.email}: "
                    f"{items_summary}"
                )
            return

        sent = 0
        errors = 0

        for cart in candidates:
            try:
                self._send_reminder(cart, reminder_type)
                sent += 1
                self.stdout.write(f"  ✓ Reminder sent to {cart.user.email}")
            except Exception as e:
                self.stderr.write(f"  ✗ Failed for {cart.user.email}: {e}")
                errors += 1

        self.stdout.write(
            self.style.SUCCESS(f"Done. Sent {sent}, errors {errors}.")
        )

    def _send_reminder(self, cart, reminder_type):
        """Send an abandoned cart recovery email and log the reminder."""

        items = list(cart.items.all())
        cart_url = f"{settings.BASE_URL}/cart/"

        context = {
            "user": cart.user,
            "items": items,
            "cart_url": cart_url,
            "total": cart.total_price,
            "reminder_type": reminder_type.lower(),
        }

        subject = "Your cart is waiting — complete your order!"
        text_message = render_to_string("emails/abandoned_cart.txt", context)
        html_message = render_to_string("emails/abandoned_cart.html", context)

        send_mail(
            subject=subject,
            message=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[cart.user.email],
            html_message=html_message,
            fail_silently=False,
        )

        AbandonedCartReminder.objects.create(
            cart_id=cart.id,
            reminder_type=reminder_type,
        )
