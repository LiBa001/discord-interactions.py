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

from dataclasses import dataclass
from enum import Enum


class PermissionType(Enum):
    ROLE = 1
    USER = 2


@dataclass()
class Permissions:
    """ Allow to enable or disable commands for specific users or roles in a guild. """

    id: int  # id of the role or user
    type: PermissionType
    permission: bool

    @classmethod
    def from_dict(cls, data: dict) -> "Permissions":
        return cls(int(data["id"]), PermissionType(data["type"]), data["permission"])

    def to_dict(self):
        return {"id": self.id, "type": self.type.value, "permission": self.permission}


@dataclass()
class GuildPermissions:
    """ Returned when fetching the permissions for a command in a guild. """

    id: int  # id of the command
    application_id: int
    guild_id: int
    permissions: Permissions

    @classmethod
    def from_dict(cls, data: dict) -> "GuildPermissions":
        return cls(
            int(data["id"]),
            int(data["application_id"]),
            int(data["guild_id"]),
            Permissions.from_dict(data["permissions"]),
        )
