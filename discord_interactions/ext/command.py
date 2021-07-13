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

from typing import Callable, Union, Tuple, Optional, Any, Type, Dict, Awaitable

from .. import Interaction, InteractionResponse, ApplicationCommand, ocm
from .context import CommandContext, AfterCommandContext


_CommandCallbackReturnTypeResolved = Union[
    InteractionResponse, str, None, Tuple[Optional[str], bool]
]
_CommandCallbackReturnType = Union[
    Awaitable[_CommandCallbackReturnTypeResolved], _CommandCallbackReturnTypeResolved
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
        self.error_callback = None
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

    def on_error(self, f: Callable[[Exception], _CommandCallbackReturnType]):
        """
        A decorator to set the command-level error callback function.
        The provided function will be called when an exception is raised in any other
        callback of this command
        (or subcommands if not handled by their own error handler).

        :param f: The error callback function.
        """

        self.error_callback = f


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

    @classmethod
    def create_from(
        cls,
        cmd: Union[ApplicationCommand, Type[ocm.Command], str],
        callback: _CommandCallback,
    ) -> "CommandData":
        """
        Create an instance of :class:`CommandData`.

        :param cmd: The command
        :param callback: The function that is called when the command is triggered
        :return: An object containing all the command data (e.g. structure, callbacks)
        """

        if isinstance(cmd, str):
            cmd = cls(cmd, callback)
        elif isinstance(cmd, ApplicationCommand):
            cmd = cls(cmd.name, callback, cmd)
        elif issubclass(cmd, ocm.Command):
            cmd = cls(cmd.__cmd_name__, callback, cmd.to_application_command())
        else:
            raise TypeError(
                "'command' must be 'str', 'ApplicationCommand'"
                + "or subclass of 'ocm.Command'"
            )

        return cmd


def command(
    cmd: _DecoratedCommand = None,
) -> Union[Callable[[_CommandCallback], CommandData], CommandData]:
    """
    A decorator to register a callback on a slash command.

    :param cmd: The command that the decorated function is called on
    """

    _f = None
    if isinstance(cmd, Callable) and not isinstance(cmd, type(ocm.Command)):
        _f = cmd
        cmd = None

    def decorator(f: _CommandCallback) -> CommandData:
        if cmd is not None:
            return CommandData.create_from(cmd, f)
        elif len(annotations := f.__annotations__.values()) == 1:
            _command = next(iter(annotations))  # get 'ocm.Command' from annotation
            if issubclass(_command, ocm.Command):
                return CommandData.create_from(_command, f)

        return CommandData.create_from(f.__name__.lower().strip("_"), f)

    return decorator(_f) if _f is not None else decorator
