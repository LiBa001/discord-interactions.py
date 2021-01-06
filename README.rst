Discord Interactions
====================

.. image:: https://badge.fury.io/py/discord-interactions.py.svg
    :target: https://pypi.org/project/discord-interactions.py
    :alt: PyPI

.. image:: https://img.shields.io/github/license/LiBa001/discord-interactions.py
    :target: https://github.com/LiBa001/discord-interactions.py/blob/master/LICENSE
    :alt: License

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/psf/black

.. image:: https://github.com/LiBa001/discord-interactions.py/workflows/Python%20package/badge.svg
    :target: https://github.com/LiBa001/discord-interactions.py/actions


A wrapper for the Discord Interactions API that does not rely on websockets
and can therefore be used in a stateless webhook environment.

Furthermore, it allows for strict separation between your commands' structure
and and the data that is received when triggering it.


Installation
------------

Requires Python 3.8+

Latest release from PyPI_ using *pip*:
    ``pip install discord-interactions.py``

Latest commit from GitHub using *pip* and *git*:
    ``pip install git+https://github.com/LiBa001/discord-interactions.py``

.. note::

    Installing directly from GitHub
    requires you to have Git_ installed on your computer.

If this doesn't work, you might try:
    ``python -m pip install ...``
Or if you are on windows:
    ``py -m pip install ...``


Use with Flask
--------------

This library is specifically designed to work seamlessly with the Flask_ microframework.

Using API-like Data Classes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The most API-like example with the flask extension is this:

.. code-block:: py

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
            type=InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
            data=InteractionApplicationCommandCallbackData(content=msg),
        )

Here, we use the rudimentary ``ApplicationCommand``, ``Interaction`` and
``InteractionResponse`` classes, which are in their structure basically
exact counterparts of the `original API models`__.

__ https://discord.com/developers/docs/interactions/slash-commands#data-models-and-types

Let's make it a bit simpler:

.. code-block:: py

    @interactions.command(echo_cmd)
    def _echo(interaction: Interaction):
        msg = interaction.data.options[0].value  # "message" option content

        return msg

Now, we don't need to deal with ``InteractionResponse`` anymore, but instead just
return the response content as a string. The response type then defaults to
``InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE``. You could also just return
None, if you don't want to send a response. You can also simply return a boolean as a
second value, indicating whether or not the command call should be displayed in Discord
(i.e. the ``_WITH_SOURCE`` part of the response type).


The Object-Command Mapper
~~~~~~~~~~~~~~~~~~~~~~~~~

This library provides another abstraction layer, though.
Inspired by the concept of database ORMs_, it has an Object-Command Mapper (OCM)
that lets you define a class for each command which will then serve as both
a generic structural description of the command (like ``ApplicationCommand``)
**and** a container for the actual data that is received
when the command is called (like ``Interaction``).

So, the simplest possible example looks like this:

.. code-block:: py

    from discord_interactions.flask_ext import Interactions
    from discord_interactions.ocm import Command, Option
    from flask import Flask
    import os

    app = Flask(__name__)
    interactions = Interactions(app, os.getenv("CLIENT_PUBLIC_KEY"))


    class _Echo(Command):
        """ what goes around comes around """

        message: str = Option("This will be echoed.", required=True)


    @interactions.command
    def _echo(cmd: _Echo):
        return cmd.message


More Examples
~~~~~~~~~~~~~

For more examples take a look at examples_.


.. _Git: https://git-scm.com
.. _PyPI: https://pypi.org
.. _Flask: https://flask.palletsprojects.com/
.. _ORMs: https://en.wikipedia.org/wiki/Object%E2%80%93relational_mapping
.. _examples: https://github.com/LiBa001/discord-interactions.py/tree/master/examples
