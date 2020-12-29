from enum import Enum
from typing import List
from discord import Embed, AllowedMentions


class InteractionResponseType(Enum):
    PONG = 1
    ACKNOWLEDGE = 2
    CHANNEL_MESSAGE = 3
    CHANNEL_MESSAGE_WITH_SOURCE = 4
    ACKNOWLEDGE_WITH_SOURCE = 5


class InteractionApplicationCommandCallbackData:
    def __init__(
            self,
            content: str,
            tts: bool = False,
            embeds: List[Embed] = None,
            allowed_mentions: AllowedMentions = None
    ):
        self.content = content
        self.tts = tts
        self.embeds = embeds
        self.allowed_mentions = allowed_mentions

    def to_dict(self) -> dict:
        data = {
            "content": self.content,
            "tts": self.tts
        }

        if self.embeds:
            data["embeds"] = [embed.to_dict() for embed in self.embeds]
        if self.allowed_mentions:
            data["allowed_mentions"] = self.allowed_mentions.to_dict()

        return data


class InteractionResponse:
    def __init__(self, response_type: InteractionResponseType, data: InteractionApplicationCommandCallbackData = None):
        self.type = response_type
        self.data = data

    def to_dict(self) -> dict:
        response = {"type": self.type.value}

        if self.data:
            response["data"] = self.data.to_dict()

        return response
