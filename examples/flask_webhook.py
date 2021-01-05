from discord_interactions.flask_ext import Interactions
from discord_interactions import (
    ApplicationCommand,
    ApplicationCommandOption,
    ApplicationCommandOptionType,
    Interaction,
    InteractionResponse,
    InteractionResponseType,
    InteractionApplicationCommandCallbackData,
)
from flask import Flask
import os

app = Flask(__name__)
interactions = Interactions(app, os.getenv("CLIENT_PUBLIC_KEY"))

echo_cmd = ApplicationCommand("echo", "what goes around comes around")
echo_cmd.add_option(
    ApplicationCommandOption(
        type=ApplicationCommandOptionType.STRING,
        name="message",
        description="This will be echoed.",
        required=True,
    )
)


@interactions.command(echo_cmd)
def _echo(interaction: Interaction):
    msg = interaction.data.options[0].value  # "message" option content

    return InteractionResponse(
        response_type=InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
        data=InteractionApplicationCommandCallbackData(content=msg),
    )


if __name__ == "__main__":
    app.run("0.0.0.0", 80)
