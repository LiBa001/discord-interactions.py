from discord import UserFlags, PremiumType
from typing import List
from datetime import datetime


class User:
    def __init__(self, **data):
        self.id = data["id"]
        self.username = data["username"]
        self.discriminator = data["discriminator"]
        self.avatar = data.get("avatar")
        self.bot = data.get("bot")
        self.system = data.get("system")
        self.mfa_enabled = data.get("mfa_enabled")
        self.locale = data.get("locale")
        self.verified = data.get("verified")
        self.email = data.get("email")
        self.flags = self._parse_user_flags(int(data.get("flags")))
        self.premium_type = None

        if (premium_type := data.get("premium_type")) is not None:
            self.premium_type = PremiumType(premium_type)

        self.public_flags = self._parse_user_flags(int(data.get("public_flags")))

    @staticmethod
    def _parse_user_flags(flags: int) -> List[UserFlags]:
        return [flag for flag in UserFlags if flags & flag.value != 0]


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
        self.pending = data.get("pending")
