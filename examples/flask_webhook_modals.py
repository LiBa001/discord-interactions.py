from flask import Flask
import os
from discord_interactions.ext.flask import Interactions
from discord_interactions.ext import ModalContext
from discord_interactions import (
    TextInput,
    TextInputStyle,
    ModalResponse,
)


app = Flask(__name__)
interactions = Interactions(app, os.getenv("CLIENT_PUBLIC_KEY"))


@interactions.command
def create_resource():
    return ModalResponse(
        "resource_creation",
        "Create a new resource",
        components=[
            TextInput("title", TextInputStyle.Short, "Title", 5, 200),
            TextInput(
                "description", TextInputStyle.Paragraph, "Description", required=False
            ),
        ],
    )


@interactions.modal("resource_creation")
def resource_creation(ctx: ModalContext):
    print(ctx.components)
    title = ctx.get_input("title").value
    description = ctx.get_input("description").value
    return f"resource created:\n\n**{title}**\n```{description}```"
