import os
from io import StringIO
from unittest import mock

from django.core.management import call_command
from django.test import TestCase

from accounts.models import Role, User


class BootstrapAdminTests(TestCase):
    def run_cmd(self, **env):
        with mock.patch.dict(os.environ, env, clear=False):
            out = StringIO()
            call_command("bootstrap_admin", stdout=out)
            return out.getvalue()

    def test_creates_owner_once(self):
        self.run_cmd(ADMIN_USERNAME="boss", ADMIN_PASSWORD="s3cret-pass", TENANT_NAME="Acme")
        u = User.objects.get(username="boss")
        self.assertEqual(u.role, Role.OWNER)
        self.assertEqual(u.tenant.name, "Acme")
        self.assertTrue(u.check_password("s3cret-pass"))
        out = self.run_cmd(ADMIN_USERNAME="boss", ADMIN_PASSWORD="other")
        self.assertIn("pehle se hai", out)
        self.assertTrue(User.objects.get(username="boss").check_password("s3cret-pass"))

    def test_skips_without_env(self):
        with mock.patch.dict(os.environ, {"ADMIN_USERNAME": "", "ADMIN_PASSWORD": ""}):
            out = StringIO()
            call_command("bootstrap_admin", stdout=out)
        self.assertFalse(User.objects.exists())
