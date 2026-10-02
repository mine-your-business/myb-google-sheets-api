"""Read-only smoke test against the real Google Sheets API.

Skipped unless both environment variables are set:

- GOOGLE_SHEETS_CREDENTIALS: path to a service account JSON key file
- GOOGLE_SHEETS_SPREADSHEET_ID: a spreadsheet shared with that service account

GOOGLE_SHEETS_RANGE optionally sets the A1 range read (default ``A1:A1``).
"""

import json
import os
from pathlib import Path

import pytest

from sheets import SheetsApi

CREDENTIALS_PATH = os.environ.get('GOOGLE_SHEETS_CREDENTIALS')
SPREADSHEET_ID = os.environ.get('GOOGLE_SHEETS_SPREADSHEET_ID')

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(
        not (CREDENTIALS_PATH and SPREADSHEET_ID),
        reason='GOOGLE_SHEETS_CREDENTIALS and GOOGLE_SHEETS_SPREADSHEET_ID not set',
    ),
]


def test_read_from_sheet_live():
    api = SheetsApi(json.loads(Path(CREDENTIALS_PATH).read_text()))

    value_ranges = api.read_from_sheet(
        SPREADSHEET_ID,
        {'a1Range': os.environ.get('GOOGLE_SHEETS_RANGE', 'A1:A1')},
    )

    assert isinstance(value_ranges, list)
