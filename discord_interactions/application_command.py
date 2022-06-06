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

from dataclasses import dataclass
from enum import Enum

from .models import ChannelType


class ApplicationCommandType(Enum):
    CHAT_INPUT = 1
    USER = 2
    MESSAGE = 3


class ApplicationCommandOptionType(Enum):
    SUB_COMMAND = 1
    SUB_COMMAND_GROUP = 2
    STRING = 3
    INTEGER = 4
    BOOLEAN = 5
    USER = 6
    CHANNEL = 7
    ROLE = 8
    MENTIONABLE = 9
    NUMBER = 10
    ATTACHMENT = 11


@dataclass()
class ApplicationCommandOptionChoice:
    name: str
    value: str | int | float
    name_localizations: dict[str, str] = None

    def to_dict(self):
        data = {"name": self.name, "value": self.value}
        if self.name_localizations:
            data["name_localizations"] = self.name_localizations
        return data


@dataclass()
class ApplicationCommandOption:
    type: ApplicationCommandOptionType
    name: str
    description: str
    name_localizations: dict[str, str] = None
    description_localizations: dict[str, str] = None
    required: bool = False
    choices: list[ApplicationCommandOptionChoice] = None
    options: list["ApplicationCommandOption"] = None
    channel_types: list[ChannelType] = None
    min_value: int | float = None
    max_value: int | float = None
    autocomplete: bool = False

    @classmethod
    def from_dict(cls, data) -> "ApplicationCommandOption":
        option_type = ApplicationCommandOptionType(data.pop("type"))
        data["choices"] = [
            ApplicationCommandOptionChoice(**choice)
            for choice in data.get("choices", [])
        ] or None
        data["options"] = [
            cls.from_dict(option) for option in data.get("options", [])
        ] or None
        return cls(type=option_type, **data)

    def to_dict(self) -> dict:
        data = {
            "type": self.type.value,
            "name": self.name,
            "description": self.description,
            "default": self.default,
            "required": self.required,
        }

        if self.choices:
            data["choices"] = [choice.to_dict() for choice in self.choices]
        if self.options:
            data["options"] = [option.to_dict() for option in self.options]

        return data


class ApplicationCommand:
    def __init__(
        self,
        name: str,
        description: str = None,
        cmd_type: ApplicationCommandType = ApplicationCommandType.CHAT_INPUT,
        options: list[ApplicationCommandOption] = None,
        default_permission: bool = True,
        **kwargs
    ):
        self.id = int(kwargs.get("id", 0)) or None
        self.type = cmd_type
        self.application_id = int(kwargs.get("application_id", 0)) or None
        self.guild_id = int(kwargs.get("guild_id", 0)) or None
        self.name = name
        self.name_localizations = kwargs.get("name_localizations", {})
        self.description = description
        self.description_localizations = kwargs.get("description_localizations", {})
        self.default_permission = default_permission
        self.version = int(kwargs.get("version", 0)) or None

        # type CHAT_INPUT only
        self.options = options

    def add_option(self, option: ApplicationCommandOption):
        if self.options is None:
            self.options = [option]
        else:
            self.options.append(option)

    @classmethod
    def from_dict(cls, data) -> "ApplicationCommand":
        data["options"] = [
            ApplicationCommandOption.from_dict(option)
            for option in data.get("options", [])
        ] or None
        return cls(**data)

    def to_dict(self) -> dict:
        data = {"name": self.name, "type": self.type.value}

        if self.name_localizations:
            data["name_localizations"] = self.name_localizations
        if self.description:
            data["description"] = self.description
        if self.description_localizations:
            data["description_localizations"] = self.description_localizations
        if self.id:
            data["id"] = self.id
            data["application_id"] = self.application_id
        if self.options:
            data["options"] = [option.to_dict() for option in self.options]
        if not self.default_permission:  # omit when set to true
            data["default_permission"] = self.default_permission

        return data
