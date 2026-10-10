import os

from django.core.management.base import BaseCommand

from accounts.models import Role, User
from tenants.models import Tenant


class Command(BaseCommand):
    help = ("Pehla Owner user + store banata hai (ADMIN_USERNAME / ADMIN_PASSWORD / TENANT_NAME env). "
            "Agar user pehle se hai to kuch nahi badalta.")

    def handle(self, *args, **opts):
        username = os.environ.get("ADMIN_USERNAME", "").strip()
        password = os.environ.get("ADMIN_PASSWORD", "")
        if not username or not password:
            self.stdout.write("ADMIN_USERNAME / ADMIN_PASSWORD set nahi hain, skip.")
            return
        if User.objects.filter(username=username).exists():
            self.stdout.write(f"User '{username}' pehle se hai, skip.")
            return
        tenant = Tenant.objects.create(name=os.environ.get("TENANT_NAME", "My Store"))
        User.objects.create_user(username=username, password=password,
                                 tenant=tenant, role=Role.OWNER, is_staff=True, is_superuser=True)
        self.stdout.write(f"Owner '{username}' ban gaya.")
