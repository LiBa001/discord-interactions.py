#!/usr/bin/env python

"""
MIT License

Original work Copyright (c) 2015-2020 Rapptz
Modified work Copyright (c) 2020-2021 Linus Bartsch

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

from typing import List
from datetime import datetime
from enum import Enum


class UserFlags(Enum):
    staff = 1
    partner = 2
    hypesquad = 4
    bug_hunter = 8
    mfa_sms = 16
    premium_promo_dismissed = 32
    hypesquad_bravery = 64
    hypesquad_brilliance = 128
    hypesquad_balance = 256
    early_supporter = 512
    team_user = 1024
    system = 4096
    has_unread_urgent_messages = 8192
    bug_hunter_level_2 = 16384
    verified_bot = 65536
    verified_bot_developer = 131072


class PremiumType(Enum):
    nitro_classic = 1
    nitro = 2


class User:
    def __init__(self, **data):
        self.id = int(data["id"])
        self.username = data["username"]
        self.discriminator = data["discriminator"]
        self.avatar = data.get("avatar")
        self.bot = data.get("bot")
        self.system = data.get("system")
        self.mfa_enabled = data.get("mfa_enabled")
        self.locale = data.get("locale")
        self.verified = data.get("verified")
        self.email = data.get("email")
        self.flags = self._parse_flags(int(data.get("flags", 0)))
        self.premium_type = None

        if (premium_type := data.get("premium_type")) is not None:
            self.premium_type = PremiumType(premium_type)

        self.public_flags = self._parse_flags(int(data.get("public_flags", 0)))

    @staticmethod
    def _parse_flags(flags: int) -> List[UserFlags]:
        return [flag for flag in UserFlags if flags & flag.value != 0]

    @staticmethod
    def _flags_to_int(flags: List[UserFlags]) -> int:
        return sum(map(lambda flag: flag.value, flags))

    def to_dict(self) -> dict:
        data = {
            "id": str(self.id),
            "username": self.username,
            "discriminator": self.discriminator,
        }

        if self.avatar:
            data["avatar"] = self.avatar
        if self.bot:
            data["bot"] = self.bot
        if self.system:
            data["system"] = self.system
        if self.mfa_enabled:
            data["mfa_enabled"] = self.mfa_enabled
        if self.locale:
            data["locale"] = self.locale
        if self.verified:
            data["verified"] = self.verified
        if self.email:
            data["email"] = self.email
        if self.flags:
            data["flags"] = self._flags_to_int(self.flags)
        if self.premium_type:
            data["premium_type"] = self.premium_type.value
        if self.public_flags:
            data["public_flags"] = self._flags_to_int(self.public_flags)

        return data


class Member:
    def __init__(self, **data):
        self.user = None
        if user_data := data.get("user"):
            self.user = User(**user_data)

        self.nick = data["nick"]
        self.roles = data["roles"]
        self.joined_at = datetime.fromisoformat(data["joined_at"])
        self.premium_since = None

        if premium_since := data.get("premium_since"):
            self.premium_since = datetime.fromisoformat(premium_since)

        self.deaf = data["deaf"]
        self.mute = data["mute"]
        self.pending = data.get("pending", False)

    def to_dict(self) -> dict:
        data = {
            "nick": self.nick,
            "roles": self.roles,
            "joined_at": self.joined_at.isoformat(),
            "deaf": self.deaf,
            "mute": self.mute,
        }

        if self.user:
            data["user"] = self.user.to_dict()
        if self.premium_since:
            data["premium_since"] = self.premium_since.isoformat()
        if self.pending:
            data["pending"] = self.pending

        return data
