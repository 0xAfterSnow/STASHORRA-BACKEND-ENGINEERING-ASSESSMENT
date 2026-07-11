from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdminRole(BasePermission):
    """Grants access only to users whose role is 'admin' (or superusers)."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "is_admin_role", False)
        )


class IsOwnerOrAdmin(BasePermission):
    """
    Object-level permission: safe methods (GET/HEAD/OPTIONS) are allowed
    for anyone, but write access is restricted to the object's owner or
    an admin user.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True

        user = request.user
        if not user or not user.is_authenticated:
            return False

        if getattr(user, "is_admin_role", False):
            return True

        owner = getattr(obj, "owner", None)
        return owner == user
