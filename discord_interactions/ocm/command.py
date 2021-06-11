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

from discord_interactions import (
    Interaction,
    Member,
    User,
    Channel,
    Role,
    ApplicationCommandInteractionDataOption,
    ApplicationCommandInteractionDataResolved,
    ApplicationCommand,
    ApplicationCommandOption,
    ApplicationCommandOptionType,
    ApplicationCommandOptionChoice,
)
from typing import List, Union, Type, Any
from dataclasses import dataclass
from enum import Enum
import inspect


class OptionChoices(Enum):
    @classmethod
    def to_application_command_option_choices(
        cls,
    ) -> List[ApplicationCommandOptionChoice]:
        choices = []

        for choice in cls:
            choices.append(ApplicationCommandOptionChoice(choice.name, choice.value))

        return choices


class OptionContainer:
    """
    Superclass for classes that can have attributes of type :class:`Option`,
    i.e. :class:`Command` and :class:`Option` itself or more specific
    :class:`SubCommand` and :class:`SubCommandGroup`.
    """

    def get_options(self):
        return {
            attr.name: attr
            for _, attr in inspect.getmembers(self, lambda a: isinstance(a, Option))
        }


class _Option(OptionContainer):
    pass


class OptionContainerType(type):
    def __new__(mcs, name, bases, attributes):
        cls = super(OptionContainerType, mcs).__new__(mcs, name, bases, attributes)

        for attr_name, attr in attributes.items():
            if isinstance(attr, _Option):
                # set option name to attribute name where not explicitly set
                if attr.name is None:
                    attr.name = attr_name.strip("_")

                # set option type based on type annotations where not explicitly set
                if attr.type is None:
                    attr.type = (
                        ApplicationCommandOptionType.STRING
                    )  # use string as default option type
                    if cls.__annotations__:
                        _type = cls.__annotations__.get(attr_name)
                        if isinstance(_type, ApplicationCommandOptionType):
                            attr.type = _type
                        elif _type == int:
                            attr.type = ApplicationCommandOptionType.INTEGER
                        elif _type == bool:
                            attr.type = ApplicationCommandOptionType.BOOLEAN
                        elif _type == User or _type == Member:
                            attr.type = ApplicationCommandOptionType.USER
                        elif _type == Channel:
                            attr.type = ApplicationCommandOptionType.CHANNEL
                        elif _type == Role:
                            attr.type = ApplicationCommandOptionType.ROLE
                        elif issubclass(_type, OptionChoices):
                            attr.choices = _type
                            _type = type(next(iter(_type)).value)
                            if _type == int:
                                attr.type = ApplicationCommandOptionType.INTEGER

                        attr.__type = _type

        return cls


@dataclass()
class Option(_Option, metaclass=OptionContainerType):
    description: str
    type: ApplicationCommandOptionType = None
    name: str = None
    default: bool = False
    required: bool = False
    choices: Union[Type[OptionChoices], dict] = None
    __data: ApplicationCommandInteractionDataOption = None
    __resolved: ApplicationCommandInteractionDataResolved = None
    __type: Any = None

    @property
    def is_sub_command(self):
        return self.type in (
            ApplicationCommandOptionType.SUB_COMMAND,
            ApplicationCommandOptionType.SUB_COMMAND_GROUP,
        )

    def __get__(self, instance: Union["Command", "Option"], owner):
        """ Return what data this option actually received. """

        if not self.is_sub_command:
            data = (
                getattr(instance, "_Command__interaction").data
                if not issubclass(owner, Option)
                else instance.__data
            )

            if (option := data.get_option(self.name)) is not None:
                value = option.value
                choices = self.choices
                if isinstance(choices, type) and issubclass(choices, OptionChoices):
                    return choices(value)
                elif self.__type in (User, Channel, Role):
                    resolved = self.__resolved or data.resolved
                    return getattr(resolved, f"{self.__type.__name__.lower()}s")[value]
                else:
                    return value
            else:
                return None

        else:
            if isinstance(self, owner):
                self.__data = instance.__data.get_option(self.name)
            else:
                interaction_data = getattr(instance, "_Command__interaction").data
                self.__data = interaction_data.get_option(self.name)
                self.__resolved = interaction_data.resolved
            return self

    def __bool__(self):
        return self.__data is not None

    def to_application_command_option(self) -> ApplicationCommandOption:
        options = []
        for option in self.__class__.__dict__.values():
            if not isinstance(option, Option):
                continue
            options.append(option.to_application_command_option())

        if self.choices:
            if isinstance(self.choices, dict):
                choices = [
                    ApplicationCommandOptionChoice(name, value)
                    for name, value in self.choices.items()
                ]
            else:
                choices = self.choices.to_application_command_option_choices()
        else:
            choices = None

        return ApplicationCommandOption(
            type=self.type,
            name=self.name,
            description=self.description,
            default=self.default,
            required=self.required,
            options=options or None,
            choices=choices,
        )


class CommandType(OptionContainerType):
    def __new__(mcs, *args, **kwargs):
        cls = super(CommandType, mcs).__new__(mcs, *args, **kwargs)

        # abort if it's a class in this module
        # (the `Command` class itself and not a subclass)
        if cls.__module__ == __name__:
            return cls

        if cls.__cmd_name__ is None:
            cls.__cmd_name__ = cls.__name__.lower().strip("_")

        if cls.__cmd_description__ is None and cls.__doc__ is not None:
            cls.__cmd_description__ = cls.__doc__.strip()

        return cls


class Command(OptionContainer, metaclass=CommandType):
    """ Represents a Discord Slash Command in the Object-Command-Mapper (OCM). """

    __cmd_name__ = None
    __cmd_description__ = None

    __interaction: Interaction = None

    @classmethod
    def wrap(cls, interaction: Interaction):
        inst = cls()
        inst.__interaction = interaction
        return inst

    @property
    def interaction(self) -> Interaction:
        return self.__interaction

    @property
    def guild_id(self) -> int:
        return self.interaction.guild_id

    @property
    def channel_id(self) -> int:
        return self.interaction.channel_id

    @property
    def author(self) -> Union[Member, User]:
        return self.interaction.author

    @property
    def interaction_id(self) -> int:
        return self.interaction.id

    @property
    def app_id(self) -> int:
        return self.interaction.application_id

    @property
    def command_id(self) -> int:
        return self.interaction.data.id

    @property
    def token(self) -> str:
        return self.interaction.token

    @classmethod
    def to_application_command(cls) -> ApplicationCommand:
        options = []

        for option in cls.__dict__.values():
            if not isinstance(option, Option):
                continue
            options.append(option.to_application_command_option())

        return ApplicationCommand(
            name=cls.__cmd_name__,
            description=cls.__cmd_description__,
            options=options or None,
        )


class SubCommand(Option):
    def __init__(self, **kwargs):
        super().__init__(
            self.__doc__, ApplicationCommandOptionType.SUB_COMMAND, **kwargs
        )


class SubCommandGroup(Option):
    def __init__(self, **kwargs):
        super().__init__(
            self.__doc__, ApplicationCommandOptionType.SUB_COMMAND_GROUP, **kwargs
        )
