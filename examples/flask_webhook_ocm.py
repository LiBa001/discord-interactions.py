from discord_interactions.ext.flask import Interactions
from discord_interactions.ext import CommandContext
from discord_interactions.ocm import Command, SubCommand, Option, OptionChoices, UserCommand, MessageCommand
from discord_interactions import User
from flask import Flask
import os
import random
import hashlib

app = Flask(__name__)
interactions = Interactions(app, os.getenv("CLIENT_PUBLIC_KEY"))


class Ping(Command):
    """simple ping command"""


class Echo(Command):
    """what goes around comes around"""

    message: str = Option("This will be echoed.", required=True)


class RPSSymbol(OptionChoices):
    ROCK = "rock"
    PAPER = "paper"
    SCISSORS = "scissors"


class RPS(Command):
    """Play Rock, Paper, Scissors!"""

    symbol: RPSSymbol = Option("rock, paper or scissors", required=True)


class Guess(Command):
    """Guess my number!"""

    number: int = Option("what do you guess?", required=True)
    min_num: int = Option("smallest possible number (default: 0)")
    max_num: int = Option("biggest possible number (default: 10)")


class Hug(Command):
    """Hug someone nice"""

    cutie: User = Option("hug this person", required=True)


class Sha1(SubCommand):
    """Generate a SHA1 hash"""

    text: str = Option("the text to be hashed", required=True)


class Generate(Command):
    """Generate different things"""

    sha1 = Sha1()


# user and message commands
Kick = UserCommand.create("kick")
Delete = MessageCommand.create("delete")


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


@interactions.command
def hug(cmd: Hug):
    return f"<@{cmd.author.id}> *hugs* <@{cmd.cutie}>"


@interactions.command(Generate)
def generate():
    pass  # this function gets called before any subcommands


@generate.subcommand()
def sha1(_: CommandContext, cmd: Sha1):
    txt = cmd.text
    return f'"{txt}"\n=> `{hashlib.sha1(txt.encode()).hexdigest()}`', True


@generate.fallback
def generate_fallback(_: CommandContext):
    return "error: no subcommand provided", True


# === user and message commands ===


@interactions.command
def kick(cmd: Kick):
    ...  # kick user
    return f"kicked {cmd.user.username}", True


@interactions.command
def delete(cmd: Delete):
    ...  # delete message
    return f"deleted message || {cmd.message.content} ||", True


if __name__ == "__main__":
    app.run("0.0.0.0", 8080)
