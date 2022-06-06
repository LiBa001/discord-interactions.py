#!/usr/bin/env python

"""
MIT License

Copyright (c) 2020-2022 Linus Bartsch

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
    MessageCallbackData,
    ApplicationCommand,
    ApplicationClient,
)
from typing import Callable, Coroutine, get_type_hints, cast
from types import FunctionType
import logging
import importlib
import sys
import types
from abc import ABC, abstractmethod
import inspect

from .context import (
    AfterCommandContext,
    CommandContext,
    ElementContext,
    AfterComponentContext,
    ComponentContext,
    ModalContext,
)
from .command import (
    SubCommandData,
    CommandData,
    _CommandCallbackReturnType,
    _DecoratedCommand,
    _CommandCallback,
    command as command_decorator,
)
from .element import ElementData, ElementType, _ElementCallback
from . import errors


logger = logging.getLogger("discord_interactions")


def _is_submodule(parent, child):
    return parent == child or child.startswith(parent + ".")


class BaseExtension(ABC):
    def __init__(self, public_key: str, app_id: int = None):
        self._public_key = public_key
        self._app_id = app_id

        self._commands: dict[str, CommandData] = {}
        self._components: dict[str, ElementData] = {}
        self._modals: dict[str, ElementData] = {}

        self.__extensions = {}

        self._error_callback = None

    @property
    def commands(self) -> list[ApplicationCommand]:
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

    @staticmethod
    def _get_cb_args_kwargs(
            cb: FunctionType, options: list[ApplicationCommandInteractionDataOption]
    ) -> tuple[list, dict]:
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

        annotations = get_type_hints(cb)

        zipped_args = zip(cb.__code__.co_varnames[1:len(cb_args) + 1], cb_args)

        def convert(name, value):
            return t(value) if (t := annotations.get(name)) else value

        cb_args = [convert(name, value) for name, value in zipped_args]
        cb_kwargs = {o.name: convert(o.name, o.value) for o in cb_kwargs}
        return cb_args, cb_kwargs

    @classmethod
    async def _handle_subcommand(
            cls,
            ctx: CommandContext,
            subcmd: ApplicationCommandInteractionDataOption,
            data: SubCommandData,
    ) -> _CommandCallbackReturnType:
        """Handle calling registered callbacks corresponding to invoked subcommands"""

        cb = cast(FunctionType, data.callback)
        arg_count = cb.__code__.co_argcount

        logger.debug(f"handling subcommand {data.name}")

        kwargs = {}
        if arg_count == 0:
            args = ()
        elif arg_count == 1:
            args = (ctx,)
        else:
            args, kwargs = cls._get_cb_args_kwargs(cb, subcmd.options)
            args = (ctx, *args)

        try:
            resp = cb(*args, **kwargs)
            if inspect.iscoroutinefunction(cb):
                resp = await resp
        except Exception as e:
            if data.error_callback:
                resp = data.error_callback(e)
            else:
                raise e

        # check for nested subcommand
        if resp is None and len(subcmd.options) == 1:
            option = subcmd.options[0]
            if option.is_sub_command:
                # nested subcommand is being called -> figure out how to handle it
                sub_cmd_data = data.subcommands.get(option.name)
                if sub_cmd_data is None:
                    # nested subcommand is not registered -> try to call fallback
                    if data.fallback_callback is not None:
                        try:
                            resp = data.fallback_callback(ctx)
                            if inspect.iscoroutinefunction(data.fallback_callback):
                                resp = await resp
                        except Exception as e:
                            if data.error_callback:
                                resp = data.error_callback(e)
                            else:
                                raise e
                else:
                    # nested subcommand is registered -> handle it regularly
                    try:
                        resp = await cls._handle_subcommand(ctx, option, sub_cmd_data)
                    except Exception as e:
                        if sub_cmd_data.error_callback:
                            resp = sub_cmd_data.error_callback(e)
                        elif data.error_callback:
                            resp = data.error_callback(e)
                        else:
                            raise e

        if isinstance(resp, Coroutine):
            resp = await resp

        return resp

    @staticmethod
    def _build_channel_message(resp) -> InteractionResponse:
        # build the actual interaction response
        if isinstance(resp, InteractionResponse):
            # response is already provided
            return resp

        # figure out what the response should look like
        ephemeral = False

        if isinstance(resp, tuple):
            resp, ephemeral = resp

        if resp is None:
            r_type = InteractionCallbackType.DEFERRED_CHANNEL_MESSAGE
            r_data = None
            if ephemeral:
                r_data = MessageCallbackData(
                    flags=ResponseFlags.EPHEMERAL
                )
        else:
            r_type = InteractionCallbackType.CHANNEL_MESSAGE
            r_data = MessageCallbackData(str(resp))
            if ephemeral:
                r_data.flags = ResponseFlags.EPHEMERAL

        return InteractionResponse(type=r_type, data=r_data)

    async def _handle_application_command_interaction(self, interaction: Interaction) -> InteractionResponse | None:
        # handle an application command (slash command)
        logger.debug("incoming application command interaction")
        cmd_name = interaction.data.name
        cmd_data = self._commands[cmd_name]
        cb = cast(FunctionType, cmd_data.callback)
        ctx = CommandContext(self, interaction)

        match cb.__code__.co_argcount:
            case 0:
                args, kwargs = (), {}
            case 1:
                args, kwargs = (ctx,), {}
            case _:
                args, kwargs = self._get_cb_args_kwargs(cb, interaction.data.options)
                args = (ctx, *args)

        try:
            resp = cb(*args, **kwargs)
            if inspect.iscoroutinefunction(cb):
                resp = await resp
        except Exception as e:
            if cmd_data.error_callback:
                resp = cmd_data.error_callback(ctx, e)
            elif self._error_callback:
                resp = self._error_callback(ctx, e)
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
                    try:
                        resp = await self._handle_subcommand(ctx, option, sub_cmd_data)
                    except Exception as e:
                        if cmd_data.error_callback:
                            resp = cmd_data.error_callback(ctx, e)
                        elif self._error_callback:
                            resp = self._error_callback(ctx, e)
                        else:
                            raise e

        if isinstance(resp, Coroutine):
            resp = await resp

        return self._build_channel_message(resp)

    async def _handle_ui_element_interaction(self, ctx: ElementContext, elements_data: dict):
        prefix, *custom_args = ctx.custom_id.split(":")

        component_data = elements_data[prefix]

        cb = cast(FunctionType, component_data.callback)
        arg_count = cb.__code__.co_argcount

        match arg_count:
            case 0:
                args = ()
            case 1:
                args = (ctx,)
            case _:
                annotations = get_type_hints(cb)
                zipped_args = zip(cb.__code__.co_varnames[1:arg_count], custom_args)
                # convert (cast) args to annotated types
                custom_args = [
                    annotations.get(name, str)(value) for name, value in zipped_args
                ]
                args = (ctx, *custom_args)

        try:
            resp = cb(*args)  # call the callback
            if inspect.iscoroutinefunction(cb):
                resp = await resp
        except Exception as e:
            if component_data.error_callback:
                resp = component_data.error_callback(e)
            elif self._error_callback:
                resp = self._error_callback(e)
            else:
                raise e

        if isinstance(resp, Coroutine):
            resp = await resp

        return resp

    async def _handle_message_component_interaction(self, interaction: Interaction) -> InteractionResponse | None:
        # a message component has been interacted with (e.g. button clicked)
        logger.debug("incoming message component interaction")
        ctx = ComponentContext(self, interaction)

        resp = await self._handle_ui_element_interaction(ctx, self._components)

        if isinstance(resp, InteractionResponse):
            interaction_response = resp
        elif resp is None:
            interaction_response = InteractionResponse(
                InteractionCallbackType.DEFERRED_UPDATE_MESSAGE
            )
        else:
            r_data = MessageCallbackData(content=resp)

            interaction_response = InteractionResponse(
                InteractionCallbackType.UPDATE_MESSAGE, r_data
            )

        return interaction_response

    async def _handle_modal_interaction(self, interaction: Interaction) -> InteractionResponse | None:
        # a modal has been submitted
        logger.debug("incoming modal interaction")
        ctx = ModalContext(self, interaction)

        resp = await self._handle_ui_element_interaction(ctx, self._modals)

        return self._build_channel_message(resp)

    async def _handle_interaction(
        self, interaction: Interaction
    ) -> InteractionResponse | None:
        match interaction.type:
            case InteractionType.PING:
                # handle a ping
                logger.debug("incoming ping interaction")
                return InteractionResponse(InteractionCallbackType.PONG)
            case InteractionType.APPLICATION_COMMAND:
                return await self._handle_application_command_interaction(interaction)
            case InteractionType.MESSAGE_COMPONENT:
                return await self._handle_message_component_interaction(interaction)
            case InteractionType.APPLICATION_COMMAND_AUTOCOMPLETE:
                logger.error("autocomplete is not yet supported")  # TODO: implement
                return None
            case InteractionType.MODAL_SUBMIT:
                return await self._handle_modal_interaction(interaction)
            case _:
                return None

    @abstractmethod
    def _main(self, *args, **kwargs):
        resp = self._handle_interaction(...)

    def _get_after_request_data(
        self, interaction: Interaction, interaction_response: InteractionResponse
    ) -> tuple[CommandData | ElementData | None, CommandContext | None]:
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
    ) -> Callable[[_CommandCallback], CommandData] | CommandData:
        """
        A decorator to register a slash command.
        Calls :meth:`register_command` internally.

        :param command: The command that the decorated function is called on
        """

        _f = None
        if isinstance(command, FunctionType):
            _f = command
            command = None

        dec = command_decorator(command)

        def decorator(f):
            return self.register_command(dec(f))

        return decorator(_f) if _f is not None else decorator

    def register_element(self, element_data: ElementData) -> ElementData:
        """
        Register data for a Discord UI element, such as a message component or a modal.

        :param element_data:
            An object containing all the element data (e.g. custom_id, callbacks)
        :return: element data
        """

        match element_data.element_type:
            case ElementType.MESSAGE_COMPONENT:
                self._components[element_data.custom_id] = element_data
            case ElementType.MODAL:
                self._modals[element_data.custom_id] = element_data

        return element_data

    def component(
        self, component_id: str
    ) -> Callable[[_ElementCallback], ElementData]:
        """
        A decorator to register a message component.
        Calls :meth:`register_element` internally.

        :param component_id: The custom id specified when creating the component.
        """

        def decorator(f: _ElementCallback) -> ElementData:
            return self.register_element(ElementData.create_from(ElementType.MESSAGE_COMPONENT, component_id, f))

        return decorator

    def modal(
        self, modal_id: str
    ) -> Callable[[_ElementCallback], ElementData]:
        """
        A decorator to register a modal.
        Calls :meth:`register_element` internally.

        :param modal_id: The custom id specified when creating the modal.
        """

        def decorator(f: _ElementCallback) -> ElementData:
            return self.register_element(ElementData.create_from(ElementType.MODAL, modal_id, f))

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
