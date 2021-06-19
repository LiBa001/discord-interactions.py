Discord Interactions
====================

.. image:: https://badge.fury.io/py/discord-interactions.py.svg
    :target: https://pypi.org/project/discord-interactions.py
    :alt: PyPI

.. image:: https://readthedocs.org/projects/discord-interactionspy/badge/?version=latest
    :target: https://discord-interactionspy.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

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

    from discord_interactions.ext.flask import Interactions
    from discord_interactions import (
        ApplicationCommand,
        ApplicationCommandOption,
        ApplicationCommandOptionType,
        Interaction,
        InteractionResponse,
        InteractionCallbackType,
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
            type=InteractionCallbackType.CHANNEL_MESSAGE_WITH_SOURCE,
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
        # different way of getting an option
        msg = interaction.data.get_option("message").value

        return msg

Now, we don't need to deal with ``InteractionResponse`` anymore, but instead just
return the response content as a string. The response type then defaults to
``InteractionCallbackType.CHANNEL_MESSAGE``. You could also just return
None, if you don't want to send a response. You can also simply return a boolean as a
second value, indicating whether or not the response should be ephemeral
(i.e. only visible to the invoking user).
Also we get the option via the ``get_option`` helper method.


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

    from discord_interactions.ext.flask import Interactions
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


Followup Messages
~~~~~~~~~~~~~~~~~

If you want to send messages after the initial response, you need to create followup
messages. For this purpose you can use the ``after_command`` decorator, that registers
a function to be called after the actual command function has returned. The function
needs to take exactly one parameter, the ``AfterCommandContext``, which contains the
several things, like the ``Interaction`` and initial ``InteractionResponse``.

.. code-block:: py

    interactions = Interactions(app, PUBLIC_KEY)

    @interactions.command("delay")
    def delay(_: Interaction):
        return "starting countdown", True  # this message is ephemeral


    @delay.after_command
    def after_delay(ctx: AfterCommandContext):
        delay_time = ctx.interaction.data.options[0].value
        time.sleep(delay_time)
        ctx.send(f"{delay_time} seconds have passed")


Message Components
~~~~~~~~~~~~~~~~~~

You can also register callbacks for message components, such as buttons.
Components are registered and identified by their ``custom_id``.

.. code-block:: py

    @interactions.component("my_button")
    def my_button_handler(ctx: ComponentContext):
        return f"{ctx.interaction.user.username} clicked the button"


More Examples
-------------

For more examples of the different features take a look at examples_.

If you want to know how to make your Discord bot work with Slash Commands
and how to set everything up, take a look at `this example project`__.
It hosts the program in a serverless environment via Google Cloud Run and also
provides a demo bot, so you can try out Slash Commands in your Discord server.
Check it out to learn more!

__ https://github.com/LiBa001/discord-interactions-example


.. _Git: https://git-scm.com
.. _PyPI: https://pypi.org
.. _Flask: https://flask.palletsprojects.com/
.. _ORMs: https://en.wikipedia.org/wiki/Object%E2%80%93relational_mapping
.. _examples: https://github.com/LiBa001/discord-interactions.py/tree/master/examples
