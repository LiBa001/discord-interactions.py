#!/usr/bin/env python

"""
MIT License

Original work Copyright (c) 2020 Ian Webster
Modified work Copyright (c) 2020-2021 Linus Bartsch

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from discord_interactions import InteractionType, InteractionResponseType, verify_key
from flask import request, jsonify
from functools import wraps


def verify_key_decorator(client_public_key):
    def _decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # Verify request
            signature = request.headers.get("X-Signature-Ed25519")
            timestamp = request.headers.get("X-Signature-Timestamp")

            if (
                signature is None
                or timestamp is None
                or not verify_key(request.data, signature, timestamp, client_public_key)
            ):
                return "Bad request signature", 401

            # Automatically respond to pings
            if request.json and request.json.get("type") == InteractionType.PING:
                return jsonify({"type": InteractionResponseType.PONG})

            # Pass through
            return f(*args, **kwargs)

        return wrapper

    return _decorator
