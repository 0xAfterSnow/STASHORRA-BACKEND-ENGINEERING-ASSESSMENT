from django.contrib.auth.models import AbstractUser
from django.db import models
from utils.enums.user import UserAccountType


class User(AbstractUser):
    """
    Custom user model that adds a `role` field on top of Django's
    built-in auth fields.

    Roles:
        - USER: default role, can manage only their own listings/bids.
        - ADMIN: full access to all resources.

    We keep this separate from `is_staff`/`is_superuser` (which still
    control Django admin-site access) so that the marketplace's notion
    of "admin" is explicit and easy to reason about via the API.
    """

    role = models.CharField(max_length=10, choices=UserAccountType.choices(), default=UserAccountType.USER.value)

    @property
    def is_admin_role(self) -> bool:
        return self.role == UserAccountType.ADMIN.value or self.is_superuser

    def __str__(self):
        return f"{self.username} ({self.role})"
