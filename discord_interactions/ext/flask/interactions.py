#!/usr/bin/env python

"""
MIT License

Copyright (c) 2020-2021 Linus Bartsch

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

from flask import Flask, request, jsonify, Response, g, current_app
from discord_interactions import Interaction, verify_key
from threading import Thread
import logging

from ..base_extension import BaseExtension


logger = logging.getLogger("discord_interactions")


def _is_submodule(parent, child):
    return parent == child or child.startswith(parent + ".")


class Interactions(BaseExtension):
    def __init__(
        self, app: Flask, public_key: str, app_id: int = None, path: str = "/"
    ):
        super().__init__(public_key, app_id)

        self._app = app
        self._path = path

        app.add_url_rule(
            path, "interactions", app.ensure_sync(self._main), methods=["POST"]
        )
        app.after_request_funcs.setdefault(None, []).append(self._after_request)

    @property
    def path(self) -> str:
        return self._path

    def _verify_request(self):
        signature = request.headers.get("X-Signature-Ed25519")
        timestamp = request.headers.get("X-Signature-Timestamp")

        if signature is None or timestamp is None:
            return False

        return verify_key(request.data, signature, timestamp, self._public_key)

    async def _main(self):
        g.interaction = None
        g.interaction_response = None

        # Verify request
        if not current_app.config["TESTING"]:
            if not self._verify_request():
                logger.debug("invalid request signature")
                return "Bad request signature", 401

        # Handle interactions
        interaction = Interaction(**request.json)

        resp = await self._handle_interaction(interaction)

        if resp is None:
            return "Unknown interaction type", 501

        g.interaction = interaction
        g.interaction_response = resp

        return jsonify(resp.to_dict())

    def _after_request(self, response: Response):
        try:
            interaction = g.interaction
            interaction_response = g.interaction_response
        except AttributeError:
            return response

        if interaction is None or current_app.config["TESTING"]:
            return response

        target, ctx = self._get_after_request_data(interaction, interaction_response)

        if target and target.after_callback is not None:
            t = Thread(
                target=current_app.ensure_sync(target.after_callback), args=(ctx,)
            )
            t.start()

        return response
