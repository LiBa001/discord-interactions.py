from discord_interactions.flask_ext import Interactions
from discord_interactions import (
    ApplicationCommand,
    ApplicationCommandOption,
    ApplicationCommandOptionType,
    ApplicationCommandOptionChoice,
    Interaction,
    InteractionResponse,
    InteractionResponseType,
    InteractionApplicationCommandCallbackData,
)
from flask import Flask
import os
import random

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

rps_cmd = ApplicationCommand("rps", "Play Rock, Paper, Scissors!", options=[
    ApplicationCommandOption(
        type=ApplicationCommandOptionType.STRING,
        name="symbol",
        description="rock, paper or scissors",
        required=True,
        choices=[
            ApplicationCommandOptionChoice("ROCK", "rock"),
            ApplicationCommandOptionChoice("PAPER", "paper"),
            ApplicationCommandOptionChoice("SCISSORS", "scissors"),
        ],
    )
])


@interactions.command(echo_cmd)
def _echo(interaction: Interaction):
    msg = interaction.data.options[0].value  # "message" option content

    return InteractionResponse(
        response_type=InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
        data=InteractionApplicationCommandCallbackData(content=msg),
    )


@interactions.command(rps_cmd)
def rps(interaction: Interaction):
    choice = random.choice([symbol.value for symbol in rps_cmd.options[0].choices])
    user_choice = interaction.data.options[0].value

    if user_choice == choice:
        msg = "It's a draw!"
    elif user_choice == "rock":
        if choice == "rock":
            msg = "You crush me and win!"
        else:
            msg = "You get covered and lose!"
    elif user_choice == "paper":
        if choice == "rock":
            msg = "You cover me and win!"
        else:
            msg = "You get cut and lose!"
    else:
        if choice == "rock":
            msg = "You get crushed and lose!"
        else:
            msg = "You cut me and win!"

    return f"I took {choice}. {msg}"


if __name__ == "__main__":
    app.run("0.0.0.0", 80)
