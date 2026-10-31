import json
import os
import re
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

DATA_FILE = Path(os.getenv("DATA_FILE", "/var/lib/backend_data/messages.json"))
MAX_MESSAGE_LENGTH = 500
MAX_LIMIT = 100


def read_messages():
    if not DATA_FILE.exists():
        return []
    try:
        data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    if not isinstance(data, list):
        return []
    return data


def write_messages(messages):
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(
        json.dumps(messages, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )


def normalize(messages):
    changed = False
    next_id = 1
    for item in messages:
        if "id" not in item:
            item["id"] = next_id
            changed = True
        next_id = max(next_id, item["id"]) + 1
    if changed:
        write_messages(messages)
    return messages


def save_message(message):
    messages = normalize(read_messages())
    item = {
        "id": messages[-1]["id"] + 1 if messages else 1,
        "message": message,
        "created_at": datetime.now(UTC).isoformat()
    }
    messages.append(item)
    write_messages(messages)
    return item


def find_message(messages, message_id):
    for item in messages:
        if item.get("id") == message_id:
            return item
    return None


class APIHandler(BaseHTTPRequestHandler):
    server_version = "PythonCRUDAPI/1.1"

    def send_json(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_json(200, {"status": "ok"})

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"

        if path in ("/", "/health"):
            return self.send_json(200, {
                "status": "active", "service": "Backend API"
            })

        if path == "/messages":
            messages = normalize(read_messages())
            query = parse_qs(parsed.query)

            search = (query.get("search") or [""])[0].strip().lower()
            if search:
                messages = [
                    item for item in messages
                    if search in str(item.get("message", "")).lower()
                ]

            limit = None
            if "limit" in query:
                try:
                    limit = int(query["limit"][0])
                except ValueError:
                    return self.send_json(400, {"error": "limit must be an integer"})
                if limit < 0:
                    return self.send_json(400, {"error": "limit must be zero or greater"})
                messages = messages[:min(limit, MAX_LIMIT)]

            return self.send_json(200, {
                "messages": messages, "total": len(messages)
            })

        match = re.fullmatch(r"/messages/(\d+)", path)
        if match:
            message = find_message(normalize(read_messages()), int(match.group(1)))
            if message is None:
                return self.send_json(404, {"error": "Message not found"})
            return self.send_json(200, {"message": message})

        return self.send_json(404, {"error": "Endpoint not found"})

    def do_POST(self):
        if urlparse(self.path).path.rstrip("/") != "/messages":
            return self.send_json(404, {"error": "Endpoint not found"})

        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
        except (ValueError, json.JSONDecodeError):
            return self.send_json(400, {"error": "Invalid JSON request body"})

        if not isinstance(payload, dict):
            return self.send_json(400, {"error": "Invalid JSON request body"})

        message = str(payload.get("message", "")).strip()
        if not message:
            return self.send_json(400, {"error": "message must not be empty"})
        if len(message) > MAX_MESSAGE_LENGTH:
            return self.send_json(400, {
                "error": "message must be 500 characters or fewer"
            })

        return self.send_json(201, {
            "status": "created", "message": save_message(message)
        })

    def do_DELETE(self):
        parsed = urlparse(self.path)
        if parsed.path.rstrip("/") != "/messages":
            return self.send_json(404, {"error": "Endpoint not found"})

        query = parse_qs(parsed.query)
        if "index" not in query:
            return self.send_json(400, {"error": "Missing index parameter"})

        try:
            index = int(query["index"][0])
        except ValueError:
            return self.send_json(400, {"error": "Index must be an integer"})

        messages = normalize(read_messages())
        if index < 0 or index >= len(messages):
            return self.send_json(404, {"error": "Message not found"})

        removed = messages.pop(index)
        write_messages(messages)
        return self.send_json(200, {"status": "deleted", "removed": removed})

    def log_message(self, fmt, *args):
        print(f"[{self.log_date_time_string()}] {fmt % args}", flush=True)


def create_server(host="0.0.0.0", port=5000):
    return ThreadingHTTPServer((host, port), APIHandler)


if __name__ == "__main__":
    print("Backend API listening on 0.0.0.0:5000", flush=True)
    create_server().serve_forever()
