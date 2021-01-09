from discord_interactions.flask_ext import Interactions, CommandContext
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


class Guess(Command):
    """ Guess my number! """

    number: int = Option("what do you guess?", required=True)
    min_num: int = Option("smallest possible number (default: 0)")
    max_num: int = Option("biggest possible number (default: 10)")


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


# This type of syntax does also work with the OCM, though, it will lose the advantage
# of the command class being used as container for the interaction data.
@interactions.command(Guess)
def guess(ctx: CommandContext, guessed_num, min_num=None, max_num=None):
    min_val = min_num or 0  # defaults to 0
    max_val = max_num or 10  # defaults to 10

    my_number = random.randint(min_val, max_val)

    if my_number == guessed_num:
        msg = "You are correct! :tada:"
    else:
        msg = "You guessed it wrong. :confused:"

    return f"My number was {my_number}. {msg}"


if __name__ == "__main__":
    app.run("0.0.0.0", 8080)
