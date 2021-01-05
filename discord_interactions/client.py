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

from requests import Session, Request, Response, exceptions
from typing import List, Union, Type

from .application_command import ApplicationCommand as Cmd
from .interaction import Interaction
from .interaction_response import (
    InteractionResponse,
    InteractionApplicationCommandCallbackData,
    FollowupMessage,
)
from . import ocm

CmdClass = Type[ocm.Command]

API_BASE_URL = "https://discord.com/api/v8"


class _BaseClient:
    BASE_URL: str

    def __init__(self, app_id: int):
        self._s = Session()
        self._app_id = app_id

    def _app_url(self, *path) -> str:
        path = "/".join([str(p).strip("/") for p in path if p is not None])
        return f"{self.BASE_URL}/{self._app_id}/{path}"

    def _send(self, req: Request) -> Response:
        r = self._s.send(self._s.prepare_request(req))

        if not r.ok:
            raise exceptions.HTTPError(
                f"failed with status code {r.status_code}: {r.reason}: {r.json()}",
                response=r,
            )

        return r


class ApplicationClient(_BaseClient):
    BASE_URL = f"{API_BASE_URL}/applications"

    def __init__(self, token: str, app_id: int = None):
        super().__init__(app_id)
        self._token = token

        self._s.headers.update(self._auth_header)

        if app_id is None:
            r = self._send(Request("GET", f"{API_BASE_URL}/users/@me"))
            self._app_id = int(r.json()["id"])

    @property
    def _auth_header(self) -> dict:
        return {"Authorization": f"Bot {self._token}"}

    @property
    def application_id(self) -> int:
        return self._app_id

    def _cmd_url(self, cmd_id=None, guild_id=None):
        if guild_id is None:
            return self._app_url("commands", cmd_id)
        else:
            return self._app_url("guilds", guild_id, "commands", cmd_id)

    def get_commands(self, guild: int = None) -> List[Cmd]:
        """ Get all global or guild application commands. """

        r = self._send(Request("GET", self._cmd_url(guild_id=guild)))

        return [Cmd.from_dict(cmd) for cmd in r.json()]

    def create_command(self, cmd: Union[Cmd, CmdClass], guild: int = None) -> Cmd:
        """ Create a global or guild application command. """

        if not isinstance(cmd, Cmd):
            cmd = cmd.to_application_command()

        r = self._send(
            Request("POST", self._cmd_url(guild_id=guild), json=cmd.to_dict())
        )

        return Cmd.from_dict(r.json())

    def edit_command(self, cmd: Union[Cmd, CmdClass], guild: int = None) -> Cmd:
        """ Edit a global or guild application command. """

        if not isinstance(cmd, Cmd):
            cmd = cmd.to_application_command()

        if cmd.id is None:
            # creating a command with a name that already exist, overwrites the old one
            return self.create_command(cmd)

        r = self._send(
            Request("PATCH", self._cmd_url(cmd.id, guild), json=cmd.to_dict())
        )

        return Cmd.from_dict(r.json())

    def delete_command(self, cmd_id: int, guild: int = None):
        """ Delete a global or guild application command. """

        self._send(Request("DELETE", self._cmd_url(cmd_id, guild)))


class InteractionClient(_BaseClient):
    BASE_URL = f"{API_BASE_URL}/webhooks"

    def __init__(self, app_id: int, interaction: Interaction):
        super().__init__(app_id)

        self._interaction = interaction

    def _url(self, *path):
        return self._app_url(self._interaction.token, *path)

    def create_response(self, resp: InteractionResponse):
        """ Create a response to an interaction from the gateway. """

        url = "{0}/interactions/{1.id}/{1.token}/callback".format(
            API_BASE_URL,
            self._interaction,
        )

        self._send(Request("POST", url, json=resp.to_dict()))

    def edit_response(self, data: InteractionApplicationCommandCallbackData):
        """ Edit the initial Interaction response. """

        self._send(
            Request("PATCH", self._url("messages/@original"), json=data.to_dict())
        )

    def delete_response(self):
        """ Delete the initial Interaction response. """

        self._send(Request("DELETE", self._url("messages/@original")))

    def create_message(self, msg: FollowupMessage):
        """ Create a followup message for an Interaction. """

        self._send(Request("POST", self._url(), json=msg.to_dict()))

    def edit_message(self, msg_id: int, msg: FollowupMessage):
        """ Edit a followup message for an Interaction. """

        self._send(Request("PATCH", self._url("messages", msg_id), json=msg.to_dict()))

    def delete_message(self, msg_id: int):
        """ Delete a followup message for an Interaction. """

        self._send(Request("DELETE", self._url("messages", msg_id)))
