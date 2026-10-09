from unittest import mock

from django.test import TestCase

from accounts.testutils import client_for, make_user
from marketplaces.adapters.base import AdapterError
from marketplaces.models import ChannelConnection
from tenants.models import Tenant

URL = "/api/v1/channels/connections"
GQL = "marketplaces.adapters.shopify.ShopifyAdapter._graphql"
SHOP = {"channel": "SHOPIFY", "name": "My Shop", "shop_domain": "mystore.myshopify.com",
        "access_token": "shpat_secret123"}


class ConnectionTests(TestCase):
    def setUp(self):
        self.t1 = Tenant.objects.create(name="T1")
        self.t2 = Tenant.objects.create(name="T2")
        self.owner = client_for(make_user(self.t1, "o1", "OWNER"))
        self.catalog = client_for(make_user(self.t1, "c1", "CATALOG_MANAGER"))
        self.viewer = client_for(make_user(self.t1, "v1", "VIEWER"))
        self.other = client_for(make_user(self.t2, "o2", "OWNER"))

    def shopify(self, client=None, **over):
        with mock.patch(GQL, return_value={"shop": {"name": "Test Store"}}):
            return (client or self.owner).post(URL, {**SHOP, **over}, format="json")

    def test_demo_connect_ok_and_token_hidden(self):
        r = self.owner.post(URL, {"channel": "DEMO", "name": "Demo", "access_token": "demo"},
                            format="json")
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.json()["status"], "CONNECTED")
        self.assertNotIn("access_token", r.json())
        self.assertNotIn("credentials_encrypted", r.json())

    def test_token_encrypted_at_rest(self):
        self.assertEqual(self.shopify().status_code, 201)
        conn = ChannelConnection.objects.get()
        self.assertNotIn("shpat_secret123", conn.credentials_encrypted)
        self.assertEqual(conn.get_credentials()["access_token"], "shpat_secret123")

    def test_wrong_token_saved_as_error(self):
        with mock.patch(GQL, side_effect=AdapterError("token galat", needs_action=True)):
            r = self.owner.post(URL, SHOP, format="json")
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.json()["status"], "ERROR")
        self.assertIn("token galat", r.json()["last_error"])

    def test_shop_domain_validation_blocks_other_hosts(self):
        with mock.patch(GQL) as g:
            r = self.owner.post(URL, {**SHOP, "shop_domain": "evil.com"}, format="json")
            self.assertEqual(r.status_code, 400)
            g.assert_not_called()

    def test_only_owner_admin_can_connect(self):
        self.assertEqual(self.shopify(client=self.catalog).status_code, 403)
        self.assertEqual(self.shopify(client=self.viewer).status_code, 403)
        self.assertEqual(self.viewer.get(URL).status_code, 200)

    def test_tenant_isolation(self):
        cid = self.shopify().json()["id"]
        self.assertEqual(self.other.get(URL).json()["results"], [])
        self.assertEqual(self.other.post(f"{URL}/{cid}/check").status_code, 404)

    def test_recheck_updates_status(self):
        with mock.patch(GQL, side_effect=AdapterError("down", retryable=True)):
            cid = self.owner.post(URL, SHOP, format="json").json()["id"]
        with mock.patch(GQL, return_value={"shop": {"name": "Test Store"}}):
            r = self.owner.post(f"{URL}/{cid}/check")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["status"], "CONNECTED")

    def test_duplicate_rejected(self):
        self.assertEqual(self.shopify().status_code, 201)
        self.assertEqual(self.shopify().status_code, 400)

    def test_delete(self):
        cid = self.shopify().json()["id"]
        self.assertEqual(self.owner.delete(f"{URL}/{cid}").status_code, 204)
        self.assertEqual(ChannelConnection.objects.count(), 0)
