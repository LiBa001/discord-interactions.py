from flask import Flask
import os
from discord_interactions.flask_ext import Interactions, ComponentContext
from discord_interactions import (
    Button,
    ButtonStyle,
    ActionRow,
    InteractionResponse,
    InteractionCallbackType,
    InteractionApplicationCommandCallbackData,
)

app = Flask(__name__)
interactions = Interactions(app, os.getenv("CLIENT_PUBLIC_KEY"))


@interactions.command
def hello_components():
    btn = Button("my_button", style=ButtonStyle.PRIMARY, label="Click me!")

    return InteractionResponse(
        InteractionCallbackType.CHANNEL_MESSAGE,
        data=InteractionApplicationCommandCallbackData(
            content="This is a button.", components=[ActionRow(components=[btn])]
        ),
    )


@interactions.component("my_button")
def button_handler(_: ComponentContext):
    return "you clicked the button"
