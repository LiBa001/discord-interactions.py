from flask import Flask, request, jsonify
from discord_interaction import Interaction, InteractionType, InteractionResponse, InteractionResponseType
from discord_interaction.utils import verify_key
from discord_command import ApplicationCommand
from typing import Callable


class Interactions:
    def __init__(self, app: Flask, public_key: str):
        self._app = app
        self._public_key = public_key

        app.add_url_rule("/", "interactions", self._main, methods=["POST"])

        self._commands = {}
        self._callbacks = {}

    def _main(self):
        # Verify request
        signature = request.headers.get("X-Signature-Ed25519")
        timestamp = request.headers.get("X-Signature-Timestamp")

        if (
                signature is None or timestamp is None or
                not verify_key(request.data, signature, timestamp, self._public_key)
        ):
            return "Bad request signature", 401

        # Handle interactions
        interaction = Interaction(**request.json)

        if interaction.type == InteractionType.PING:
            return jsonify(InteractionResponse(InteractionResponseType.PONG).to_dict())
        elif interaction.type == InteractionType.APPLICATION_COMMAND:
            cmd = interaction.data.name
            return jsonify(self._callbacks[cmd](interaction).to_dict())
        else:
            return "Unknown interaction type", 501

    def register_command(self, command: ApplicationCommand, callback: Callable[[Interaction], InteractionResponse]):
        self._commands[command.name] = command
        self._callbacks[command.name] = callback

    def command(self, command: ApplicationCommand):
        """ A decorator to register a slash command. Calls :meth:`register_command` internally. """

        def decorator(f: Callable[[Interaction], InteractionResponse]):
            self.register_command(command, f)

        return decorator
