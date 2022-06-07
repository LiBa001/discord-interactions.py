#!/usr/bin/env python

"""
MIT License

Copyright (c) 2020-2022 Linus Bartsch

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

from __future__ import annotations

import json
from enum import Enum
from .models import User, Member, Role, Channel, Message, Attachment
from .application_command import ApplicationCommandType, ApplicationCommandOptionType
from .message_component import Component, ComponentType, SelectOption
from typing import TypeAlias


class InteractionType(Enum):
    PING = 1
    APPLICATION_COMMAND = 2
    MESSAGE_COMPONENT = 3
    APPLICATION_COMMAND_AUTOCOMPLETE = 4
    MODAL_SUBMIT = 5


class ApplicationCommandInteractionDataResolved:
    users: dict[int, User]
    members: dict[int, Member]
    roles: dict[int, Role]
    channels: dict[int, Channel]
    messages: dict[int, Message]
    attachments: dict[int, Attachment]

    def __init__(self, **kwargs):
        self.users = {u_id: User(**u) for u_id, u in kwargs.get("users", {}).items()}
        self.members = {
            m_id: Member(**m) for m_id, m in kwargs.get("members", {}).items()
        }
        self.roles = {r_id: Role(**r) for r_id, r in kwargs.get("roles", {}).items()}
        self.channels = {
            c_id: Channel(**c) for c_id, c in kwargs.get("channels", {}).items()
        }
        self.messages = {
            m_id: Message(**m) for m_id, m in kwargs.get("messages", {}).items()
        }
        self.attachments = {
            a_id: Attachment(**a) for a_id, a in kwargs.get("attachments", {}).items()
        }


class _OptionGetter:
    options: list

    def get_option(
        self, option_name: str
    ) -> ApplicationCommandInteractionDataOption | None:
        """Get option by name."""

        for option in self.options:
            if option.name == option_name:
                return option
        return None


class ApplicationCommandInteractionDataOption(_OptionGetter):
    name: str
    type: ApplicationCommandOptionType
    value: str | int | float | None
    options: list[ApplicationCommandInteractionDataOption]
    focused: bool | None

    def __init__(self, **kwargs):
        self.name = kwargs["name"]
        self.type = ApplicationCommandOptionType(kwargs["type"])
        self.value = kwargs.get("value")
        self.options = [
            ApplicationCommandInteractionDataOption(**option)
            for option in kwargs.get("options", [])
        ]
        self.focused = kwargs.get("focused")

    def __str__(self):
        return str(self.value)

    def __int__(self):
        return int(self.value)

    @property
    def is_sub_command(self):
        return self.type in (
            ApplicationCommandOptionType.SUB_COMMAND,
            ApplicationCommandOptionType.SUB_COMMAND_GROUP,
        )


class ApplicationCommandInteractionData(_OptionGetter):
    id: int
    name: str
    type: ApplicationCommandType
    resolved: ApplicationCommandInteractionDataResolved
    options: list[ApplicationCommandInteractionDataOption]
    target_id: int | None  # user and message commands only

    def __init__(self, **kwargs):
        self.id = int(kwargs["id"])
        self.name = kwargs["name"]
        self.type = ApplicationCommandType(kwargs["type"])
        self.resolved = ApplicationCommandInteractionDataResolved(
            **kwargs.get("resolved", {})
        )
        self.options = [
            ApplicationCommandInteractionDataOption(**option)
            for option in kwargs.get("options", [])
        ]
        self.target_id = int(kwargs.get("target_id", 0)) or None


class ComponentInteractionData:
    custom_id: str
    component_type: ComponentType
    values: list[SelectOption] | None

    def __init__(self, **kwargs):
        self.custom_id = kwargs["custom_id"]
        self.component_type = ComponentType(kwargs["component_type"])
        # for select components only
        self.values = [SelectOption(**v) for v in kwargs.get("values", [])] or None


class ModalInteractionData:
    custom_id: str
    components: list[Component]

    def __init__(self, **kwargs):
        self.custom_id = kwargs["custom_id"]
        self.components = [Component(c) for c in kwargs["components"]]


InteractionData: TypeAlias = (
    ApplicationCommandInteractionData | ComponentInteractionData | ModalInteractionData
)

INTERACTION_TYPE_MAP = {
    InteractionType.PING: type(None),
    InteractionType.APPLICATION_COMMAND: ApplicationCommandInteractionData,
    InteractionType.MESSAGE_COMPONENT: ComponentInteractionData,
    InteractionType.APPLICATION_COMMAND_AUTOCOMPLETE: ApplicationCommandInteractionData,
    InteractionType.MODAL_SUBMIT: ModalInteractionData,
}


class Interaction:
    """
    This represents the base interaction type that gets invoked for Slash Commands
    and other interaction types.
    """

    id: int
    application_id: int
    type: InteractionType
    data: InteractionData | None
    guild_id: int | None
    channel_id: int | None
    member: Member | None
    user: User | None
    token: str
    version: int
    message: Message | None
    locale: str | None
    guild_locale: str | None

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
        self.user = User(**kwargs["user"]) if "user" in kwargs else self.member.user
        self.token = kwargs["token"]
        self.version = int(kwargs["version"])
        self.message = (m := kwargs.get("message")) and Message(**m)
        self.locale = kwargs["locale"]
        self.guild_locale = kwargs.get("guild_locale")

    @classmethod
    def from_json(cls, data: dict | str) -> Interaction:
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
    def author(self) -> Member | User:
        return self.member or self.user

    @property
    def is_dm(self) -> bool:
        return self.member is None

    @property
    def target(self) -> User | Message | None:
        """Target of user or message command."""

        return self.find_any_resolved(self.data.target_id)

    def get_user(self, user_id: int) -> User | None:
        return self.data.resolved.users.get(user_id)

    def get_member(self, member_id: int) -> Member | None:
        return self.data.resolved.members.get(member_id)

    def get_role(self, role_id: int) -> Role | None:
        return self.data.resolved.roles.get(role_id)

    def get_channel(self, channel_id: int) -> Channel | None:
        return self.data.resolved.channels.get(channel_id)

    def get_message(self, message_id: int) -> Message | None:
        return self.data.resolved.messages.get(message_id)

    def find_any_resolved(
        self, target_id: int
    ) -> User | Member | Role | Channel | Message | None:
        for target_type in "users", "members", "roles", "channels", "messages":
            if target := getattr(self.data.resolved, target_type).get(target_id):
                return target
