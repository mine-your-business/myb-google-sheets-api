import json
from urllib.parse import parse_qs, urlparse

import pytest
from googleapiclient.errors import HttpError

from sheets import SheetsApi
from sheets.client import READ_WRITE_SCOPES

from .conftest import SERVICE_ACCOUNT_INFO, SPREADSHEET_ID, load_fixture, response


def _path_and_query(uri):
    parsed = urlparse(uri)
    return parsed.path, parse_qs(parsed.query)


class TestConstruction:
    def test_credentials_built_from_service_account_info_with_read_write_scope(self, offline):
        offline.client()

        assert offline.credentials_calls == [(SERVICE_ACCOUNT_INFO, {'scopes': READ_WRITE_SCOPES})]
        assert READ_WRITE_SCOPES == ['https://www.googleapis.com/auth/spreadsheets']

    def test_builds_sheets_v4_service_with_those_credentials(self, offline):
        offline.client()

        [(service_name, version, credentials, kwargs)] = offline.build_calls
        assert (service_name, version) == ('sheets', 'v4')
        assert credentials is not None
        assert kwargs == {'cache_discovery': False}

    def test_construction_makes_no_network_calls(self, offline):
        offline.client()

        assert offline.requests == []

    def test_is_exported_from_package(self):
        import sheets.client

        assert SheetsApi is sheets.client.SheetsApi


class TestReadFromSheet:
    def test_posts_batch_get_by_data_filter_request(self, offline):
        api = offline.client(response(200, 'batch-get-by-data-filter-response-200.json'))

        api.read_from_sheet(SPREADSHEET_ID, load_fixture('read-data-filter-a1-range.json'))

        [(uri, method, body, _headers)] = offline.requests
        path, _query = _path_and_query(uri)
        assert method == 'POST'
        assert path == f'/v4/spreadsheets/{SPREADSHEET_ID}/values:batchGetByDataFilter'
        assert json.loads(body) == load_fixture('batch-get-by-data-filter-request.json')

    def test_returns_value_ranges(self, offline):
        api = offline.client(response(200, 'batch-get-by-data-filter-response-200.json'))

        value_ranges = api.read_from_sheet(SPREADSHEET_ID, load_fixture('read-data-filter-a1-range.json'))

        expected = load_fixture('batch-get-by-data-filter-response-200.json')['valueRanges']
        assert value_ranges == expected
        assert value_ranges[0]['valueRange']['values'][1] == ['2021-06-01', 'BTC', '0.01234567']

    def test_returns_empty_list_when_no_ranges_match(self, offline):
        api = offline.client(response(200, 'batch-get-by-data-filter-response-200-no-matches.json'))

        assert api.read_from_sheet(SPREADSHEET_ID, load_fixture('read-data-filter-a1-range.json')) == []

    def test_raises_http_error_for_missing_spreadsheet(self, offline):
        api = offline.client(response(404, 'error-404-spreadsheet-not-found.json'))

        with pytest.raises(HttpError) as excinfo:
            api.read_from_sheet(SPREADSHEET_ID, load_fixture('read-data-filter-a1-range.json'))

        assert excinfo.value.status_code == 404
        assert excinfo.value.reason == 'Requested entity was not found.'


class TestWriteToSheet:
    def test_posts_batch_update_by_data_filter_request(self, offline):
        api = offline.client(response(200, 'batch-update-by-data-filter-response-200.json'))

        api.write_to_sheet(SPREADSHEET_ID, load_fixture('write-data-filter-value-range.json'))

        [(uri, method, body, _headers)] = offline.requests
        path, _query = _path_and_query(uri)
        assert method == 'POST'
        assert path == f'/v4/spreadsheets/{SPREADSHEET_ID}/values:batchUpdateByDataFilter'
        assert json.loads(body) == load_fixture('batch-update-by-data-filter-request.json')

    def test_returns_full_response(self, offline):
        api = offline.client(response(200, 'batch-update-by-data-filter-response-200.json'))

        result = api.write_to_sheet(SPREADSHEET_ID, load_fixture('write-data-filter-value-range.json'))

        assert result == load_fixture('batch-update-by-data-filter-response-200.json')

    def test_logs_response_at_debug_instead_of_printing(self, offline, caplog, capsys):
        api = offline.client(response(200, 'batch-update-by-data-filter-response-200.json'))

        with caplog.at_level('DEBUG', logger='sheets.client'):
            api.write_to_sheet(SPREADSHEET_ID, load_fixture('write-data-filter-value-range.json'))

        assert capsys.readouterr().out == ''
        assert 'batchUpdateByDataFilter response' in caplog.text

    def test_raises_http_error_when_caller_lacks_permission(self, offline):
        api = offline.client(response(403, 'error-403-caller-lacks-permission.json'))

        with pytest.raises(HttpError) as excinfo:
            api.write_to_sheet(SPREADSHEET_ID, load_fixture('write-data-filter-value-range.json'))

        assert excinfo.value.status_code == 403
