"""
Glick Web application.

Copyright (C) 2025 Ayrik Nabirahni. This file
is apart of the Glick project, and licensed under
the GNU AGPL-3.0-or-later. See LICENSE and README for more details.
"""

from __future__ import annotations

import os

from flask import Flask, jsonify, render_template, request

from files.vars import version_dec, version_enc, version_gli
from glickcrypt import DecryptionUnavailable, convert_text


def create_app() -> Flask:
    app = Flask(__name__)

    @app.after_request
    def add_iframe_headers(response):
        frame_ancestors = os.environ.get("GLICK_FRAME_ANCESTORS", "*")
        response.headers.pop("X-Frame-Options", None)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self'; "
            "img-src 'self' data:; "
            "connect-src 'self'; "
            "base-uri 'self'; "
            "form-action 'self'; "
            f"frame-ancestors {frame_ancestors}"
        )
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    @app.get("/")
    def index():
        return render_template(
            "index.html",
            embed=request.args.get("embed") == "1",
            version=version_gli,
            version_enc=version_enc,
            version_dec=version_dec,
        )

    @app.get("/embed")
    def embed():
        return render_template(
            "index.html",
            embed=True,
            version=version_gli,
            version_enc=version_enc,
            version_dec=version_dec,
        )

    @app.get("/healthz")
    def healthz():
        return jsonify(status="ok")

    @app.post("/api/convert")
    def convert():
        payload = request.get_json(silent=True) or {}
        mode = str(payload.get("mode", "encrypt"))
        text = str(payload.get("text", ""))

        try:
            conversion = convert_text(mode, text)
        except ValueError as exc:
            return jsonify(error=str(exc)), 400
        except DecryptionUnavailable as exc:
            return jsonify(error=str(exc)), 503

        return jsonify(
            mode=conversion.mode,
            result=conversion.result,
            text=conversion.text,
        )

    return app


app = create_app()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)
