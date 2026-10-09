from accounts.permissions import RoleWritePermission


class ChannelPermission(RoleWritePermission):
    """Credentials sensitive hain: sirf Owner/Admin connect ya hata sakte hain."""
    write_roles = {"OWNER", "ADMIN"}


class SyncPermission(RoleWritePermission):
    """Publish/retry: catalog roles. Read: har tenant user."""
    write_roles = {"OWNER", "ADMIN", "CATALOG_MANAGER"}
