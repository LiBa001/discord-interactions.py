from flask import Flask
import os
from discord_interactions.flask_ext import (
    Interactions,
    ComponentContext,
    AfterComponentContext,
)
from discord_interactions import (
    Button,
    ButtonStyle,
    ActionRow,
    Response,
)

app = Flask(__name__)
interactions = Interactions(app, os.getenv("CLIENT_PUBLIC_KEY"))


@interactions.command
def hello_components():
    btn = Button("my_button", style=ButtonStyle.PRIMARY, label="Click me!")

    return Response("This is a button.", components=[ActionRow(components=[btn])])


@interactions.component("my_button")
def button_handler(ctx: ComponentContext):
    return f"{ctx.interaction.user.username} clicked the button"


@button_handler.after_component
def _after_button_handler(ctx: AfterComponentContext):
    ctx.send(
        f"this is a followup message to {ctx.interaction.user.username}'s button click"
    )
