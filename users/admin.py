from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from users.models import User

# Register your models here.

class UserAdmin(BaseUserAdmin):

    # Custom admin configuration for User model. Extends Django's default UserAdmin.

    # Fields to display in admin list view
    list_display = (
        "id",
        "email",
        "username",
        "is_email_verified",
        "is_staff",
        "is_active",
        "is_log_in",
        "is_private_account",
        "created_at",
    )

    readonly_fields = ("created_at",)

    # Filters in right sidebar
    list_filter = (
        "is_staff",
        "is_active",
        "is_private_account",
        "gender",
        "is_email_verified",
    )

    # Search functionality
    search_fields = ("email", "username")

    # Default ordering
    ordering = ("-created_at",)

    # Fieldsets for editing user
    fieldsets = BaseUserAdmin.fieldsets + (
        (
            "Additional Info",
            {
                "fields": (
                    "profile_picture",
                    "bio",
                    "date_of_birth",
                    "gender",
                    "is_private_account",
                    "is_log_in",
                    "created_at",
                )
            },
        ),
    )

    # Fields when creating a new user in admin
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (
            "Additional Info",
            {
                "fields": (
                    "email",
                    "username",
                    "profile_picture",
                    "bio",
                    "date_of_birth",
                    "gender",
                    "is_private_account",
                )
            },
        ),
    )

admin.site.register(User, UserAdmin)