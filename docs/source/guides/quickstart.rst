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
    like `AWS lambda`_ or `Google Cloud Run`_. An example project for setting up a bot
    that uses this library and is hosted on Cloud Run can be found here__.

__ https://github.com/LiBa001/discord-interactions-example

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
