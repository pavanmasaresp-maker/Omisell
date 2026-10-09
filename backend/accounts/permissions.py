from rest_framework.permissions import SAFE_METHODS, BasePermission

CATALOG_WRITE_ROLES = {"OWNER", "ADMIN", "CATALOG_MANAGER"}
INVENTORY_WRITE_ROLES = {"OWNER", "ADMIN", "INVENTORY_MANAGER"}


class HasTenant(BasePermission):
    def has_permission(self, request, view):
        u = request.user
        return bool(u and u.is_authenticated and u.tenant_id)


class RoleWritePermission(HasTenant):
    """Read: any user of the tenant. Write: only roles in write_roles."""
    write_roles = set()

    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        if request.method in SAFE_METHODS:
            return True
        return request.user.role in self.write_roles


class CatalogPermission(RoleWritePermission):
    write_roles = CATALOG_WRITE_ROLES


class InventoryPermission(RoleWritePermission):
    write_roles = INVENTORY_WRITE_ROLES
