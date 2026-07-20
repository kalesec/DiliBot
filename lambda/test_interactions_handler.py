"""Offline tests for the interactions endpoint's signature handling.

The endpoint is publicly reachable with no AWS auth in front of it, so Ed25519
verification is the only thing standing between the internet and the worker.
These tests run without AWS or Discord.

Usage:  python test_interactions_handler.py
"""

import json
import os
import sys
from unittest import mock

from nacl.signing import SigningKey

# A throwaway keypair standing in for the Discord application keypair.
_signing_key = SigningKey.generate()
os.environ["DISCORD_PUBLIC_KEY"] = _signing_key.verify_key.encode().hex()
os.environ["WORKER_FUNCTION_NAME"] = "dilibot-worker-test"

# boto3 builds a real Lambda client at import time; stub it so no AWS call or
# credential lookup happens during tests.
_fake_lambda = mock.MagicMock()
with mock.patch("boto3.client", return_value=_fake_lambda):
    import interactions_handler


def _signed_event(payload, tamper=False):
    """Build a Function URL event carrying a validly signed body."""
    body = json.dumps(payload)
    timestamp = "1700000000"
    signature = _signing_key.sign(f"{timestamp}{body}".encode()).signature.hex()
    if tamper:
        # Flip the payload after signing -- the signature no longer matches.
        body = json.dumps({**payload, "injected": "evil"})
    return {
        "headers": {
            "X-Signature-Ed25519": signature,
            "X-Signature-Timestamp": timestamp,
        },
        "body": body,
    }


def _check(name, condition):
    print(f"{'PASS' if condition else 'FAIL'}  {name}")
    return condition


def main():
    results = []

    # A signed PING must return PONG. This is exactly what the Developer Portal
    # sends when validating the Interactions Endpoint URL.
    response = interactions_handler.lambda_handler(_signed_event({"type": 1}), None)
    results.append(
        _check(
            "signed PING returns 200 with type 1 (PONG)",
            response["statusCode"] == 200
            and json.loads(response["body"])["type"] == 1,
        )
    )

    # A signed /audit must defer (type 5) and dispatch to the worker.
    _fake_lambda.reset_mock()
    command = {
        "type": 2,
        "token": "interaction-token-abc",
        "guild_id": "123456789",
        "data": {
            "name": "audit",
            "options": [{"name": "raid_id", "value": "1514020131834036406"}],
        },
    }
    response = interactions_handler.lambda_handler(_signed_event(command), None)
    results.append(
        _check(
            "signed /audit returns 200 with type 5 (deferred)",
            response["statusCode"] == 200
            and json.loads(response["body"])["type"] == 5,
        )
    )
    results.append(
        _check(
            "/audit invokes worker asynchronously with the interaction token",
            _fake_lambda.invoke.call_count == 1
            and _fake_lambda.invoke.call_args.kwargs["InvocationType"] == "Event"
            and json.loads(_fake_lambda.invoke.call_args.kwargs["Payload"])["token"]
            == "interaction-token-abc",
        )
    )

    # A tampered body must be rejected, and must not reach the worker.
    _fake_lambda.reset_mock()
    response = interactions_handler.lambda_handler(
        _signed_event(command, tamper=True), None
    )
    results.append(
        _check(
            "tampered body returns 401",
            response["statusCode"] == 401,
        )
    )
    results.append(
        _check(
            "tampered body does not invoke the worker",
            _fake_lambda.invoke.call_count == 0,
        )
    )

    # Missing headers must be rejected rather than raising.
    response = interactions_handler.lambda_handler({"headers": {}, "body": "{}"}, None)
    results.append(
        _check("missing signature headers returns 401", response["statusCode"] == 401)
    )

    # A malformed signature must be rejected rather than raising.
    response = interactions_handler.lambda_handler(
        {
            "headers": {
                "X-Signature-Ed25519": "not-hex",
                "X-Signature-Timestamp": "1700000000",
            },
            "body": "{}",
        },
        None,
    )
    results.append(
        _check("malformed signature returns 401", response["statusCode"] == 401)
    )

    print()
    if all(results):
        print(f"All {len(results)} checks passed.")
        return 0
    print(f"{results.count(False)} of {len(results)} checks FAILED.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
