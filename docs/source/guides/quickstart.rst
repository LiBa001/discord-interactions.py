.. py:currentmodule:: discord_interactions

Quickstart Guide
================

This library enables you to easily use the Discord Interactions API with your
App or Bot on Discord.

It is based on interactions being received via the outgoing webhook method.
If you don't know about the different ways interactions can be received, check out
the `corresponding page of the Discord Documentation`__. But don't worry about the more
complicated stuff you see there, since it will be taken care of for you when you are
using this library.

__ https://discord.com/developers/docs/interactions/slash-commands#receiving-an-interaction

.. note::
    This means that you will need to host a webserver that can be publicly accessed via
    secure HTTPS. A great way of achieving this is to use serverless cloud solutions
    like `AWS lambda`_ or `Google Cloud Run`_. An `example project`_ for setting up a
    bot that uses this library and is hosted on Cloud Run can be found here__.

__ `example project`_

.. _AWS lambda: https://aws.amazon.com/lambda/
.. _Google Cloud Run: https://cloud.google.com/run

Installation
------------

See :ref:`installation`!


Code
----

Now we can start coding!

Import the module like this:

.. code-block:: py

    import discord_interactions


Flask Webhook
~~~~~~~~~~~~~

The main purpose that you will probably want to use ``discord-interactions.py`` for, is
handling the HTTP calls you receive, when using the Interactions API with
outgoing webhooks.

For this purpose you can use the flask extension:

.. code-block:: py

    from discord_interactions.flask_ext import Interactions
    from flask import Flask

    app = Flask(__name__)
    interactions = Interactions(app, "CLIENT_PUBLIC_KEY")

You simply create a normal Flask app and wrap it into a :class:`flask_ext.Interactions`
object. You also need to provide your app's public key, so the HTTP requests it
receives can be accordingly validated and authorized.


Registering commands
^^^^^^^^^^^^^^^^^^^^

You can now use the ``interactions`` object to register callback functions for commands
via a decorator:

.. code-block:: py

    @interactions.command
    def ping(interaction):
        return "pong"

The function will be automatically called, when someone uses a Slash Command called
"ping".

You most likely want to also define the structure of your command, though. For example
so you can also register it to Discord, i.e. making it available to use.


Defining commands
^^^^^^^^^^^^^^^^^

So the easiest way to define a command is via the Object-Command Mapper (OCM):

.. code-block:: py

    from discord_interactions.ocm import Command, Option

    class Echo(Command):
        """ Sends back what you put in. """

        message: str = Option("This will be echoed.", required=True)

Here, we defined a command named "echo". The command name is automatically set to the
lowercase name of the class and the description is set to it's docstring.
It has one required option called "message" that takes a string.

Now, you can register your command callback like this:

.. code-block:: py

    @interactions.command
    def echo(cmd: Echo):
        return cmd.message

The decorator recognises the annotation and passes an instance of your class to the
function, so you can simply access all the option data via the object's attributes.


Register commands at Discord
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Once you defined all your commands and registered them to
:class:`flask_ext.Interactions`, you are ready to create them in Discord.

This should normally be in a different file than your commands' logic, because you only
need to run it when you change something about their structure:

.. code-block:: py

    from discord_interactions import ApplicationClient

    # you need to import the "flask_ext.Interactions" object from your main file
    from main import interactions

    if __name__ == "__main__":
        client = ApplicationClient("BOT_TOKEN")

        # do this for all registered commands that we provided structural information for
        for cmd in interactions.commands:
            print("create", cmd.name)

            # You might specify a guild here.
            # Global commands can take up to one hour to be available after registration.
            client.create_command(cmd)

.. note::
    You don't necessarily need the flask extension to register commands at Discord,
    since :meth:`ApplicationClient.create_command` just takes an
    :class:`ApplicationCommand` or :class:`ocm.Command`.


Examples
--------

To see more of the different features of this library in action, visit the
`examples folder`_ on GitHub. There is also a full `example project`_.


.. _example project: https://github.com/LiBa001/discord-interactions-example
.. _examples folder: https://github.com/LiBa001/discord-interactions.py/tree/master/examples
