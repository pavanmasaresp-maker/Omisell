import io
import json
import unittest
from unittest import mock

from marketplaces.adapters.base import AdapterError
from marketplaces.adapters.shopify import ShopifyAdapter


class Resp(io.BytesIO):
    def __enter__(self): return self
    def __exit__(self, *a): return False


class ClientCredsTests(unittest.TestCase):
    def setUp(self):
        ShopifyAdapter._TOKENS.clear()

    def test_static_token_unchanged(self):
        a = ShopifyAdapter("s.myshopify.com", "shpat_abc")
        self.assertEqual(a._token(), "shpat_abc")

    def test_client_credentials_fetched_once_and_cached(self):
        calls = []
        def fake(req, timeout=0):
            calls.append((req.full_url, req.data))
            return Resp(json.dumps({"access_token": "TOK", "expires_in": 86399}).encode())
        with mock.patch("urllib.request.urlopen", fake):
            a = ShopifyAdapter("s.myshopify.com", "cid:sec")
            self.assertEqual(a._token(), "TOK")
            self.assertEqual(ShopifyAdapter("s.myshopify.com", "cid:sec")._token(), "TOK")
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][0], "https://s.myshopify.com/admin/oauth/access_token")
        self.assertIn(b"grant_type=client_credentials", calls[0][1])
        self.assertIn(b"client_id=cid", calls[0][1])

    def test_bad_credentials_needs_action(self):
        import urllib.error
        def fake(req, timeout=0):
            raise urllib.error.HTTPError(req.full_url, 400, "bad", {}, None)
        with mock.patch("urllib.request.urlopen", fake):
            with self.assertRaises(AdapterError) as c:
                ShopifyAdapter("s.myshopify.com", "cid:sec")._token()
        self.assertTrue(c.exception.needs_action)

    def test_non_shopify_host_never_gets_secret(self):
        with self.assertRaises(AdapterError):
            ShopifyAdapter("evil.com", "cid:sec")._token()


if __name__ == "__main__":
    unittest.main()
