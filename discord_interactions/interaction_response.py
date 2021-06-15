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

from enum import Enum, Flag
from typing import List, Protocol, Optional
from dataclasses import dataclass
from .message_component import Component


class DictConvertible(Protocol):
    """
    Represents a generic dictionary convertible object type
    that can be implemented elsewhere.
    E.g. discord.py's `discord.Embed` or `discord.AllowedMentions` implements this.
    """

    def to_dict(self) -> dict:
        ...


class InteractionCallbackType(Enum):
    PONG = 1
    CHANNEL_MESSAGE = 4
    DEFERRED_CHANNEL_MESSAGE = 5
    DEFERRED_UPDATE_MESSAGE = 6
    UPDATE_MESSAGE = 7


class ResponseFlags(Flag):
    NONE = 0
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
    flags: ResponseFlags = ResponseFlags.NONE
    components: List[Component] = None

    def to_dict(self) -> dict:
        data = {}

        if self.content is not None:
            data["content"] = str(self.content)
        if self.tts:
            data["tts"] = self.tts
        if self.embeds is not None:
            data["embeds"] = [embed.to_dict() for embed in self.embeds]
        if self.allowed_mentions:
            data["allowed_mentions"] = self.allowed_mentions.to_dict()
        if self.flags:
            data["flags"] = self.flags.value
        if self.components is not None:
            data["components"] = [c.to_dict() for c in self.components]

        return data


@dataclass()
class InteractionResponse:
    """
    Represents a basic response to a received :class:`Interaction`.
    """

    type: InteractionCallbackType
    data: InteractionApplicationCommandCallbackData = None

    def to_dict(self) -> dict:
        response = {"type": self.type.value}

        if self.data:
            response["data"] = self.data.to_dict()

        return response


class Response(InteractionResponse):
    """
    An utility class to create simplified interaction responses to application commands.
    Useful for responding with an embed.

    Creates an :class:`InteractionResponse` of type
    `InteractionResponseType.CHANNEL_MESSAGE` internally.

    :type content: Optional[str]
    :param content: The response message content

    :type embed: Optional[:class:`DictConvertible`] (e.g. discord.py's `discord.Embed`)
    :param embed: The response message embed

    :type ephemeral: bool
    :param ephemeral: Whether or not the response should be ephemeral (default: `False`)
    """

    _TYPE = InteractionCallbackType.CHANNEL_MESSAGE

    def __init__(
        self,
        content: Optional[str] = None,
        embed: Optional[DictConvertible] = None,
        ephemeral: bool = False,
        **kwargs
    ):
        kwargs.setdefault("flags", ResponseFlags.NONE)
        if ephemeral:
            kwargs["flags"] |= ResponseFlags.EPHEMERAL

        super().__init__(
            type=self._TYPE,
            data=InteractionApplicationCommandCallbackData(
                content=content, embeds=[embed] if embed else [], **kwargs
            ),
        )


class ComponentResponse(Response):
    _TYPE = InteractionCallbackType.UPDATE_MESSAGE


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
