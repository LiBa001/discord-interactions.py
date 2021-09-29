import pytest
from flask import Response, Flask
from typing import Tuple, TypeVar

from examples import flask_webhook, flask_webhook_ocm, flask_webhook_components

from discord_interactions import (
    InteractionType,
    InteractionCallbackType,
    ComponentType,
    ApplicationCommandType,
)

DO_NOT_VALIDATE = TypeVar("DO_NOT_VALIDATE")

command_apps = [flask_webhook.app, flask_webhook_ocm.app]
command_data = [
    (
        {
            "id": "44444",
            "name": "ping",
            "resolved": {},
            "options": [],
            "type": ApplicationCommandType.CHAT_INPUT.value,
        },
        {
            "type": InteractionCallbackType.CHANNEL_MESSAGE.value,
            "data": {"content": "pong"},
        },
    ),
    (
        {
            "id": "44444",
            "name": "echo",
            "resolved": {},
            "options": [
                {"name": "message", "type": 3, "value": "this is a test message"}
            ],
            "type": ApplicationCommandType.CHAT_INPUT.value,
        },
        {
            "type": InteractionCallbackType.CHANNEL_MESSAGE.value,
            "data": {
                "content": "this is a test message",
            },
        },
    ),
    (
        {
            "id": "44444",
            "name": "rps",
            "resolved": {},
            "options": [{"name": "symbol", "type": 3, "value": "paper"}],
            "type": ApplicationCommandType.CHAT_INPUT.value,
        },
        {
            "type": InteractionCallbackType.CHANNEL_MESSAGE.value,
            "data": {
                "content": DO_NOT_VALIDATE,
            },
        },
    ),
    (
        {
            "id": "44444",
            "name": "guess",
            "resolved": {},
            "options": [
                {"name": "number", "type": 4, "value": 42},
                {"name": "max_num", "type": 4, "value": 69},
            ],
            "type": ApplicationCommandType.CHAT_INPUT.value,
        },
        {
            "type": InteractionCallbackType.CHANNEL_MESSAGE.value,
            "data": {
                "content": DO_NOT_VALIDATE,
            },
        },
    ),
    (
        {
            "id": "44444",
            "name": "guess",
            "resolved": {},
            "options": [
                {"name": "number", "type": 4, "value": 7},
            ],
            "type": ApplicationCommandType.CHAT_INPUT.value,
        },
        {
            "type": InteractionCallbackType.CHANNEL_MESSAGE.value,
            "data": {
                "content": DO_NOT_VALIDATE,
            },
        },
    ),
    (
        {
            "id": "44444",
            "name": "hug",
            "resolved": {
                "members": {
                    "123456789": {
                        "nick": None,
                        "roles": [],
                        "joined_at": "2021-01-04T23:38:01.370760",
                        "deaf": False,
                        "mute": False,
                    }
                }
            },
            "options": [
                {"name": "cutie", "type": 6, "value": "123456789"},
            ],
            "type": ApplicationCommandType.CHAT_INPUT.value,
        },
        {
            "type": InteractionCallbackType.CHANNEL_MESSAGE.value,
            "data": {
                "content": "<@987654321> *hugs* <@123456789>",
            },
        },
    ),
    (
        {
            "id": "44444",
            "name": "generate",
            "resolved": {},
            "options": [
                {
                    "name": "sha1",
                    "type": 1,
                    "options": [{"name": "text", "type": 3, "value": "hello world"}],
                },
            ],
            "type": ApplicationCommandType.CHAT_INPUT.value,
        },
        {
            "type": InteractionCallbackType.CHANNEL_MESSAGE.value,
            "data": {
                "content": '"hello world"\n=> `2aae6c35c94fcfb415dbe95f408b9ce91ee846ed`',
                "flags": 64,
            },
        },
    ),
    (
        {
            "id": "44444",
            "name": "kick",
            "resolved": {
                "users": {
                    "987654321": {
                        "id": "987654321",
                        "username": "test-user",
                        "discriminator": "1234",
                    },
                },
            },
            "type": ApplicationCommandType.USER.value,
            "target_id": "987654321",
        },
        {
            "type": InteractionCallbackType.CHANNEL_MESSAGE.value,
            "data": {
                "content": "kicked test-user",
                "flags": 64,
            },
        },
    ),
    (
        {
            "id": "44444",
            "name": "delete",
            "resolved": {
                "messages": {
                    "867793854505943041": {
                        "attachments": [],
                        "author": {
                            "avatar": "a_f03401914fb4f3caa9037578ab980920",
                            "discriminator": "6538",
                            "id": "167348773423415296",
                            "public_flags": 1,
                            "username": "ian"
                        },
                        "channel_id": "772908445358620702",
                        "components": [],
                        "content": "some message",
                        "edited_timestamp": None,
                        "embeds": [],
                        "flags": 0,
                        "id": "867793854505943041",
                        "mention_everyone": False,
                        "mention_roles": [],
                        "mentions": [],
                        "pinned": False,
                        "timestamp": "2021-07-22T15:42:57.744000+00:00",
                        "tts": False,
                        "type": 0
                    }
                },
            },
            "type": ApplicationCommandType.USER.value,
            "target_id": "867793854505943041",
        },
        {
            "type": InteractionCallbackType.CHANNEL_MESSAGE.value,
            "data": {
                "content": "deleted message || some message ||",
                "flags": 64,
            },
        },
    ),
]


def _test_interaction(app: Flask, data: Tuple[dict, dict], i_type: InteractionType):
    app.config["TESTING"] = True

    interaction = {
        "id": "11111",
        "application_id": "55555",
        "type": i_type.value,
        "data": data[0],
        "guild_id": "22222",
        "channel_id": "33333",
        "member": {
            "user": {
                "id": "987654321",
                "username": "test-user",
                "discriminator": "1234",
            },
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


@pytest.mark.parametrize("app", command_apps)
@pytest.mark.parametrize("data", command_data)
def test_commands(app: Flask, data: Tuple[dict, dict]):
    """Test application commands."""

    _test_interaction(app, data, InteractionType.APPLICATION_COMMAND)


component_apps = [flask_webhook_components.app]
component_data = [
    (
        {
            "custom_id": "my_button",
            "component_type": ComponentType.Button.value,
        },
        {
            "type": InteractionCallbackType.UPDATE_MESSAGE.value,
            "data": {"content": "test-user clicked the button"},
        },
    ),
    (
        {
            "custom_id": "confirm_deletion:42",
            "component_type": ComponentType.Button.value,
        },
        {
            "type": InteractionCallbackType.UPDATE_MESSAGE.value,
            "data": {"content": "successfully deleted resource 42"},
        },
    ),
]


@pytest.mark.parametrize("app", component_apps)
@pytest.mark.parametrize("data", component_data)
def test_components(app: Flask, data: Tuple[dict, dict]):
    """Test message components."""

    _test_interaction(app, data, InteractionType.MESSAGE_COMPONENT)
