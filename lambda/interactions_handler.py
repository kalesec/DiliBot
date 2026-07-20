"""Public-facing Discord interactions endpoint.

Discord POSTs every slash command here via a Lambda Function URL. This function
does the minimum possible work: verify the request really came from Discord,
acknowledge it within Discord's 3 second deadline, and hand the actual audit off
to the worker function.

It deliberately holds no bot token and needs no outbound internet access.
"""

import json
import os

import boto3
from nacl.exceptions import BadSignatureError
from nacl.signing import VerifyKey

# The application public key is not a secret -- it is published in the Developer
# Portal and only used to verify Discord's signature. Plain env var is correct.
PUBLIC_KEY = os.environ["DISCORD_PUBLIC_KEY"]
WORKER_FUNCTION_NAME = os.environ["WORKER_FUNCTION_NAME"]

# Interaction types Discord sends us
PING = 1
APPLICATION_COMMAND = 2

# Interaction response types we send back
PONG = 1
DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE = 5

_verify_key = VerifyKey(bytes.fromhex(PUBLIC_KEY))
_lambda = boto3.client("lambda")


def _response(status, body):
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }


def _signature_is_valid(event):
    """Verify the Ed25519 signature Discord attaches to every request.

    Discord signs the concatenation of the timestamp header and the raw body.
    Any failure here means the request did not come from Discord.
    """
    headers = {k.lower(): v for k, v in (event.get("headers") or {}).items()}
    signature = headers.get("x-signature-ed25519")
    timestamp = headers.get("x-signature-timestamp")
    body = event.get("body") or ""

    if not signature or not timestamp:
        return False

    try:
        _verify_key.verify(
            f"{timestamp}{body}".encode(), bytes.fromhex(signature)
        )
    except (BadSignatureError, ValueError):
        return False
    return True


def lambda_handler(event, context):
    # Reject before parsing anything -- an unsigned request gets no further.
    if not _signature_is_valid(event):
        return _response(401, {"error": "invalid request signature"})

    body = json.loads(event.get("body") or "{}")
    interaction_type = body.get("type")

    # Discord validates the endpoint URL by sending a signed PING and expecting
    # a PONG. This is also what the Developer Portal checks when saving the URL.
    if interaction_type == PING:
        return _response(200, {"type": PONG})

    if interaction_type == APPLICATION_COMMAND:
        # The audit makes two external HTTP calls and will not finish inside
        # Discord's 3 second window, so defer. This shows a "thinking" state and
        # gives the worker 15 minutes to edit the response in place.
        _lambda.invoke(
            FunctionName=WORKER_FUNCTION_NAME,
            InvocationType="Event",  # fire and forget, do not wait
            Payload=json.dumps(
                {
                    "token": body["token"],
                    "guild_id": body.get("guild_id"),
                    "data": body.get("data", {}),
                }
            ).encode(),
        )
        return _response(200, {"type": DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE})

    return _response(400, {"error": "unsupported interaction type"})
