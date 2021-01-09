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

from flask import Flask, request, jsonify, Response, g
from discord_interactions import (
    Interaction,
    InteractionType,
    InteractionResponse,
    InteractionResponseType,
    InteractionApplicationCommandCallbackData,
    verify_key,
    ApplicationCommand,
    ApplicationClient,
)
from discord_interactions import ocm
from typing import Callable, Union, Type, Dict, List, Tuple, Optional, Any
from threading import Thread

from .context import AfterCommandContext, CommandContext


_CommandCallbackReturnType = Union[
    InteractionResponse, str, None, Tuple[Optional[str], bool]
]
_CommandCallback = Union[
    Callable[
        [Union[Interaction, ocm.Command]],
        _CommandCallbackReturnType,
    ],
    Callable[[CommandContext, Any], _CommandCallbackReturnType],
]
_AfterCommandCallback = Callable[[AfterCommandContext], None]
_DecoratedCommand = Union[ApplicationCommand, str, _CommandCallback, Type[ocm.Command]]


class CommandData:
    def __init__(self, name: str, cb: _CommandCallback, cmd: ApplicationCommand = None):
        self.name = name
        self.callback = cb
        self.application_command = cmd
        self.after_callback = None

    def after_command(self, f: _AfterCommandCallback):
        """
        A decorator to register a function that gets called after a command has run.
        The function will be internally called from within Flask's `after_request`
        function.
        """

        self.after_callback = f


class Interactions:
    def __init__(
        self, app: Flask, public_key: str, app_id: int = None, path: str = "/"
    ):
        self._app = app
        self._public_key = public_key
        self._app_id = app_id
        self._path = path

        app.add_url_rule(path, "interactions", self._main, methods=["POST"])
        app.after_request_funcs = {None: [self._after_request]}

        self._commands: Dict[str, CommandData] = {}

    @property
    def path(self) -> str:
        return self._path

    @property
    def commands(self) -> List[ApplicationCommand]:
        """ All registered application commands """

        return [
            cmd.application_command
            for cmd in self._commands.values()
            if cmd.application_command is not None
        ]

    def create_commands(self, client: ApplicationClient, guild: int = None):
        """ Create all registered commands as application commands at Discord. """

        for cmd in self.commands:
            client.create_command(cmd, guild=guild)

    def _verify_request(self):
        signature = request.headers.get("X-Signature-Ed25519")
        timestamp = request.headers.get("X-Signature-Timestamp")

        if signature is None or timestamp is None:
            return False

        return verify_key(request.data, signature, timestamp, self._public_key)

    def _main(self):
        # Verify request
        if not self._app.config["TESTING"]:
            if not self._verify_request():
                return "Bad request signature", 401

        # Handle interactions
        interaction = Interaction(**request.json)

        if interaction.type == InteractionType.PING:
            return jsonify(InteractionResponse(InteractionResponseType.PONG).to_dict())
        elif interaction.type == InteractionType.APPLICATION_COMMAND:
            cmd = interaction.data.name
            cb = self._commands[cmd].callback

            if cb.__code__.co_argcount > 1:  # if the cb takes more than one argument
                ctx = CommandContext(interaction, self._app_id)
                arg_diff = cb.__code__.co_argcount - (len(interaction.data.options) + 1)
                num_kwargs = len(cb.__defaults__)
                if 1 < num_kwargs > arg_diff > 0:
                    # if not all arguments can be passed by position
                    cb_args = interaction.data.options[:-arg_diff]
                    cb_kwargs = interaction.data.options[-arg_diff:]
                else:
                    cb_args = interaction.data.options
                    cb_kwargs = []
                resp = cb(
                    ctx,
                    *[o.value for o in cb_args],
                    **{o.name: o.value for o in cb_kwargs},
                )
            else:
                cb_data = interaction
                if len(annotations := cb.__annotations__.values()) > 0:
                    cmd_type = next(iter(annotations))
                    if issubclass(cmd_type, ocm.Command):
                        cb_data = cmd_type.wrap(interaction)
                    elif issubclass(cmd_type, CommandContext):
                        cb_data = cmd_type(interaction, self._app_id)

                resp = cb(cb_data)

            if isinstance(resp, InteractionResponse):
                interaction_response = resp
            else:
                # figure out what the response should look like
                with_source = True

                if isinstance(resp, tuple):
                    resp, with_source = resp

                if resp is None:
                    r_data = None
                    if with_source:
                        r_type = InteractionResponseType.ACKNOWLEDGE_WITH_SOURCE
                    else:
                        r_type = InteractionResponseType.ACKNOWLEDGE
                else:
                    r_data = InteractionApplicationCommandCallbackData(str(resp))
                    if with_source:
                        r_type = InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE
                    else:
                        r_type = InteractionResponseType.CHANNEL_MESSAGE

                interaction_response = InteractionResponse(
                    type=r_type,
                    data=r_data,
                )

            g.interaction = interaction
            g.interaction_response = interaction_response

            return jsonify(interaction_response.to_dict())

        else:
            return "Unknown interaction type", 501

    def _after_request(self, response: Response):
        interaction = g.interaction
        interaction_response = g.interaction_response

        cmd = self._commands[interaction.data.name]

        if cmd.after_callback is None:
            return response

        ctx = AfterCommandContext(interaction, interaction_response, self._app_id)

        t = Thread(target=cmd.after_callback, args=(ctx,))
        t.start()

        return response

    def register_command(
        self,
        command: Union[ApplicationCommand, Type[ocm.Command], str],
        callback: _CommandCallback,
    ) -> CommandData:
        """
        Register a callback function for a Discord Slash Command.

        :param command: The command that the callback is registered for
        :param callback: The function that is called when the command is triggered
        :return: An object containing all the command data (e.g. structure, callbacks)
        """

        if isinstance(command, str):
            cmd = CommandData(command, callback)
        elif isinstance(command, ApplicationCommand):
            cmd = CommandData(command.name, callback, command)
        elif issubclass(command, ocm.Command):
            cmd = CommandData(
                command.__cmd_name__, callback, command.to_application_command()
            )
        else:
            raise TypeError(
                "'command' must be 'str', 'ApplicationCommand'"
                + "or subclass of 'ocm.Command'"
            )

        self._commands[cmd.name] = cmd
        return cmd

    def command(
        self, command: _DecoratedCommand = None
    ) -> Union[Callable[[_CommandCallback], CommandData], CommandData]:
        """
        A decorator to register a slash command.
        Calls :meth:`register_command` internally.

        :param command: The command that the decorated function is called on
        """

        _f = None
        if isinstance(command, Callable) and not isinstance(command, type(ocm.Command)):
            _f = command
            command = None

        def decorator(f: _CommandCallback) -> CommandData:
            if command is not None:
                return self.register_command(command, f)
            elif len(annotations := f.__annotations__.values()) > 0:
                _command = next(
                    iter(annotations)
                )  # get :class:`ocm.Command` from type annotation
                return self.register_command(_command, f)
            else:
                return self.register_command(f.__name__.lower().strip("_"), f)

        return decorator(_f) if _f is not None else decorator
