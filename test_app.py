import json
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import app


class APITestCase(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.data_file = Path(self.tmpdir.name) / "messages.json"
        self._original_data_file = app.DATA_FILE
        app.DATA_FILE = self.data_file
        self.server = app.create_server(host="127.0.0.1", port=0)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        app.DATA_FILE = self._original_data_file
        self.tmpdir.cleanup()

    def request(self, method, path, payload=None):
        data = None
        headers = {}
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        req = Request(
            f"http://127.0.0.1:{self.port}{path}",
            data=data,
            headers=headers,
            method=method
        )
        try:
            with urlopen(req, timeout=5) as response:
                return response.status, json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            body = error.read().decode("utf-8")
            return error.code, json.loads(body) if body else {}

    def create(self, message):
        status, body = self.request("POST", "/messages", {"message": message})
        self.assertEqual(status, 201)
        return body["message"]

    def test_health(self):
        status, body = self.request("GET", "/health")
        self.assertEqual(status, 200)
        self.assertEqual(body["status"], "active")

    def test_messages_initially_empty(self):
        status, body = self.request("GET", "/messages")
        self.assertEqual(status, 200)
        self.assertEqual(body["total"], 0)
        self.assertEqual(body["messages"], [])

    def test_create_message(self):
        item = self.create("Pesan pertama dari praktikum")
        self.assertEqual(item["message"], "Pesan pertama dari praktikum")
        self.assertIn("created_at", item)
        self.assertGreaterEqual(item["id"], 1)

    def test_create_rejects_empty_message(self):
        status, body = self.request("POST", "/messages", {"message": "   "})
        self.assertEqual(status, 400)
        self.assertIn("empty", body["error"])

    def test_create_rejects_too_long_message(self):
        status, _ = self.request("POST", "/messages", {"message": "x" * 501})
        self.assertEqual(status, 400)

    def test_create_rejects_invalid_json(self):
        req = Request(
            f"http://127.0.0.1:{self.port}/messages",
            data=b"{not-json",
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with self.assertRaises(HTTPError) as ctx:
            urlopen(req, timeout=5)
        self.assertEqual(ctx.exception.code, 400)

    def test_get_message_by_id(self):
        item = self.create("Pesan dengan id")
        status, body = self.request("GET", f"/messages/{item['id']}")
        self.assertEqual(status, 200)
        self.assertEqual(body["message"]["id"], item["id"])

    def test_get_message_by_id_not_found(self):
        status, _ = self.request("GET", "/messages/999")
        self.assertEqual(status, 404)

    def test_search_filter(self):
        self.create("catatan rapat")
        self.create("catatan kuliah")
        self.create("belanja bulanan")
        status, body = self.request("GET", "/messages?search=catatan")
        self.assertEqual(status, 200)
        self.assertEqual(body["total"], 2)

    def test_limit_filter(self):
        for index in range(3):
            self.create(f"pesan {index}")
        status, body = self.request("GET", "/messages?limit=2")
        self.assertEqual(status, 200)
        self.assertEqual(body["total"], 2)

    def test_delete_by_index(self):
        self.create("akan dihapus")
        status, body = self.request("DELETE", "/messages?index=0")
        self.assertEqual(status, 200)
        self.assertEqual(body["removed"]["message"], "akan dihapus")
        _, listing = self.request("GET", "/messages")
        self.assertEqual(listing["total"], 0)

    def test_delete_out_of_range(self):
        status, _ = self.request("DELETE", "/messages?index=999")
        self.assertEqual(status, 404)

    def test_delete_missing_index(self):
        status, _ = self.request("DELETE", "/messages")
        self.assertEqual(status, 400)

    def test_data_persists_across_restart(self):
        self.create("data harus bertahan")
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

        self.server = app.create_server(host="127.0.0.1", port=0)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

        status, body = self.request("GET", "/messages")
        self.assertEqual(status, 200)
        self.assertEqual(body["total"], 1)
        self.assertEqual(body["messages"][0]["message"], "data harus bertahan")


if __name__ == "__main__":
    unittest.main(verbosity=2)
