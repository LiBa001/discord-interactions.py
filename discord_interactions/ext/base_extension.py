#!/usr/bin/env python

"""
MIT License

Copyright (c) 2020-2021 Linus Bartsch

This file contains (partly modified) contents of https://github.com/Rapptz/discord.py.
Respective Copyright (c) 2015-2020 Rapptz

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

from discord_interactions import (
    Interaction,
    InteractionType,
    ApplicationCommandInteractionDataOption,
    InteractionResponse,
    ResponseFlags,
    InteractionCallbackType,
    InteractionApplicationCommandCallbackData,
    ApplicationCommand,
    ApplicationClient,
)
from discord_interactions import ocm
from typing import Callable, Union, Dict, List, Tuple, Optional, Coroutine
import logging
import importlib
import sys
import types
from abc import ABC, abstractmethod
import inspect

from .context import (
    AfterCommandContext,
    CommandContext,
    AfterComponentContext,
    ComponentContext,
)
from .command import (
    SubCommandData,
    CommandData,
    _CommandCallbackReturnType,
    _DecoratedCommand,
    _CommandCallback,
    command as command_decorator,
)
from .component import ComponentData, _ComponentCallback
from . import errors


logger = logging.getLogger("discord_interactions")


def _is_submodule(parent, child):
    return parent == child or child.startswith(parent + ".")


class BaseExtension(ABC):
    def __init__(self, public_key: str, app_id: int = None):
        self._public_key = public_key
        self._app_id = app_id

        self._commands: Dict[str, CommandData] = {}
        self._components: Dict[str, ComponentData] = {}

        self.__extensions = {}

        self._error_callback = None

    @property
    def commands(self) -> List[ApplicationCommand]:
        """All registered application commands"""

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

    async def _handle_interaction(
        self, interaction: Interaction
    ) -> Optional[InteractionResponse]:
        if interaction.type == InteractionType.PING:
            # handle a ping
            logger.debug("incoming ping interaction")
            return InteractionResponse(InteractionCallbackType.PONG)
        elif interaction.type == InteractionType.APPLICATION_COMMAND:
            # handle an application command (slash command)
            logger.debug("incoming application command interaction")
            cmd_name = interaction.data.name
            cmd_data = self._commands[cmd_name]
            cb = cmd_data.callback
            ctx = CommandContext(self, interaction)
            cmd: Optional[ocm.Command] = None

            if cb.__code__.co_argcount > 1:
                # the cb takes more than one argument; pass them
                args, kwargs = self._get_cb_args_kwargs(cb, interaction.data.options)
                args = (ctx, *args)
            elif cb.__code__.co_argcount == 1:
                # callback takes only one argument; figure out it's type
                cb_data = interaction
                if len(annotations := cb.__annotations__.values()) > 0:
                    cmd_type = next(iter(annotations))
                    if issubclass(cmd_type, ocm.Command):
                        cb_data = cmd = cmd_type.wrap(interaction)
                    elif issubclass(cmd_type, CommandContext):
                        cb_data = ctx = cmd_type(self, interaction)

                args, kwargs = (cb_data,), {}
            else:
                args, kwargs = (), {}

            try:
                resp = cb(*args, **kwargs)
                if inspect.iscoroutinefunction(cb):
                    resp = await resp
            except Exception as e:
                if cmd_data.error_callback:
                    resp = cmd_data.error_callback(e)
                elif self._error_callback:
                    resp = self._error_callback(e)
                else:
                    raise e

            # figure out whether to call subcommands
            if resp is None and len(interaction.data.options) == 1:
                option = interaction.data.options[0]
                if option.is_sub_command:
                    sub_cmd_data = cmd_data.subcommands.get(option.name)
                    if sub_cmd_data is None:
                        # no callback registered for subcommand; try fallback
                        if cmd_data.fallback_callback is not None:
                            resp = cmd_data.fallback_callback(ctx)
                    else:
                        ocm_sub = None
                        if cmd is not None:
                            ocm_sub = cmd.get_options()[option.name]
                        try:
                            resp = await self._handle_subcommand(
                                ctx, option, sub_cmd_data, ocm_sub
                            )
                        except Exception as e:
                            if cmd_data.error_callback:
                                resp = cmd_data.error_callback(e)
                            elif self._error_callback:
                                resp = self._error_callback(e)
                            else:
                                raise e

            if isinstance(resp, Coroutine):
                resp = await resp

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

            return interaction_response

        elif interaction.type == InteractionType.MESSAGE_COMPONENT:
            # a message component has been interacted with (e.g. button clicked)
            logger.debug("incoming message component interaction")
            ctx = ComponentContext(self, interaction)
            prefix, *custom_args = ctx.custom_id.split(":")
            component_data = self._components[prefix]

            cb = component_data.callback
            arg_count = cb.__code__.co_argcount

            if arg_count == 0:
                args = ()
            else:
                if ctx_class := cb.__annotations__.get(cb.__code__.co_varnames[0]):
                    ctx = ctx_class(self, interaction)
                if arg_count == 1:
                    args = (ctx,)
                else:
                    annotations = cb.__annotations__
                    zipped_args = zip(cb.__code__.co_varnames[1:arg_count], custom_args)
                    # convert args to annotated types
                    custom_args = [
                        annotations.get(name, str)(value) for name, value in zipped_args
                    ]
                    args = (ctx, *custom_args)

            try:
                resp = cb(*args)  # call the callback
            except Exception as e:
                if component_data.error_callback:
                    resp = component_data.error_callback(e)
                elif self._error_callback:
                    resp = self._error_callback(e)
                else:
                    raise e

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

            return interaction_response

        else:
            return None

    @abstractmethod
    def _main(self, *args, **kwargs):
        resp = self._handle_interaction(...)

    @staticmethod
    def _get_cb_args_kwargs(
        cb, options: List[ApplicationCommandInteractionDataOption]
    ) -> Tuple[list, dict]:
        # count difference between command options and callback args (without ctx)
        arg_diff = cb.__code__.co_argcount - (len(options) + 1)
        # number of callback keyword args
        num_kwargs = len(cb.__defaults__ or ())
        if 1 < num_kwargs > arg_diff > 0:
            # if not all arguments can be passed by position
            cb_args = options[:-arg_diff]
            cb_kwargs = options[-arg_diff:]
        else:
            cb_args = options
            cb_kwargs = []

        annotations = cb.__annotations__

        zipped_args = zip(cb.__code__.co_varnames[1 : len(cb_args) + 1], cb_args)

        def convert(name, value):
            return t(value) if (t := annotations.get(name)) else value

        cb_args = [convert(name, value) for name, value in zipped_args]
        cb_kwargs = {o.name: convert(o.name, o.value) for o in cb_kwargs}
        return cb_args, cb_kwargs

    @classmethod
    async def _handle_subcommand(
        cls,
        ctx: CommandContext,
        interaction_sub: ApplicationCommandInteractionDataOption,
        data: SubCommandData,
        ocm_sub: Optional[ocm.Option] = None,
    ) -> _CommandCallbackReturnType:
        """Handle calling registered callbacks corresponding to invoked subcommands"""

        cb = data.callback
        arg_count = cb.__code__.co_argcount

        logger.debug(f"handling subcommand {data.name}")

        cb_data = None
        pass_option_as_arg = False
        if len(annotations := cb.__annotations__) > 0 and arg_count <= 2:
            cb_data_arg_name = cb.__code__.co_varnames[arg_count - 1]
            cmd_type = annotations.get(cb_data_arg_name)
            if issubclass(cmd_type, ocm.Option):
                if ocm_sub is None:
                    ocm_sub = cmd_type(name=interaction_sub.name)
                    ocm_sub._Option__data = interaction_sub
                cb_data = ocm_sub
            elif issubclass(cmd_type, CommandContext):
                cb_data = ctx
            elif issubclass(cmd_type, ApplicationCommandInteractionDataOption):
                cb_data = cmd_type(
                    name=interaction_sub.name,
                    type=interaction_sub.type,
                    value=interaction_sub.value,
                )
                cb_data.options = interaction_sub.options
            elif cmd_type is not None and arg_count == 2:
                # pass cmd option as individual argument when it has an annotation;
                # else it will default to 'ApplicationCommandInteractionDataOption'
                pass_option_as_arg = True
        elif arg_count == 2:
            cb_data = interaction_sub

        kwargs = {}
        if arg_count == 0:
            args = ()
        elif arg_count == 1:
            # for one arg pass ctx by default, only something else if annotated
            args = cb_data or ctx
        elif pass_option_as_arg or arg_count > 2:
            args, kwargs = cls._get_cb_args_kwargs(cb, interaction_sub.options)
            args = (ctx, *args)
        else:
            args = (ctx, cb_data)

        try:
            resp = cb(*args, **kwargs)
        except Exception as e:
            if data.error_callback:
                resp = data.error_callback(e)
            else:
                raise e

        if resp is None and len(interaction_sub.options) == 1:
            option = interaction_sub.options[0]
            if option.is_sub_command:
                sub_cmd_data = data.subcommands.get(option.name)
                if sub_cmd_data is None:
                    # try to call fallback if subcommand callback is not registered
                    if data.fallback_callback is not None:
                        try:
                            resp = data.fallback_callback(ctx)
                        except Exception as e:
                            if data.error_callback:
                                resp = data.error_callback(e)
                            else:
                                raise e
                else:
                    if ocm_sub is not None:
                        ocm_sub = ocm_sub.get_options()[option.name]
                    try:
                        resp = cls._handle_subcommand(
                            ctx, option, sub_cmd_data, ocm_sub
                        )
                    except Exception as e:
                        if sub_cmd_data.error_callback:
                            resp = sub_cmd_data.error_callback(e)
                        elif data.error_callback:
                            resp = data.error_callback(e)
                        else:
                            raise e

        return resp

    def _get_after_request_data(
        self, interaction: Interaction, interaction_response: InteractionResponse
    ) -> Tuple[Union[CommandData, ComponentData, None], Optional[CommandContext]]:
        if interaction.type == InteractionType.APPLICATION_COMMAND:
            target = self._commands[interaction.data.name]
            ctx = AfterCommandContext(self, interaction, interaction_response)
        elif interaction.type == InteractionType.MESSAGE_COMPONENT:
            target = self._components[interaction.data.custom_id.split(":")[0]]
            ctx = AfterComponentContext(self, interaction, interaction_response)
        else:
            return None, None

        return target, ctx

    @abstractmethod
    def _after_request(self, *args, **kwargs):
        target, ctx = self._get_after_request_data(..., ...)
        if target.after_callback:
            target.after_callback(ctx)

    def register_command(self, command_data: CommandData) -> CommandData:
        """
        Register data for a Discord Slash Command.

        :param command_data:
            An object containing all the command data (e.g. structure, callbacks)
        :return: command data
        """

        self._commands[command_data.name] = command_data
        return command_data

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

        dec = command_decorator(command)

        def decorator(f):
            return self.register_command(dec(f))

        return decorator(_f) if _f is not None else decorator

    def register_component(self, component_data: ComponentData) -> ComponentData:
        """
        Register data for a Discord Message Component.

        :param component_data:
            An object containing all the component data (e.g. custom_id, callbacks)
        :return: component data
        """

        self._components[component_data.custom_id] = component_data
        return component_data

    def component(
        self, component_id: str
    ) -> Callable[[_ComponentCallback], ComponentData]:
        """
        A decorator to register a message component.
        Calls :meth:`register_component` internally.

        :param component_id: The custom id specified when creating the component.
        """

        def decorator(f: _ComponentCallback) -> ComponentData:
            return self.register_component(ComponentData.create_from(component_id, f))

        return decorator

    def on_error(self, f: Callable[[Exception], _CommandCallbackReturnType]):
        """
        A decorator to set the top-level error callback function.
        The provided function will be called when an exception is raised in any other
        user defined callback that is not already handled by another error handler.

        :param f: The error callback function.
        """

        self._error_callback = f

    # extensions

    def _remove_module_references(self, name):
        pass

    def _call_module_finalizers(self, lib, key):
        try:
            func = getattr(lib, "teardown")
        except AttributeError:
            pass
        else:
            try:
                func(self)
            except Exception:
                pass
        finally:
            self.__extensions.pop(key, None)
            sys.modules.pop(key, None)
            name = lib.__name__
            for module in list(sys.modules.keys()):
                if _is_submodule(name, module):
                    del sys.modules[module]

    def _load_from_module_spec(self, spec, key):
        # precondition: key not in self.__extensions
        lib = importlib.util.module_from_spec(spec)
        sys.modules[key] = lib
        try:
            spec.loader.exec_module(lib)
        except Exception as e:
            del sys.modules[key]
            raise errors.ExtensionFailed(key, e) from e

        try:
            setup = getattr(lib, "setup")
        except AttributeError:
            del sys.modules[key]
            raise errors.NoEntryPointError(key)

        try:
            setup(self)
        except Exception as e:
            del sys.modules[key]
            self._remove_module_references(lib.__name__)
            self._call_module_finalizers(lib, key)
            raise errors.ExtensionFailed(key, e) from e
        else:
            self.__extensions[key] = lib

    def load_extension(self, name):
        """Loads an extension.
        An extension is a python module that contains commands, cogs, or
        listeners.
        An extension must have a global function, ``setup`` defined as
        the entry point on what to do when the extension is loaded. This entry
        point must have a single argument, the ``bot``.
        Parameters
        ------------
        name: :class:`str`
            The extension name to load. It must be dot separated like
            regular Python imports if accessing a sub-module. e.g.
            ``foo.test`` if you want to import ``foo/test.py``.
        Raises
        --------
        ExtensionNotFound
            The extension could not be imported.
        ExtensionAlreadyLoaded
            The extension is already loaded.
        NoEntryPointError
            The extension does not have a setup function.
        ExtensionFailed
            The extension or its setup function had an execution error.
        """

        if name in self.__extensions:
            raise errors.ExtensionAlreadyLoaded(name)

        spec = importlib.util.find_spec(name)
        if spec is None:
            raise errors.ExtensionNotFound(name)

        self._load_from_module_spec(spec, name)

    def unload_extension(self, name):
        """Unloads an extension.
        When the extension is unloaded, all commands, listeners, and cogs are
        removed from the bot and the module is un-imported.
        The extension can provide an optional global function, ``teardown``,
        to do miscellaneous clean-up if necessary. This function takes a single
        parameter, the ``bot``, similar to ``setup`` from
        :meth:`~.Bot.load_extension`.
        Parameters
        ------------
        name: :class:`str`
            The extension name to unload. It must be dot separated like
            regular Python imports if accessing a sub-module. e.g.
            ``foo.test`` if you want to import ``foo/test.py``.
        Raises
        -------
        ExtensionNotLoaded
            The extension was not loaded.
        """

        lib = self.__extensions.get(name)
        if lib is None:
            raise errors.ExtensionNotLoaded(name)

        self._remove_module_references(lib.__name__)
        self._call_module_finalizers(lib, name)

    def reload_extension(self, name):
        """Atomically reloads an extension.
        This replaces the extension with the same extension, only refreshed. This is
        equivalent to a :meth:`unload_extension` followed by a :meth:`load_extension`
        except done in an atomic way. That is, if an operation fails mid-reload then
        the bot will roll-back to the prior working state.
        Parameters
        ------------
        name: :class:`str`
            The extension name to reload. It must be dot separated like
            regular Python imports if accessing a sub-module. e.g.
            ``foo.test`` if you want to import ``foo/test.py``.
        Raises
        -------
        ExtensionNotLoaded
            The extension was not loaded.
        ExtensionNotFound
            The extension could not be imported.
        NoEntryPointError
            The extension does not have a setup function.
        ExtensionFailed
            The extension setup function had an execution error.
        """

        lib = self.__extensions.get(name)
        if lib is None:
            raise errors.ExtensionNotLoaded(name)

        # get the previous module states from sys modules
        modules = {
            name: module
            for name, module in sys.modules.items()
            if _is_submodule(lib.__name__, name)
        }

        try:
            # Unload and then load the module...
            self._remove_module_references(lib.__name__)
            self._call_module_finalizers(lib, name)
            self.load_extension(name)
        except Exception as e:
            # if the load failed, the remnants should have been
            # cleaned from the load_extension function call
            # so let's load it from our old compiled library.
            lib.setup(self)
            self.__extensions[name] = lib

            # revert sys.modules back to normal and raise back to caller
            sys.modules.update(modules)
            raise

    @property
    def extensions(self):
        """
        Mapping[:class:`str`, :class:`py:types.ModuleType`]:
        A read-only mapping of extension name to extension.
        """

        return types.MappingProxyType(self.__extensions)
