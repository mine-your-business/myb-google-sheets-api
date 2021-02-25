from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2 import service_account

READ_WRITE_SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
# READ_ONLY_SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

class SheetsApi:

    def __init__(self, credentials_json):
        creds = self._get_credentials(credentials_json)
        self._sheets_service = build('sheets', 'v4', credentials=creds, cache_discovery=False)
        self._spreadsheets = self._sheets_service.spreadsheets()

    def _get_credentials(self, credentials_json):
        creds = service_account.Credentials.from_service_account_info(
            credentials_json, 
            scopes=READ_WRITE_SCOPES
        )

        return creds

    def read_from_sheet(self, spreadsheet_id, data_filter_value_range):
        batch_get_values_by_data_filter_request_body = {
            'value_render_option': 'FORMATTED_VALUE',
            'data_filters': [data_filter_value_range],
            # This is ignored if value_render_option is FORMATTED_VALUE
            'date_time_render_option': 'SERIAL_NUMBER'
        }
        result = self._spreadsheets.values().batchGetByDataFilter(
            spreadsheetId=spreadsheet_id,
            body=batch_get_values_by_data_filter_request_body
        ).execute()
        value_ranges = result.get('valueRanges', [])
        return value_ranges

    def write_to_sheet(self, spreadsheet_id, data_filter_value_range):
        batch_update_values_by_data_filter_request_body = {
            'include_values_in_response': False,
            'data': [data_filter_value_range],
            'value_input_option': 'USER_ENTERED'
        }
        result = self._spreadsheets.values().batchUpdateByDataFilter(
            spreadsheetId=spreadsheet_id,
            body=batch_update_values_by_data_filter_request_body
        ).execute()
        print(result)
        return result