from flask import Flask, request, jsonify
from discord_interaction import Interaction, InteractionType, InteractionResponse, InteractionResponseType
from discord_interaction.utils import verify_key
from discord_command import ApplicationCommand, ocm
from typing import Callable, Union, Type, Dict


_CommandCallback = Callable[[Union[Interaction, ocm.Command]], InteractionResponse]


class Interactions:
    def __init__(self, app: Flask, public_key: str):
        self._app = app
        self._public_key = public_key

        app.add_url_rule("/", "interactions", self._main, methods=["POST"])

        self._commands: Dict[str, ApplicationCommand] = {}
        self._callbacks: Dict[str, _CommandCallback] = {}

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
            cb = self._callbacks[cmd]

            cb_data = interaction
            if len(annotations := cb.__annotations__.values()) > 0:
                cmd_type = next(iter(annotations))
                if issubclass(cmd_type, ocm.Command):
                    cb_data = cmd_type.wrap(interaction)

            return jsonify(cb(cb_data).to_dict())
        else:
            return "Unknown interaction type", 501

    def register_command(self, command: Union[ApplicationCommand, Type[ocm.Command], str], callback: _CommandCallback):
        if isinstance(command, ApplicationCommand):
            self._commands[command.name] = command
            self._callbacks[command.name] = callback
        elif issubclass(command, ocm.Command):
            self._commands[command.__cmd_name__] = command.to_application_command()
            self._callbacks[command.__cmd_name__] = callback
        else:
            self._callbacks[command] = callback

    def command(self, command: Union[ApplicationCommand, str] = None, _f: _CommandCallback = None):
        """ A decorator to register a slash command. Calls :meth:`register_command` internally. """

        def decorator(f: _CommandCallback):
            if command is not None:
                self.register_command(command, f)
            else:
                _command = next(iter(f.__annotations__.values()))  # get :class:`ocm.Command` from type annotation
                self.register_command(_command, f)

        return decorator(_f) if _f is not None else decorator
