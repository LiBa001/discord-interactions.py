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

from __future__ import annotations
from typing import TYPE_CHECKING
from discord_interactions import (
    InteractionClient,
    Interaction,
    InteractionCallbackData,
    InteractionResponse,
    FollowupMessage,
    Component,
)

if TYPE_CHECKING:
    from .base_extension import BaseExtension

# TODO: add docstrings


class CommandContext:
    def __init__(self, ext: BaseExtension, interaction: Interaction):
        self._interaction = interaction
        self._ext = ext

    @property
    def interaction(self) -> Interaction:
        return self._interaction

    @property
    def app_id(self) -> int:
        return self._interaction.application_id

    @property
    def ext(self):
        return self._ext


class AfterCommandContext(CommandContext):
    def __init__(
        self,
        ext: BaseExtension,
        interaction: Interaction,
        response: InteractionResponse,
    ):
        super(AfterCommandContext, self).__init__(ext, interaction)

        self._response = response
        self._client = InteractionClient(self.interaction)

    @property
    def response(self) -> InteractionResponse:
        return self._response

    @property
    def client(self) -> InteractionClient:
        return self._client

    def edit_original(self, content: str, **options):
        data = InteractionCallbackData(content, **options)

        self.client.edit_response(data)

    def send(self, msg: str, tts: bool = False):
        followup_msg = FollowupMessage(content=msg, tts=tts)

        self.client.create_message(followup_msg)


class ElementContext(CommandContext):
    @property
    def custom_id(self):
        return self._interaction.data.custom_id


class ComponentContext(ElementContext):
    @property
    def message(self):
        return self._interaction.message

    @property
    def component_type(self):
        return self._interaction.data.component_type

    @property
    def values(self) -> list | None:
        """Gets selected values if component is a select menu."""
        return self._interaction.data.values


class ModalContext(ElementContext):
    @property
    def components(self):
        return self._interaction.data.components

    def get_input(self, custom_id: str) -> Component:
        for c in self.components:
            if c.custom_id == custom_id:
                return c


class AfterComponentContext(AfterCommandContext, ComponentContext):
    pass
