"""
Copyright Linus Bartsch, 2020

Licensed under: MIT License
"""


import json
from enum import Enum
from .member import Member
from typing import Union


class InteractionType(Enum):
    PING = 1
    APPLICATION_COMMAND = 2


class ApplicationCommandInteractionDataOption:
    def __init__(self, **kwargs):
        self.name = kwargs["name"]
        self.value = kwargs.get("value")
        self.options = [ApplicationCommandInteractionDataOption(**option) for option in kwargs.get("options", [])]


class ApplicationCommandInteractionData:
    def __init__(self, **kwargs):
        self.id = int(kwargs["id"])
        self.name = kwargs["name"]
        self.options = [ApplicationCommandInteractionDataOption(**option) for option in kwargs.get("options", [])]


INTERACTION_TYPE_MAP = {
    InteractionType.PING: type(None),
    InteractionType.APPLICATION_COMMAND: ApplicationCommandInteractionData
}


class Interaction:
    """
    This represents the base interaction type that gets invoked for Slash Commands and future interaction types.
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
