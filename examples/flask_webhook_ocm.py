from discord_flask import Interactions
from discord_interaction import InteractionResponse, InteractionResponseType, InteractionApplicationCommandCallbackData
from discord_command import ApplicationCommandOptionType
from discord_command.ocm import Command, Option
from flask import Flask
import os

app = Flask(__name__)
interactions = Interactions(app, os.getenv("CLIENT_PUBLIC_KEY"))


class _Echo(Command):
    __cmd_name__ = "echo"
    __cmd_description__ = "what goes around comes around"

    message = Option(ApplicationCommandOptionType.STRING, "message", "This will be echoed.", required=True)


@interactions.command()
def _echo(cmd: _Echo):
    msg = cmd.message

    return InteractionResponse(
        response_type=InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
        data=InteractionApplicationCommandCallbackData(content=msg)
    )


if __name__ == "__main__":
    app.run("0.0.0.0", 80)
