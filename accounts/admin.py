from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser
from .models import Profile


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):

    list_display = (
        "id",
        "email",
        "username",
        "user_type",
        "is_email_verified",
        "is_staff",
        "is_active",
    )

    list_filter = (
        "user_type",
        "is_active",
        "is_email_verified",
    )

    search_fields = (
        "email",
        "username",
    )

    ordering = ("-date_joined",)

    fieldsets = (
        (None, {"fields": ("username", "email", "password")}),
        ("Role Info", {"fields": ("user_type", "phone_number", "is_email_verified")}),
        ("Permissions", {"fields": ("is_staff", "is_active", "is_superuser", "groups")}),
        ("Dates", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "username",
                "email",
                "user_type",
                "phone_number",
                "password1",
                "password2",
            ),
        }),
    )


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "user",
        "city",
        "country",
    )

    search_fields = (
        "user__email",
        "user__username",
    )