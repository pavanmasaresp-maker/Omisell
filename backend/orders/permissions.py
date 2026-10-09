from accounts.permissions import RoleWritePermission

ORDER_WRITE_ROLES = {"OWNER", "ADMIN", "ORDER_MANAGER"}


class OrderPermission(RoleWritePermission):
    write_roles = ORDER_WRITE_ROLES
