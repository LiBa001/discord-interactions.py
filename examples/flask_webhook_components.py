from flask import Flask
import os
from discord_interactions.ext.flask import Interactions
from discord_interactions.ext import ComponentContext, AfterComponentContext
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
    btn = Button("my_button", label="Click me!")

    return Response("This is a button.", components=[ActionRow(btn)])


@interactions.component("my_button")
def button_handler(ctx: ComponentContext):
    return f"{ctx.interaction.user.username} clicked the button"


@button_handler.after_component
def _after_button_handler(ctx: AfterComponentContext):
    ctx.send(
        f"this is a followup message to {ctx.interaction.user.username}'s button click"
    )


@interactions.command
def delete_resource(_, resource_id: int):
    btn = Button(
        f"confirm_deletion:{resource_id}", style=ButtonStyle.DANGER, label="DELETE"
    )

    return Response("This is irreversible! Are you sure?", components=[ActionRow(btn)])


@interactions.component("confirm_deletion")
def confirm_deletion(_, resource_id: int):
    ...  # do actual deletion

    return f"successfully deleted resource {resource_id}"
