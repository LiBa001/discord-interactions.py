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
    InteractionCallbackType,
    ResponseFlags,
    InteractionApplicationCommandCallbackData,
    ApplicationCommandInteractionDataOption,
    verify_key,
    ApplicationCommand,
    ApplicationClient,
)
from discord_interactions import ocm
from typing import Callable, Union, Type, Dict, List, Tuple, Optional, Any
from threading import Thread

from .context import (
    AfterCommandContext,
    CommandContext,
    ComponentContext,
    AfterComponentContext,
)


_CommandCallbackReturnType = Union[
    InteractionResponse, str, None, Tuple[Optional[str], bool]
]
_CommandCallback = Union[
    Callable[[], _CommandCallbackReturnType],
    Callable[
        [Union[Interaction, ocm.Command, ocm.Option, CommandContext]],
        _CommandCallbackReturnType,
    ],
    Callable[[CommandContext, Any], _CommandCallbackReturnType],
]
_AfterCommandCallback = Callable[[AfterCommandContext], None]
_DecoratedCommand = Union[ApplicationCommand, str, _CommandCallback, Type[ocm.Command]]
_ComponentCallback = Callable[[ComponentContext], Union[InteractionResponse, str, None]]
_AfterComponentCallback = Callable[[AfterComponentContext], None]


class SubCommandData:
    """
    Stores and handles registering callbacks for a registered
    subcommand or subcommand group.

    :type name: str
    :param name: Name of the subcommand (group).

    :param cb:
        The function to be called when the subcommand or
        a subcommand in the subcommand group is invoked.
    """

    def __init__(self, name: str, cb: _CommandCallback):
        self.name = name
        self.callback = cb
        self.after_callback = None
        self.fallback_callback = None
        self._subcommands: Dict[str, SubCommandData] = {}

    @property
    def subcommands(self) -> Dict[str, "SubCommandData"]:
        return self._subcommands

    def after_command(self, f: _AfterCommandCallback):
        """
        A decorator to register a function that gets called after a command has run.
        The function will be internally called from within Flask's `after_request`
        function.
        """

        self.after_callback = f

    def register_subcommand(
        self, name: str, callback: _CommandCallback
    ) -> "SubCommandData":
        """
        Register a callback for a subcommand or subcommand group to the parent
        command, subcommand or subcommand group.

        :type name: `str`
        :param name:
            The name of the subcommand or subcommand group.

        :type callback: `callable`
        :param callback:
            The function to register as a callback.

        :rtype: :class:`SubCommandData`
        :return:
            An object that can be used to register further callbacks for the subcommand,
            subcommand group or it's children.
        """

        cmd = SubCommandData(name, callback)
        self._subcommands[name] = cmd
        return cmd

    def subcommand(
        self, name: str = ""
    ) -> Callable[[_CommandCallback], "SubCommandData"]:
        """
        A decorator to register callbacks for subcommands or subcommand groups to the
        parent.
        Calls :meth:`register_subcommand` internally.

        :type name: `str`
        :param name:
            The subcommands name.
            If left empty, the name will be derived from the function name.

        :return: The actual decorator.
        """

        def decorator(f: _CommandCallback):
            return self.register_subcommand(name or f.__name__.lower().strip("_"), f)

        return decorator

    def fallback(self, f: Callable):
        """
        A decorator to register a fallback callback function that will be called for
        all subcommands that don't have their own callback registered
        or if no subcommand was provided at all (this case should never occur).

        :param f: The callback function.
        """

        self.fallback_callback = f


class CommandData(SubCommandData):
    """
    Stores and handles registering callbacks for a registered command.

    :type name: str
    :param name: Name of the command.

    :param cb: The function to be called when the command is invoked.

    :type cmd: Optional[:class:`ApplicationCommand`]
    :param cmd: The object storing structural information for the command.
    """

    def __init__(self, name: str, cb: _CommandCallback, cmd: ApplicationCommand = None):
        super().__init__(name, cb)
        self.application_command = cmd


class ComponentData:
    """
    Stores and handles registering callbacks for a registered message component.

    :type custom_id: str
    :param custom_id: Custom id to identify the component.

    :param cb:
        The function to be called when the component is invoked
        (e.g. button clicked).
    """

    def __init__(self, custom_id: str, cb: _ComponentCallback):
        self.custom_id = custom_id
        self.callback = cb
        self.after_callback = None

    def after_component(self, f: _AfterComponentCallback):
        """
        A decorator to register a function that gets called after a component invocation
        has returned.
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
        app.after_request_funcs.setdefault(None, []).append(self._after_request)

        self._commands: Dict[str, CommandData] = {}
        self._components: Dict[str, ComponentData] = {}

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

    def publish_commands(self, client: ApplicationClient, guild: int = None):
        """
        Create all registered commands as application commands at Discord.

        .. Note::
            This performs a bulk overwrite, which means that currently registered
            commands that are not registered to the :class:`Interactions` object will be
            deleted. If you only want to create specific commands, use
            :meth:`ApplicationClient.create_command`.

        :type client: :class:`ApplicationClient`
        :param client:
            The application client to use for registering the commands at Discord.

        :type guild: int
        :param guild:
            ID of the optional guild to register the commands at.
            Commands will be registered globally if left `None`.
        """

        client.bulk_overwrite_commands(self.commands, guild=guild)

    def _verify_request(self):
        signature = request.headers.get("X-Signature-Ed25519")
        timestamp = request.headers.get("X-Signature-Timestamp")

        if signature is None or timestamp is None:
            return False

        return verify_key(request.data, signature, timestamp, self._public_key)

    def _main(self):
        g.interaction = None
        g.interaction_response = None

        # Verify request
        if not self._app.config["TESTING"]:
            if not self._verify_request():
                return "Bad request signature", 401

        # Handle interactions
        interaction = Interaction(**request.json)

        if interaction.type == InteractionType.PING:
            # handle a ping
            return jsonify(InteractionResponse(InteractionCallbackType.PONG).to_dict())
        elif interaction.type == InteractionType.APPLICATION_COMMAND:
            # handle an application command (slash command)
            cmd_name = interaction.data.name
            cb = self._commands[cmd_name].callback
            ctx = CommandContext(interaction)
            cmd: Optional[ocm.Command] = None

            if cb.__code__.co_argcount > 1:
                # the cb takes more than one argument; pass them
                args, kwargs = self._get_cb_args_kwargs(cb, interaction.data.options)
                resp = cb(ctx, *args, **kwargs)
            elif cb.__code__.co_argcount == 1:
                # callback takes only one argument; figure out it's type
                cb_data = interaction
                if len(annotations := cb.__annotations__.values()) > 0:
                    cmd_type = next(iter(annotations))
                    if issubclass(cmd_type, ocm.Command):
                        cb_data = cmd = cmd_type.wrap(interaction)
                    elif issubclass(cmd_type, CommandContext):
                        cb_data = ctx = cmd_type(interaction)

                resp = cb(cb_data)
            else:
                resp = cb()

            # figure out whether to call subcommands
            if resp is None and len(interaction.data.options) == 1:
                option = interaction.data.options[0]
                if option.is_sub_command:
                    sub_cmd_data = self._commands[cmd_name].subcommands.get(option.name)
                    if sub_cmd_data is None:
                        # no callback registered for subcommand; try fallback
                        if self._commands[cmd_name].fallback_callback is not None:
                            resp = self._commands[cmd_name].fallback_callback(ctx)
                    else:
                        ocm_sub = None
                        if cmd is not None:
                            ocm_sub = cmd.get_options()[option.name]
                        resp = self._handle_subcommand(
                            ctx, option, sub_cmd_data, ocm_sub
                        )

            # build the actual interaction response
            if isinstance(resp, InteractionResponse):
                # response is already provided
                interaction_response = resp
            else:
                # figure out what the response should look like
                ephemeral = False

                if isinstance(resp, tuple):
                    resp, ephemeral = resp

                if resp is None:
                    r_type = InteractionCallbackType.DEFERRED_CHANNEL_MESSAGE
                    r_data = None
                    if ephemeral:
                        r_data = InteractionApplicationCommandCallbackData(
                            flags=ResponseFlags.EPHEMERAL
                        )
                else:
                    r_type = InteractionCallbackType.CHANNEL_MESSAGE
                    r_data = InteractionApplicationCommandCallbackData(str(resp))
                    if ephemeral:
                        r_data.flags = ResponseFlags.EPHEMERAL

                interaction_response = InteractionResponse(
                    type=r_type,
                    data=r_data,
                )

            g.interaction = interaction
            g.interaction_response = interaction_response

            return jsonify(interaction_response.to_dict())

        elif interaction.type == InteractionType.MESSAGE_COMPONENT:
            # a message component has been interacted with (e.g. button clicked)
            ctx = ComponentContext(interaction)
            cb = self._components.get(ctx.custom_id).callback
            resp = cb(ctx)  # call the callback

            if isinstance(resp, InteractionResponse):
                interaction_response = resp
            elif resp is None:
                interaction_response = InteractionResponse(
                    InteractionCallbackType.DEFERRED_UPDATE_MESSAGE
                )
            else:
                r_data = InteractionApplicationCommandCallbackData(content=resp)

                interaction_response = InteractionResponse(
                    InteractionCallbackType.UPDATE_MESSAGE, r_data
                )

            g.interaction = interaction
            g.interaction_response = interaction_response

            return jsonify(interaction_response.to_dict())

        else:
            return "Unknown interaction type", 501

    @staticmethod
    def _get_cb_args_kwargs(
        cb, options: List[ApplicationCommandInteractionDataOption]
    ) -> Tuple[list, dict]:
        arg_diff = cb.__code__.co_argcount - (len(options) + 1)
        num_kwargs = len(cb.__defaults__ or ())
        if 1 < num_kwargs > arg_diff > 0:
            # if not all arguments can be passed by position
            cb_args = options[:-arg_diff]
            cb_kwargs = options[-arg_diff:]
        else:
            cb_args = options
            cb_kwargs = []
        return [o.value for o in cb_args], {o.name: o.value for o in cb_kwargs}

    @classmethod
    def _handle_subcommand(
        cls,
        ctx: CommandContext,
        interaction_sub: ApplicationCommandInteractionDataOption,
        data: SubCommandData,
        ocm_sub: Optional[ocm.Option] = None,
    ) -> _CommandCallbackReturnType:
        """ Handle calling registered callbacks corresponding to invoked subcommands """

        cb = data.callback
        arg_count = cb.__code__.co_argcount

        if arg_count > 2:
            args, kwargs = cls._get_cb_args_kwargs(cb, interaction_sub.options)
            resp = cb(ctx, *args, **kwargs)
        elif arg_count == 2:
            # callback takes only one argument; figure out it's type
            cb_data = interaction_sub
            if len(annotations := cb.__annotations__) > 0:
                cb_data_arg_name = cb.__code__.co_varnames[arg_count - 1]
                cmd_type = annotations[cb_data_arg_name]
                if issubclass(cmd_type, ocm.Option):
                    if ocm_sub is None:
                        ocm_sub = cmd_type(name=interaction_sub.name)
                        ocm_sub._Option__data = interaction_sub
                    cb_data = ocm_sub
            resp = cb(ctx, cb_data)
        elif arg_count == 1:
            resp = cb(ctx)
        else:
            resp = cb()

        if resp is None and len(interaction_sub.options) == 1:
            option = interaction_sub.options[0]
            if option.is_sub_command:
                sub_cmd_data = data.subcommands.get(option.name)
                if sub_cmd_data is None:
                    # try to call fallback if subcommand callback is not registered
                    if data.fallback_callback is not None:
                        resp = data.fallback_callback(ctx)
                else:
                    if ocm_sub is not None:
                        ocm_sub = ocm_sub.get_options()[option.name]
                    resp = cls._handle_subcommand(ctx, option, sub_cmd_data, ocm_sub)

        return resp

    def _after_request(self, response: Response):
        try:
            interaction = g.interaction
            interaction_response = g.interaction_response
        except AttributeError:
            return response

        if interaction is None:
            return response

        if interaction.type == InteractionType.APPLICATION_COMMAND:
            target = self._commands[interaction.data.name]
            ctx = AfterCommandContext(interaction, interaction_response)
        elif interaction.type == InteractionType.MESSAGE_COMPONENT:
            target = self._components[interaction.data.custom_id]
            ctx = AfterComponentContext(interaction, interaction_response)
        else:
            return response

        if target.after_callback is not None:
            t = Thread(target=target.after_callback, args=(ctx,))
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

    def register_component(
        self, component_id: str, callback: Callable
    ) -> ComponentData:
        data = ComponentData(component_id, callback)
        self._components[component_id] = data
        return data

    def component(
        self, component_id: str
    ) -> Callable[[_ComponentCallback], ComponentData]:
        def decorator(f: _ComponentCallback) -> ComponentData:
            return self.register_component(component_id, f)

        return decorator
