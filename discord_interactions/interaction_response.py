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

from enum import Enum
from typing import List, Protocol
from dataclasses import dataclass


class DictConvertible(Protocol):
    """
    Represents a generic dictionary convertible object type
    that can be implemented elsewhere.
    E.g. discord.py's `discord.Embed` or `discord.AllowedMentions` implements this.
    """

    def to_dict(self) -> dict:
        ...


class InteractionResponseType(Enum):
    PONG = 1
    CHANNEL_MESSAGE = 4
    DEFERRED_CHANNEL_MESSAGE = 5


class ResponseFlags(Enum):
    EPHEMERAL = 64


@dataclass()
class InteractionApplicationCommandCallbackData:
    """
    The data that is sent in an :class:`InteractionResponse`.
    """

    content: str = None
    tts: bool = False
    embeds: List[DictConvertible] = None
    allowed_mentions: DictConvertible = None
    flags: List[ResponseFlags] = None

    @staticmethod
    def _flags_to_int(flags: List[ResponseFlags]) -> int:
        return sum(map(lambda flag: flag.value, flags))

    def to_dict(self) -> dict:
        data = {}

        if self.content:
            data["content"] = str(self.content)
        if self.tts:
            data["tts"] = self.tts
        if self.embeds:
            data["embeds"] = [embed.to_dict() for embed in self.embeds]
        if self.allowed_mentions:
            data["allowed_mentions"] = self.allowed_mentions.to_dict()
        if self.flags:
            data["flags"] = self._flags_to_int(self.flags)

        return data


@dataclass()
class InteractionResponse:
    """
    Represents a basic response to a received :class:`Interaction`.
    """

    type: InteractionResponseType
    data: InteractionApplicationCommandCallbackData = None

    def to_dict(self) -> dict:
        response = {"type": self.type.value}

        if self.data:
            response["data"] = self.data.to_dict()

        return response


@dataclass()
class FollowupMessage:
    """
    Represents a message that can be sent after the initial :class:`InteractionResponse`
    """

    content: str = None
    username: str = None
    avatar_url: str = None
    tts: bool = False
    embeds: List[DictConvertible] = None
    allowed_mentions: DictConvertible = None

    def to_dict(self) -> dict:
        data = {k: v for k, v in self.__dict__.items() if v}

        if self.content:
            data["content"] = str(self.content)
        if self.embeds:
            data["embeds"] = [embed.to_dict() for embed in self.embeds]
        if self.allowed_mentions:
            data["allowed_mentions"] = self.allowed_mentions.to_dict()

        return data
