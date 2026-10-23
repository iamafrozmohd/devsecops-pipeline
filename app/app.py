"""Small hash-lookup API used as the target of the DevSecOps pipeline.

It is deliberately simple, but written the way a security reviewer would expect:
strict input validation, a request size limit, security headers, no debug mode,
and no secrets in code.
"""

from __future__ import annotations

import hashlib
import os
import re

from flask import Flask, jsonify, request

MAX_BODY_BYTES = 16 * 1024
MAX_TEXT_CHARS = 10_000
SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")

# A tiny local "known bad" list so the API has something meaningful to answer.
# This is the SHA-256 of the harmless EICAR antivirus test file.
KNOWN_BAD = {
    "275a021bbfb6489e54d471899f7db9d1663fc695ec2fe2a2c4538aabf651fd0f": "EICAR-Test-File",
}

SECURITY_HEADERS = {
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "geolocation=(), camera=(), microphone=()",
    "Cache-Control": "no-store",
    "Cross-Origin-Resource-Policy": "same-origin",
}


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = MAX_BODY_BYTES

    @app.after_request
    def add_security_headers(response):
        response.headers.update(SECURITY_HEADERS)
        response.headers.pop("Server", None)
        return response

    @app.get("/health")
    def health():
        return jsonify(status="ok")

    @app.post("/api/hash")
    def hash_text():
        """Return the SHA-256 of the submitted text: {"text": "..."}."""
        data = request.get_json(silent=True)
        if not isinstance(data, dict) or not isinstance(data.get("text"), str):
            return jsonify(error='expected JSON body like {"text": "..."}'), 400
        text = data["text"]
        if len(text) > MAX_TEXT_CHARS:
            return jsonify(error=f"text must be at most {MAX_TEXT_CHARS} characters"), 413
        return jsonify(sha256=hashlib.sha256(text.encode("utf-8")).hexdigest())

    @app.get("/api/lookup/<sha256>")
    def lookup(sha256: str):
        """Check a SHA-256 against the local known-bad list."""
        value = sha256.lower()
        if not SHA256_PATTERN.match(value):
            return jsonify(error="expected a 64-character hex SHA-256"), 400
        name = KNOWN_BAD.get(value)
        return jsonify(sha256=value, known_bad=name is not None, name=name)

    @app.errorhandler(404)
    def not_found(_error):
        return jsonify(error="not found"), 404

    @app.errorhandler(405)
    def method_not_allowed(_error):
        return jsonify(error="method not allowed"), 405

    @app.errorhandler(413)
    def too_large(_error):
        return jsonify(error="request too large"), 413

    return app


app = create_app()

if __name__ == "__main__":
    # Local development only. In the container the app runs under gunicorn.
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "8080")), debug=False)
