from discord_interaction.utils import verify_key
from discord_interaction import InteractionType, InteractionResponseType
from flask import request, jsonify
from functools import wraps


def verify_key_decorator(client_public_key):
    # https://stackoverflow.com/questions/51691730/flask-middleware-for-specific-route
    def _decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # Verify request
            signature = request.headers.get('X-Signature-Ed25519')
            timestamp = request.headers.get('X-Signature-Timestamp')

            if (
                signature is None or timestamp is None or
                not verify_key(request.data, signature, timestamp, client_public_key)
            ):
                return 'Bad request signature', 401

            # Automatically respond to pings
            if request.json and request.json.get('type') == InteractionType.PING:
                return jsonify({
                    'type': InteractionResponseType.PONG
                })

            # Pass through
            return f(*args, **kwargs)
        return wrapper
    return _decorator
