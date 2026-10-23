import unittest

from app.app import KNOWN_BAD, MAX_TEXT_CHARS, create_app


class AppTests(unittest.TestCase):
    def setUp(self):
        self.client = create_app().test_client()

    def test_health(self):
        r = self.client.get("/health")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json(), {"status": "ok"})

    def test_security_headers_on_every_response(self):
        for path in ("/health", "/does-not-exist"):
            r = self.client.get(path)
            self.assertEqual(r.headers["X-Content-Type-Options"], "nosniff")
            self.assertEqual(r.headers["X-Frame-Options"], "DENY")
            self.assertIn("default-src 'none'", r.headers["Content-Security-Policy"])
            self.assertNotIn("Server", r.headers)

    def test_hash(self):
        r = self.client.post("/api/hash", json={"text": "hello"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["sha256"], "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824")

    def test_hash_rejects_bad_input(self):
        self.assertEqual(self.client.post("/api/hash", data="not json").status_code, 400)
        self.assertEqual(self.client.post("/api/hash", json={"text": 123}).status_code, 400)
        self.assertEqual(self.client.post("/api/hash", json={"text": "a" * (MAX_TEXT_CHARS + 1)}).status_code, 413)

    def test_body_size_limit(self):
        r = self.client.post("/api/hash", data="x" * 20000, content_type="application/json")
        self.assertEqual(r.status_code, 413)

    def test_lookup(self):
        known = next(iter(KNOWN_BAD))
        r = self.client.get(f"/api/lookup/{known.upper()}")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.get_json()["known_bad"])
        clean = self.client.get("/api/lookup/" + "0" * 64).get_json()
        self.assertFalse(clean["known_bad"])

    def test_lookup_validates_input(self):
        for bad in ("abc", "g" * 64, "../../etc/passwd"):
            r = self.client.get(f"/api/lookup/{bad}")
            self.assertIn(r.status_code, (400, 404), bad)

    def test_wrong_method(self):
        self.assertEqual(self.client.get("/api/hash").status_code, 405)


if __name__ == "__main__":
    unittest.main()
