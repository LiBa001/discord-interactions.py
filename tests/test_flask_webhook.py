import pytest
from flask import Response

from examples import flask_webhook, flask_webhook_ocm

from discord_interactions import InteractionType


@pytest.mark.parametrize("app", [flask_webhook.app, flask_webhook_ocm.app])
def test_echo(app):
    """ Test the echo command. """

    app.config["TESTING"] = True

    msg = "this is a test message"

    interaction = {
        "id": "11111",
        "type": InteractionType.APPLICATION_COMMAND.value,
        "data": {
            "id": "44444",
            "name": "echo",
            "options": [{"name": "message", "value": msg}],
        },
        "guild_id": "22222",
        "channel_id": "33333",
        "member": {
            "nick": None,
            "roles": [],
            "joined_at": "2021-01-04T23:38:01.370760",
            "deaf": False,
            "mute": False,
        },
        "token": "abc",
        "version": 1,
    }

    with app.test_client() as client:
        rv: Response = client.post("/", json=interaction)

    interaction_response = rv.get_json()

    assert interaction_response["data"]["content"] == msg
