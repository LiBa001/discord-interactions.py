from discord_interactions.flask_ext import Interactions
from discord_interactions import (
    ApplicationCommand,
    ApplicationCommandOption,
    ApplicationCommandOptionType,
    ApplicationCommandOptionChoice,
    Interaction,
)
from flask import Flask
import os
import random
import time

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

rps_cmd = ApplicationCommand(
    "rps",
    "Play Rock, Paper, Scissors!",
    [
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
    ],
)


# Note that only a name is provided here,
# so for this command only the callback gets registered.
# This cannot be used to register the slash command at Discord.
@interactions.command("ping")
def ping(_: Interaction):
    return "pong"


@interactions.command(echo_cmd)
def echo(interaction: Interaction):
    msg = interaction.data.options[0].value  # "message" option content

    return msg, False


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


@interactions.command("delay")
def delay(_: Interaction):
    return None


@delay.after_command
def after_delay(ctx):
    delay_time = ctx.interaction.data.options[0].value
    time.sleep(delay_time)
    ctx.send(f"{delay_time} seconds have passed")


if __name__ == "__main__":
    app.run("0.0.0.0", 80)
