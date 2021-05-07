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
from .models import User, Member, Role, Channel
from .application_command import ApplicationCommandOptionType
from typing import Union, Optional


class InteractionType(Enum):
    PING = 1
    APPLICATION_COMMAND = 2


class ApplicationCommandInteractionDataResolved:
    def __init__(self, **kwargs):
        self.users = {u_id: User(**u) for u_id, u in kwargs.get("users", {}).items()}
        self.members = {
            m_id: Member(**m) for m_id, m in kwargs.get("members", {}).items()
        }
        self.roles = {r_id: Role(**r) for r_id, r in kwargs.get("roles", {}).items()}
        self.channels = {
            c_id: Channel(**c) for c_id, c in kwargs.get("channels", {}).items()
        }


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
        self.type = ApplicationCommandOptionType(kwargs["type"])
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
        self.resolved = ApplicationCommandInteractionDataResolved(
            **kwargs.get("resolved", {})
        )
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
        self.application_id = int(kwargs["application_id"])
        self.type = InteractionType(kwargs["type"])

        if self.type == InteractionType.PING:
            return

        self.data = INTERACTION_TYPE_MAP[self.type](**kwargs.get("data", {}))
        self.guild_id = int(kwargs.get("guild_id", 0)) or None
        self.channel_id = int(kwargs.get("channel_id", 0)) or None
        self.member = Member(**kwargs["member"]) if "member" in kwargs else None
        self.user = User(**kwargs["user"]) if "user" in kwargs else None
        self.token = kwargs["token"]
        self.version = int(kwargs["version"])

    @classmethod
    def from_json(cls, data: Union[dict, str]) -> "Interaction":
        """
        Creates an instance of this class from the JSON data that is received on a
        Discord interaction.

        https://discord.com/developers/docs/interactions/slash-commands#interaction

        :param data: Received JSON
        :return: Instance of :class:`Interaction`
        """
        if isinstance(data, str):
            data = json.loads(data)

        return cls(**data)

    @property
    def author(self) -> Union[Member, User]:
        return self.member or self.user

    def get_user(self, user_id: int) -> Optional[User]:
        return self.data.resolved.users.get(user_id)

    def get_member(self, member_id: int) -> Optional[Member]:
        return self.data.resolved.members.get(member_id)

    def get_role(self, role_id: int) -> Optional[Role]:
        return self.data.resolved.roles.get(role_id)

    def get_channel(self, channel_id: int) -> Optional[Channel]:
        return self.data.resolved.channels.get(channel_id)
