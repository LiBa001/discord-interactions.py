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

from typing import List, Optional, Union
from datetime import datetime
from enum import Enum
from dataclasses import dataclass


class UserFlag(Enum):
    """
    Represents a flag of a Discord :class:`User`.

    See
    https://discord.com/developers/docs/resources/user#user-object-user-flags
    for reference.
    """

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
    """
    Represents the premium type of a Discord :class:`User`.

    See
    https://discord.com/developers/docs/resources/user#user-object-premium-types
    for reference.
    """

    nitro_classic = 1
    nitro = 2


class User:
    """
    Represents a Discord user.

    See https://discord.com/developers/docs/resources/user#user-object
    for reference.
    """

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

    def __int__(self) -> int:
        return self.id

    def __str__(self) -> str:
        return f"{self.username}#{self.discriminator}"

    @property
    def mention(self) -> str:
        return f"<@{self.id}>"

    @staticmethod
    def _parse_flags(flags: int) -> List[UserFlag]:
        return [flag for flag in UserFlag if flags & flag.value != 0]

    @staticmethod
    def _flags_to_int(flags: List[UserFlag]) -> int:
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
    """
    Represents a Discord guild member.

    See https://discord.com/developers/docs/resources/guild#guild-member-object
    for reference.
    """

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

        self.deaf = data.get("deaf")
        self.mute = data.get("mute")
        self.pending = data.get("pending", False)

    def __str__(self) -> str:
        return self.display_name or ""

    @property
    def id(self) -> Optional[int]:
        return self.user.id if self.user else None

    @property
    def username(self) -> Optional[str]:
        return self.user.username if self.user else None

    @property
    def display_name(self) -> Optional[str]:
        return self.nick or self.username

    def to_dict(self) -> dict:
        data = {
            "nick": self.nick,
            "roles": self.roles,
            "joined_at": self.joined_at.isoformat(),
        }

        if self.user:
            data["user"] = self.user.to_dict()
        if self.premium_since:
            data["premium_since"] = self.premium_since.isoformat()
        if self.deaf is not None:
            data["deaf"] = self.deaf
        if self.mute is not None:
            data["mute"] = self.mute
        if self.pending:
            data["pending"] = self.pending

        return data


class Role:
    """
    Represents a Discord role.

    See https://discord.com/developers/docs/topics/permissions#role-object
    for reference.
    """

    def __init__(self, **data):
        self.id = int(data["id"])
        self.name = data["name"]
        self.color = data["color"]
        self.hoist = data["hoist"]
        self.position = data["position"]
        self.permissions = data["permissions"]
        self.managed = data["managed"]
        self.mentionable = data["mentionable"]
        self.tags = data.get("tags")


class ChannelType(Enum):
    """
    Represents the type of a Discord :class:`Channel`.

    See
    https://discord.com/developers/docs/resources/channel#channel-object-channel-types
    for reference.
    """

    GUILD_TEXT = 0
    DM = 1
    VOICE = 2
    GROUP_DM = 3
    CATEGORY = 4
    NEWS = 5
    STORE = 6
    NEWS_THREAD = 10
    PUBLIC_THREAD = 11
    PRIVATE_THREAD = 12
    STAGE_VOICE = 13


class VideoQualityMode(Enum):
    """
    Represents the video quality mode of a Discord :class:`Channel`.

    See
    https://discord.com/developers/docs/resources/channel#channel-object-video-quality-modes
    for reference.
    """

    AUTO = 1
    FULL = 2


class Channel:
    """
    Represents a Discord channel.

    See https://discord.com/developers/docs/resources/channel#channel for reference.
    """

    def __init__(self, **data):
        self.id = int(data["id"])
        self.type = ChannelType(data["type"])
        self.guild_id = data.get("guild_id")
        self.position = data.get("position")
        self.permission_overwrites = data.get("permission_overwrites")
        self.name = data.get("name")
        self.topic = data.get("topic")
        self.nsfw = data.get("nsfw")
        self.last_message_id = data.get("last_message_id")
        self.bitrate = data.get("bitrate")
        self.user_limit = data.get("user_limit")
        self.rate_limit_per_user = data.get("rate_limit_per_user")
        self.recipients = data.get("recipients")
        self.icon = data.get("icon")
        self.owner_id = data.get("owner_id")
        self.application_id = data.get("application_id")
        self.parent_id = data.get("parent_id")
        self.last_pin_timestamp = data.get("last_pin_timestamp")
        self.rtc_region = data.get("rtc_region")
        self.video_quality_mode = VideoQualityMode(data.get("video_quality_mode", 1))
        self.message_count = data.get("message_count")
        self.member_count = data.get("member_count")
        self.thread_metadata = data.get("thread_metadata")
        self.member = data.get("member")


class MessageType(Enum):
    """
    Represents the type of a Discord :class:`Message`.

    See
    https://discord.com/developers/docs/resources/channel#message-object-message-types
    for reference.
    """

    DEFAULT = 0
    RECIPIENT_ADD = 1
    RECIPIENT_REMOVE = 2
    CALL = 3
    CHANNEL_NAME_CHANGE = 4
    CHANNEL_ICON_CHANGE = 5
    CHANNEL_PINNED_MESSAGE = 6
    GUILD_MEMBER_JOIN = 7
    USER_PREMIUM_GUILD_SUBSCRIPTION = 8
    USER_PREMIUM_GUILD_SUBSCRIPTION_TIER_1 = 9
    USER_PREMIUM_GUILD_SUBSCRIPTION_TIER_2 = 10
    USER_PREMIUM_GUILD_SUBSCRIPTION_TIER_3 = 11
    CHANNEL_FOLLOW_ADD = 12
    GUILD_DISCOVERY_DISQUALIFIED = 14
    GUILD_DISCOVERY_REQUALIFIED = 15
    GUILD_DISCOVERY_GRACE_PERIOD_INITIAL_WARNING = 16
    GUILD_DISCOVERY_GRACE_PERIOD_FINAL_WARNING = 17
    THREAD_CREATED = 18
    REPLY = 19
    APPLICATION_COMMAND = 20
    THREAD_STARTER_MESSAGE = 21
    GUILD_INVITE_REMINDER = 22


class Message:
    """
    Represents a Discord message.

    See https://discord.com/developers/docs/resources/channel#message-object
    for reference.
    """

    def __init__(self, **data):
        self.id = int(data["id"])
        self.channel_id = int(data["channel_id"])
        self.guild_id = int(data.get("guild_id", 0)) or None
        self.webhook_id = int(data.get("webhook_id", 0)) or None
        self.author = User(**data["author"]) if not self.webhook_id else data["author"]
        self.member = Member(**data["member"]) if "member" in data else None
        self.content = data["content"]
        self.timestamp = datetime.fromisoformat(data["timestamp"])
        self.edited_timestamp = (
            t := data["edited_timestamp"]
        ) and datetime.fromisoformat(t)
        self.tts = data["tts"]
        self.mention_everyone = data["mention_everyone"]
        self.mentions = [User(**u) for u in data["mentions"]]
        self.mention_roles = [int(r_id) for r_id in data["mention_roles"]]
        self.mention_channels = data.get("mention_channels")
        self.attachments = data["attachments"]  # TODO: convert to Attachment object
        self.embeds = data["embeds"]  # TODO: convert to Embed object
        self.reactions = data.get("reactions")
        self.nonce = data.get("nonce")
        self.pinned = data["pinned"]
        self.type = MessageType(data["type"])
        self.activity = data.get("activity")
        self.application = data.get("application")
        self.application_id = (a_id := data.get("application_id")) and int(a_id)
        self.message_reference = data.get("message_reference")
        self.flags = data.get("flags")
        self.stickers = data.get("stickers")
        self.referenced_message = (m := data.get("reference_message")) and Message(**m)
        self.interaction = data.get("interaction")
        self.thread = (c := data.get("thread")) and Channel(**c)
        self.components = data.get("components")  # TODO: convert to component object


@dataclass
class PartialEmoji:
    id: Optional[int] = None
    name: Optional[str] = None
    animated: bool = False

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name, "animated": self.animated}

    @classmethod
    def from_any(cls, emoji: Union[str, "PartialEmoji"]) -> "PartialEmoji":
        """Convert values of any type into a partial emoji dict."""
        if isinstance(emoji, str):
            return cls(name=emoji)
        elif isinstance(emoji, cls):
            return emoji
        else:
            raise TypeError(f"cannot convert '{type(emoji)}' to partial emoji dict")
