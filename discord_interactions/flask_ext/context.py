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
    InteractionClient,
    Interaction,
    InteractionApplicationCommandCallbackData,
    InteractionResponse,
    FollowupMessage,
)


class CommandContext:
    def __init__(self, interaction: Interaction):
        self._interaction = interaction

    @property
    def interaction(self) -> Interaction:
        return self._interaction

    @property
    def app_id(self) -> int:
        return self._interaction.application_id


class AfterCommandContext(CommandContext):
    def __init__(self, interaction: Interaction, response: InteractionResponse):
        super(AfterCommandContext, self).__init__(interaction)

        self._response = response
        self._client = InteractionClient(self.interaction)

    @property
    def response(self) -> InteractionResponse:
        return self._response

    @property
    def client(self) -> InteractionClient:
        return self._client

    def edit_original(self, content: str, **options):
        data = InteractionApplicationCommandCallbackData(content, **options)

        self.client.edit_response(data)

    def send(self, msg: str, tts: bool = False):
        followup_msg = FollowupMessage(content=msg, tts=tts)

        self.client.create_message(followup_msg)
