# myb-google-sheets-api

A small Python client for reading from and writing to Google Sheets with a service account, built on
[`google-auth`](https://pypi.org/project/google-auth/) and
[`google-api-python-client`](https://pypi.org/project/google-api-python-client/).

Requires Python 3.10 or newer.

## Installation

```
pip install myb-google-sheets-api
```

To install from source:

```
git clone https://github.com/mine-your-business/myb-google-sheets-api.git
cd myb-google-sheets-api
pip install .
```

## Usage

`SheetsApi` takes the parsed contents of a service account JSON key. The service account needs edit access to the
spreadsheet (share the sheet with its `client_email`). The client requests the
`https://www.googleapis.com/auth/spreadsheets` scope.

```python
import json

from sheets import SheetsApi

with open('service-account.json') as f:
    api = SheetsApi(json.load(f))

spreadsheet_id = '1AbCdEfGhIjKlMnOpQrStUvWxYz0123456789abcdEFG'

# read_from_sheet takes a DataFilter and returns the response's valueRanges list
# (an empty list when nothing matches).
value_ranges = api.read_from_sheet(spreadsheet_id, {'a1Range': 'Balances!A1:C3'})
rows = value_ranges[0]['valueRange'].get('values', []) if value_ranges else []

# write_to_sheet takes a DataFilterValueRange and returns the full batchUpdateByDataFilter response.
# Values are entered as if typed by a user (USER_ENTERED).
api.write_to_sheet(
    spreadsheet_id,
    {
        'dataFilter': {'a1Range': 'Balances!A4:C4'},
        'majorDimension': 'ROWS',
        'values': [['2021-06-03', 'BTC', '0.02']],
    },
)
```

API errors are raised as `googleapiclient.errors.HttpError`. The `write_to_sheet` response is logged at `DEBUG`
level on the `sheets.client` logger.

See the Sheets API reference for
[`DataFilter`](https://developers.google.com/sheets/api/reference/rest/v4/DataFilter) and
[`DataFilterValueRange`](https://developers.google.com/sheets/api/reference/rest/v4/DataFilterValueRange).

## Development

```
python -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
ruff check .
ruff format --check .
pytest -v
```

The unit tests run offline: HTTP is served from JSON fixtures in [`tests/fixtures`](tests/fixtures), and the
google-auth service account flow is exercised with a key generated at test time.

[`tests/test_live.py`](tests/test_live.py) reads from a real spreadsheet and is skipped unless both of these are set:

| Variable | Meaning |
| --- | --- |
| `GOOGLE_SHEETS_CREDENTIALS` | Path to a service account JSON key file |
| `GOOGLE_SHEETS_SPREADSHEET_ID` | A spreadsheet shared with that service account |
| `GOOGLE_SHEETS_RANGE` | Optional A1 range to read; defaults to `A1:A1` |

CI ([`.github/workflows/ci.yml`](.github/workflows/ci.yml)) runs lint, the tests on Python 3.10 to 3.13 plus a run
against the minimum supported dependency versions, and a package build check.

## Releases

Versions follow [Semantic Versioning](https://semver.org/). The version is set in
[`pyproject.toml`](pyproject.toml).

To release, merge the version bump to `main`, then [draft a new release](https://github.com/mine-your-business/myb-google-sheets-api/releases)
with a tag such as `v1.1.0` targeting `main`. Publishing the release runs
[`.github/workflows/python-publish.yml`](.github/workflows/python-publish.yml), which builds the package and uploads
it to [PyPI](https://pypi.org/project/myb-google-sheets-api/) using
[trusted publishing](https://docs.pypi.org/trusted-publishers/). No API token is stored in GitHub; the PyPI project
must have this repository and workflow (environment `pypi`) registered as a trusted publisher.

## Changelog

### 1.1.0

- Requires Python 3.10 or newer (previously 3.7).
- Dependencies are now ranges instead of exact pins: `google-api-python-client>=2.181.0,<3` and
  `google-auth>=2.41.0,<3`. `google-auth-oauthlib` is no longer a dependency (it was never imported), and
  `google-auth-httplib2` is no longer pinned directly (it comes in through `google-api-python-client`).
- `write_to_sheet` no longer prints its response to stdout; it logs it at `DEBUG` on the `sheets.client` logger.
- The `SheetsApi` interface is unchanged.
