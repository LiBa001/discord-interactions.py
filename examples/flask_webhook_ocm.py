from discord_interactions.flask_ext import Interactions
from discord_interactions.ocm import Command, Option, OptionChoices
from flask import Flask
import os
import random

app = Flask(__name__)
interactions = Interactions(app, os.getenv("CLIENT_PUBLIC_KEY"))


class Ping(Command):
    """ simple ping command """


class Echo(Command):
    """ what goes around comes around """

    message: str = Option("This will be echoed.", required=True)


class RPSSymbol(OptionChoices):
    ROCK = "rock"
    PAPER = "paper"
    SCISSORS = "scissors"


class RPS(Command):
    """ Play Rock, Paper, Scissors! """

    symbol: RPSSymbol = Option("rock, paper or scissors", required=True)


@interactions.command
def ping(_: Ping):
    return "pong"


@interactions.command
def echo(cmd: Echo):
    return cmd.message, False


@interactions.command
def rps(cmd: RPS):
    choice = random.choice(list(RPSSymbol))

    if cmd.symbol == choice:
        msg = "It's a draw!"
    elif cmd.symbol == RPSSymbol.ROCK:
        if choice == RPSSymbol.SCISSORS:
            msg = "You crush me and win!"
        else:
            msg = "You get covered and lose!"
    elif cmd.symbol == RPSSymbol.PAPER:
        if choice == RPSSymbol.ROCK:
            msg = "You cover me and win!"
        else:
            msg = "You get cut and lose!"
    else:
        if choice == RPSSymbol.ROCK:
            msg = "You get crushed and lose!"
        else:
            msg = "You cut me and win!"

    return f"I took {choice.value}. {msg}"


if __name__ == "__main__":
    app.run("0.0.0.0", 8080)
