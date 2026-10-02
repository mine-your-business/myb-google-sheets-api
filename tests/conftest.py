import json
from pathlib import Path

import pytest
from googleapiclient import discovery
from googleapiclient.http import HttpMockSequence

import sheets.client

FIXTURES = Path(__file__).parent / 'fixtures'

SPREADSHEET_ID = '1AbCdEfGhIjKlMnOpQrStUvWxYz0123456789abcdEFG'
SERVICE_ACCOUNT_INFO = {'type': 'service_account', 'client_email': 'tests@example.iam.gserviceaccount.com'}


def load_fixture(name):
    return json.loads((FIXTURES / name).read_text())


def response(status, fixture_name):
    return ({'status': str(status), 'content-type': 'application/json'}, (FIXTURES / fixture_name).read_text())


class OfflineSheets:
    """Wires SheetsApi to an httplib2 mock instead of Google.

    The real discovery document bundled with google-api-python-client is used, so
    request URLs and bodies are built exactly as they are in production.
    """

    def __init__(self, monkeypatch):
        self.credentials_calls = []
        self.build_calls = []
        self.http = None
        self._monkeypatch = monkeypatch

        def fake_from_service_account_info(info, **kwargs):
            self.credentials_calls.append((info, kwargs))
            return object()

        monkeypatch.setattr(
            sheets.client.service_account.Credentials,
            'from_service_account_info',
            staticmethod(fake_from_service_account_info),
        )

    def client(self, *responses):
        self.http = HttpMockSequence(list(responses))
        real_build = discovery.build

        def fake_build(service_name, version, credentials=None, **kwargs):
            self.build_calls.append((service_name, version, credentials, kwargs))
            # build() rejects http= together with credentials=, so the mock replaces them.
            return real_build(service_name, version, http=self.http, **kwargs)

        self._monkeypatch.setattr(sheets.client, 'build', fake_build)
        return sheets.client.SheetsApi(SERVICE_ACCOUNT_INFO)

    @property
    def requests(self):
        return self.http.request_sequence


@pytest.fixture
def offline(monkeypatch):
    return OfflineSheets(monkeypatch)
