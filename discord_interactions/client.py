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

from aiohttp import ClientSession
from typing import Type, TYPE_CHECKING

from .application_command import ApplicationCommand as Cmd
from .interaction import Interaction
from .interaction_response import InteractionResponse, FollowupMessage
from .permissions import GuildPermissions, Permissions
from . import ocm, errors

if TYPE_CHECKING:
    from .interaction_response import MessageCallbackData

CmdClass = Type[ocm.Command]

API_BASE_URL = "https://discord.com/api/v10"


class _BaseClient:
    BASE_URL: str

    def __init__(self, app_id: int):
        self._s = None
        self._app_id = app_id

    async def __aenter__(self):
        self._s = ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    def _app_url(self, *path) -> str:
        path = "/".join([str(p).strip("/") for p in path if p is not None])
        return f"{self.BASE_URL}/{self._app_id}/{path}"

    async def _send(self, method: str, url: str, json: dict | list = None) -> dict:
        async with self._s.request(method=method, url=url, json=json) as r:
            if not r.ok:
                raise errors.DiscordException(
                    f"failed with status code {r.status}: {r.reason}: {r.json()}"
                )

            return await r.json()

    async def close(self):
        await self._s.close()

    @property
    def closed(self) -> bool:
        return self._s.closed


class ApplicationClient(_BaseClient):
    BASE_URL = f"{API_BASE_URL}/applications"

    def __init__(self, token: str, app_id: int = None):
        super().__init__(app_id)
        self._token = token

    async def __aenter__(self):
        await super(ApplicationClient, self).__aenter__()
        self._s.headers.update(self._auth_header)
        return self

    async def _app_url(self, *path) -> str:
        if self._app_id is None:
            data = await self._send("GET", f"{API_BASE_URL}/users/@me")
            self._app_id = int(data["id"])
        return super()._app_url(*path)

    @property
    def _auth_header(self) -> dict:
        return {"Authorization": f"Bot {self._token}"}

    @property
    def application_id(self) -> int:
        return self._app_id

    async def _cmd_url(self, cmd_id=None, guild_id=None):
        if guild_id is None:
            return await self._app_url("commands", cmd_id)
        else:
            return await self._app_url("guilds", guild_id, "commands", cmd_id)

    async def get_commands(self, guild: int = None) -> list[Cmd]:
        """Get all global or guild application commands."""

        data = await self._send("GET", await self._cmd_url(guild_id=guild))
        return [Cmd.from_dict(cmd) for cmd in data]

    async def create_command(self, cmd: Cmd | CmdClass, guild: int = None) -> Cmd:
        """Create a global or guild application command."""

        if not isinstance(cmd, Cmd):
            cmd = cmd.to_application_command()

        data = await self._send(
            "POST", await self._cmd_url(guild_id=guild), json=cmd.to_dict()
        )
        return Cmd.from_dict(data)

    async def edit_command(self, cmd: Cmd | CmdClass, guild: int = None) -> Cmd:
        """Edit a global or guild application command."""

        if not isinstance(cmd, Cmd):
            cmd = cmd.to_application_command()

        if cmd.id is None:
            # creating a command with a name that already exist, overwrites the old one
            return await self.create_command(cmd)

        data = await self._send(
            "PATCH", await self._cmd_url(cmd.id, guild), json=cmd.to_dict()
        )
        return Cmd.from_dict(data)

    async def delete_command(self, cmd_id: int, guild: int = None):
        """Delete a global or guild application command."""

        await self._send("DELETE", await self._cmd_url(cmd_id, guild))

    async def bulk_overwrite_commands(
        self, commands: list[Cmd | CmdClass], guild: int = None
    ) -> list[Cmd]:
        """Overwrite all existing global/guild commands."""

        commands_data = []
        for cmd in commands:
            if not isinstance(cmd, Cmd):
                cmd = cmd.to_application_command()
            commands_data.append(cmd.to_dict())

        data = await self._send(
            "PUT", await self._cmd_url(guild_id=guild), json=commands_data
        )

        return [Cmd.from_dict(cmd) for cmd in data]

    async def get_guild_command_permissions(self, guild: int) -> list[GuildPermissions]:
        """Fetch command permissions for all commands for your app in a guild."""

        data = await self._send("GET", f"{await self._cmd_url(guild)}/permissions")

        return [GuildPermissions.from_dict(p) for p in data]

    async def get_command_permissions(
        self, cmd_id: int, guild: int
    ) -> GuildPermissions:
        """
        Fetch command permissions for a specific command for your app in a guild.
        """

        data = await self._send(
            "GET", f"{await self._cmd_url(cmd_id, guild)}/permissions"
        )

        return GuildPermissions.from_dict(data)

    async def edit_command_permissions(
        self, cmd_id: int, guild: int, perms: Permissions
    ):
        """
        Edit command permissions for a specific command for your app in a guild.
        """

        await self._send(
            "PUT",
            f"{await self._cmd_url(cmd_id, guild)}/permissions",
            json=perms.to_dict(),
        )


class InteractionClient(_BaseClient):
    BASE_URL = f"{API_BASE_URL}/webhooks"

    def __init__(self, interaction: Interaction):
        super().__init__(interaction.application_id)

        self._interaction = interaction

    def _url(self, *path):
        return self._app_url(self._interaction.token, *path)

    async def create_response(self, resp: InteractionResponse):
        """Create a response to an interaction received via the gateway."""

        url = "{0}/interactions/{1.id}/{1.token}/callback".format(
            API_BASE_URL,
            self._interaction,
        )

        await self._send("POST", url, json=resp.to_dict())

    async def edit_response(self, data: MessageCallbackData):
        """Edit the initial Interaction response."""

        await self._send("PATCH", self._url("messages/@original"), json=data.to_dict())

    async def delete_response(self):
        """Delete the initial Interaction response."""

        await self._send("DELETE", self._url("messages/@original"))

    async def create_message(self, msg: FollowupMessage):  # TODO: return message
        """Create a followup message for an Interaction."""

        await self._send("POST", self._url(), json=msg.to_dict())

    async def edit_message(self, msg_id: int, msg: FollowupMessage):
        """Edit a followup message for an Interaction."""

        await self._send("PATCH", self._url("messages", msg_id), json=msg.to_dict())

    async def delete_message(self, msg_id: int):
        """Delete a followup message for an Interaction."""

        await self._send("DELETE", self._url("messages", msg_id))
