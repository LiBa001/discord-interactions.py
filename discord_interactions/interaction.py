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

import json
from enum import Enum
from .member import Member
from typing import Union


class InteractionType(Enum):
    PING = 1
    APPLICATION_COMMAND = 2


class _OptionGetter:
    options: list

    def get_option(
        self, option_name: str
    ) -> Union["ApplicationCommandInteractionDataOption", None]:
        """ Get option by name. """

        for option in self.options:
            if option.name == option_name:
                return option
        return None


class ApplicationCommandInteractionDataOption(_OptionGetter):
    def __init__(self, **kwargs):
        self.name = kwargs["name"]
        self.value = kwargs.get("value")
        self.options = [
            ApplicationCommandInteractionDataOption(**option)
            for option in kwargs.get("options", [])
        ]

    def __str__(self):
        return str(self.value)

    def __int__(self):
        return int(self.value)


class ApplicationCommandInteractionData(_OptionGetter):
    def __init__(self, **kwargs):
        self.id = int(kwargs["id"])
        self.name = kwargs["name"]
        self.options = [
            ApplicationCommandInteractionDataOption(**option)
            for option in kwargs.get("options", [])
        ]


INTERACTION_TYPE_MAP = {
    InteractionType.PING: type(None),
    InteractionType.APPLICATION_COMMAND: ApplicationCommandInteractionData,
}


class Interaction:
    """
    This represents the base interaction type that gets invoked for Slash Commands
    and future interaction types.
    """

    def __init__(self, **kwargs):
        self.id = int(kwargs["id"])
        self.type = InteractionType(kwargs["type"])

        if self.type == InteractionType.PING:
            return

        self.data = INTERACTION_TYPE_MAP[self.type](**kwargs.get("data", {}))
        self.guild_id = int(kwargs["guild_id"])
        self.channel_id = int(kwargs["channel_id"])
        self.member = Member(**kwargs["member"])
        self.token = kwargs["token"]
        self.version = int(kwargs["version"])

    @classmethod
    def from_json(cls, data: Union[dict, str]) -> "Interaction":
        if isinstance(data, str):
            data = json.loads(data)

        return cls(**data)
