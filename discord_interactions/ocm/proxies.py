from discord_interactions import ApplicationCommandType
from abc import ABC, abstractmethod

from .command import Command


class _CommandProxy(ABC):
    @classmethod
    @abstractmethod
    def create(cls, name, **kwargs):
        """Create an individualized command subclass."""

        if "proxy_target" in kwargs:
            # add an additional proxy property for user or message command targets
            # e.g. `cmd.user` instead of `cmd.target` for user commands
            proxy_dict = {kwargs.pop("proxy_target"): Command.target}
        else:
            proxy_dict = {}

        return type(name, (Command,), proxy_dict, name=name, **kwargs)


class UserCommand(_CommandProxy):
    """A proxy class for simplified creation of user commands."""

    @classmethod
    def create(cls, name, **kwargs):
        return super().create(
            name, cmd_type=ApplicationCommandType.USER, proxy_target="user"
        )


class MessageCommand(_CommandProxy):
    """A proxy class for simplified creation of message commands."""

    @classmethod
    def create(cls, name, **kwargs):
        return super().create(
            name, cmd_type=ApplicationCommandType.MESSAGE, proxy_target="message"
        )
