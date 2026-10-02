"""Exercises the real google-auth service account flow against mocked HTTP.

The signing key is generated per run so no private key is committed.
"""

import base64
import json
from urllib.parse import parse_qs

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from googleapiclient import http as googleapiclient_http
from googleapiclient.http import HttpMockSequence

from sheets import SheetsApi

from .conftest import SPREADSHEET_ID, load_fixture, response


@pytest.fixture(scope='module')
def service_account_info():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode()
    return {
        'type': 'service_account',
        'project_id': 'test-project',
        'private_key_id': 'test-key-id',
        'private_key': pem,
        'client_email': 'tests@test-project.iam.gserviceaccount.com',
        'client_id': '1234567890',
        'token_uri': 'https://oauth2.googleapis.com/token',
    }


def test_read_fetches_token_then_calls_api_with_bearer(monkeypatch, service_account_info):
    mock_http = HttpMockSequence(
        [
            response(200, 'oauth-token-response-200.json'),
            response(200, 'batch-get-by-data-filter-response-200.json'),
        ]
    )
    monkeypatch.setattr(googleapiclient_http, 'build_http', lambda: mock_http)

    api = SheetsApi(service_account_info)
    value_ranges = api.read_from_sheet(SPREADSHEET_ID, load_fixture('read-data-filter-a1-range.json'))

    assert value_ranges == load_fixture('batch-get-by-data-filter-response-200.json')['valueRanges']

    (token_uri, _, token_body, _), (api_uri, _, _, api_headers) = mock_http.request_sequence
    assert token_uri == 'https://oauth2.googleapis.com/token'
    token_form = parse_qs(token_body if isinstance(token_body, str) else token_body.decode())
    assert token_form['grant_type'] == ['urn:ietf:params:oauth:grant-type:jwt-bearer']
    assert 'assertion' in token_form

    assert api_uri.startswith(f'https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}/values')
    auth_header = {k.lower(): v for k, v in api_headers.items()}['authorization']
    assert auth_header == 'Bearer ' + load_fixture('oauth-token-response-200.json')['access_token']


def test_jwt_assertion_requests_spreadsheets_scope(monkeypatch, service_account_info):
    mock_http = HttpMockSequence(
        [
            response(200, 'oauth-token-response-200.json'),
            response(200, 'batch-get-by-data-filter-response-200-no-matches.json'),
        ]
    )
    monkeypatch.setattr(googleapiclient_http, 'build_http', lambda: mock_http)

    SheetsApi(service_account_info).read_from_sheet(SPREADSHEET_ID, load_fixture('read-data-filter-a1-range.json'))

    token_body = mock_http.request_sequence[0][2]
    assertion = parse_qs(token_body if isinstance(token_body, str) else token_body.decode())['assertion'][0]
    payload_segment = assertion.split('.')[1]
    claims = json.loads(base64.urlsafe_b64decode(payload_segment + '=' * (-len(payload_segment) % 4)))
    assert claims['scope'] == 'https://www.googleapis.com/auth/spreadsheets'
    assert claims['iss'] == service_account_info['client_email']
