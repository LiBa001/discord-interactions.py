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

from discord_interactions import ApplicationCommandType
from abc import ABC, abstractmethod
from typing import Type

from .command import Command


class _CommandProxy(ABC):
    @classmethod
    @abstractmethod
    def create(cls, name: str, **kwargs) -> Type[Command]:
        """Create an individualized command subclass."""

        if "proxy_target" in kwargs:
            # add an additional proxy property for user or message command targets
            # e.g. `cmd.user` instead of `cmd.target` for user commands
            proxy_dict = {kwargs.pop("proxy_target"): Command.target}
        else:
            proxy_dict = {}

        return type(name, (Command,), proxy_dict, name=name, **kwargs)


class UserCommand(_CommandProxy):
    """A proxy class for simplified creation of user commands."""

    @classmethod
    def create(cls, name: str, **kwargs) -> Type[Command]:
        return super().create(
            name, cmd_type=ApplicationCommandType.USER, proxy_target="user"
        )


class MessageCommand(_CommandProxy):
    """A proxy class for simplified creation of message commands."""

    @classmethod
    def create(cls, name: str, **kwargs) -> Type[Command]:
        return super().create(
            name, cmd_type=ApplicationCommandType.MESSAGE, proxy_target="message"
        )
