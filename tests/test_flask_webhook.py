import pytest
from flask import Response, Flask
from typing import Tuple, TypeVar

from examples import flask_webhook, flask_webhook_ocm

from discord_interactions import InteractionType, InteractionResponseType

DO_NOT_VALIDATE = TypeVar("DO_NOT_VALIDATE")

test_apps = [flask_webhook.app, flask_webhook_ocm.app]
test_data = [
    (
        {
            "id": "44444",
            "name": "ping",
            "options": [],
        },
        {
            "type": InteractionResponseType.CHANNEL_MESSAGE.value,
            "data": {"content": "pong"},
        },
    ),
    (
        {
            "id": "44444",
            "name": "echo",
            "options": [{"name": "message", "value": "this is a test message"}],
        },
        {
            "type": InteractionResponseType.CHANNEL_MESSAGE.value,
            "data": {
                "content": "this is a test message",
            },
        },
    ),
    (
        {
            "id": "44444",
            "name": "rps",
            "options": [{"name": "symbol", "value": "paper"}],
        },
        {
            "type": InteractionResponseType.CHANNEL_MESSAGE.value,
            "data": {
                "content": DO_NOT_VALIDATE,
            },
        },
    ),
    (
        {
            "id": "44444",
            "name": "guess",
            "options": [
                {"name": "number", "value": 42},
                {"name": "max_num", "value": 69},
            ],
        },
        {
            "type": InteractionResponseType.CHANNEL_MESSAGE.value,
            "data": {
                "content": DO_NOT_VALIDATE,
            },
        },
    ),
    (
        {
            "id": "44444",
            "name": "guess",
            "options": [
                {"name": "number", "value": 7},
            ],
        },
        {
            "type": InteractionResponseType.CHANNEL_MESSAGE.value,
            "data": {
                "content": DO_NOT_VALIDATE,
            },
        },
    ),
]


@pytest.mark.parametrize("app", test_apps)
@pytest.mark.parametrize("data", test_data)
def test_commands(app: Flask, data: Tuple[dict, dict]):
    """ Test the echo command. """

    app.config["TESTING"] = True

    interaction = {
        "id": "11111",
        "type": InteractionType.APPLICATION_COMMAND.value,
        "data": data[0],
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
    expected_response = data[1]

    for key, value in expected_response["data"].items():
        if value is DO_NOT_VALIDATE:
            interaction_response["data"][key] = DO_NOT_VALIDATE

    assert interaction_response == expected_response
