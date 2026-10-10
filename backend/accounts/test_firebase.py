import os
from unittest import mock

from django.test import TestCase
from rest_framework.test import APIClient

from accounts import firebase_auth
from accounts.models import Role, User
from tenants.models import Tenant

URL = "/api/v1/auth/google"


def claims(email="seller@gmail.com", verified=True, provider="google.com", name="Ravi Seller"):
    return {"email": email, "email_verified": verified, "name": name, "sub": "uid123456",
            "firebase": {"sign_in_provider": provider}}


class GoogleLoginTests(TestCase):
    def post(self, c=None, env=None, token="tok", exc=None):
        patcher = mock.patch("accounts.firebase_auth.verify",
                             side_effect=exc, return_value=c if exc is None else None)
        with patcher, mock.patch.dict(os.environ, env or {}, clear=False):
            return APIClient().post(URL, {"id_token": token}, format="json")

    def test_new_google_user_gets_own_store_as_owner(self):
        r = self.post(claims())
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.data["token"])
        u = User.objects.get(email="seller@gmail.com")
        self.assertEqual(u.role, Role.OWNER)
        self.assertIsNotNone(u.tenant_id)
        self.assertFalse(u.has_usable_password())
        self.assertEqual(Tenant.objects.count(), 1)

    def test_second_login_reuses_same_user(self):
        self.post(claims())
        r = self.post(claims())
        self.assertEqual(r.status_code, 200)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(Tenant.objects.count(), 1)

    def test_existing_user_with_same_email_is_linked(self):
        t = Tenant.objects.create(name="Old")
        existing = User.objects.create_user("boss", password="x", email="Seller@Gmail.com",
                                            tenant=t, role=Role.ADMIN)
        r = self.post(claims())
        self.assertEqual(r.status_code, 200)
        self.assertEqual(User.objects.count(), 1)
        from rest_framework.authtoken.models import Token
        self.assertEqual(Token.objects.get(key=r.data["token"]).user_id, existing.id)

    def test_unverified_email_rejected(self):
        self.assertEqual(self.post(claims(verified=False)).status_code, 400)
        self.assertFalse(User.objects.exists())

    def test_non_google_provider_rejected(self):
        self.assertEqual(self.post(claims(provider="password")).status_code, 400)
        self.assertFalse(User.objects.exists())

    def test_invalid_token(self):
        self.assertEqual(self.post(exc=ValueError("bad")).status_code, 400)

    def test_not_configured(self):
        self.assertEqual(self.post(exc=firebase_auth.NotConfigured("x")).status_code, 503)

    def test_missing_token(self):
        self.assertEqual(APIClient().post(URL, {}, format="json").status_code, 400)

    def test_signup_can_be_closed_but_existing_users_still_login(self):
        r = self.post(claims(), env={"GOOGLE_SIGNUP": "0"})
        self.assertEqual(r.status_code, 403)
        t = Tenant.objects.create(name="Old")
        User.objects.create_user("boss", password="x", email="seller@gmail.com", tenant=t, role=Role.OWNER)
        self.assertEqual(self.post(claims(), env={"GOOGLE_SIGNUP": "0"}).status_code, 200)

    def test_allowlist(self):
        env = {"FIREBASE_ALLOWED_EMAILS": "other@gmail.com"}
        self.assertEqual(self.post(claims(), env=env).status_code, 403)
        env = {"FIREBASE_ALLOWED_EMAILS": "SELLER@gmail.com, other@gmail.com"}
        self.assertEqual(self.post(claims(), env=env).status_code, 200)


class DeleteAccountTests(TestCase):
    def setUp(self):
        from catalog.models import Product
        self.tenant = Tenant.objects.create(name="Shop")
        self.other_tenant = Tenant.objects.create(name="Other")
        self.owner = User.objects.create_user("owner", password="x", tenant=self.tenant, role=Role.OWNER)
        self.staff = User.objects.create_user("staff", password="x", tenant=self.tenant, role=Role.VIEWER)
        self.stranger = User.objects.create_user("stranger", password="x", tenant=self.other_tenant, role=Role.OWNER)
        Product.objects.create(tenant=self.tenant, title="Cap")
        Product.objects.create(tenant=self.other_tenant, title="Other cap")

    def api(self, user):
        c = APIClient()
        c.force_authenticate(user=user)
        return c

    def test_requires_confirmation(self):
        r = self.api(self.owner).delete("/api/v1/auth/me", {}, format="json")
        self.assertEqual(r.status_code, 400)
        self.assertTrue(User.objects.filter(pk=self.owner.pk).exists())

    def test_owner_delete_removes_whole_store_only(self):
        from catalog.models import Product
        r = self.api(self.owner).delete("/api/v1/auth/me", {"confirm": "DELETE"}, format="json")
        self.assertEqual(r.status_code, 204)
        self.assertFalse(Tenant.objects.filter(pk=self.tenant.pk).exists())
        self.assertFalse(User.objects.filter(username__in=["owner", "staff"]).exists())
        self.assertEqual(Product.objects.filter(title="Cap").count(), 0)
        self.assertTrue(Tenant.objects.filter(pk=self.other_tenant.pk).exists())
        self.assertEqual(Product.objects.filter(title="Other cap").count(), 1)

    def test_staff_delete_removes_only_self(self):
        r = self.api(self.staff).delete("/api/v1/auth/me", {"confirm": "DELETE"}, format="json")
        self.assertEqual(r.status_code, 204)
        self.assertFalse(User.objects.filter(username="staff").exists())
        self.assertTrue(User.objects.filter(username="owner").exists())
        self.assertTrue(Tenant.objects.filter(pk=self.tenant.pk).exists())

    def test_anonymous_cannot_delete(self):
        r = APIClient().delete("/api/v1/auth/me", {"confirm": "DELETE"}, format="json")
        self.assertIn(r.status_code, (401, 403))
