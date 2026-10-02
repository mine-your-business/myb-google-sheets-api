import logging

from google.oauth2 import service_account
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

READ_WRITE_SCOPES = ['https://www.googleapis.com/auth/spreadsheets']


class SheetsApi:
    def __init__(self, credentials_json):
        creds = self._get_credentials(credentials_json)
        self._sheets_service = build('sheets', 'v4', credentials=creds, cache_discovery=False)
        self._spreadsheets = self._sheets_service.spreadsheets()

    def _get_credentials(self, credentials_json):
        return service_account.Credentials.from_service_account_info(credentials_json, scopes=READ_WRITE_SCOPES)

    def read_from_sheet(self, spreadsheet_id, data_filter_value_range):
        batch_get_values_by_data_filter_request_body = {
            'value_render_option': 'FORMATTED_VALUE',
            'data_filters': [data_filter_value_range],
            # This is ignored if value_render_option is FORMATTED_VALUE
            'date_time_render_option': 'SERIAL_NUMBER',
        }
        result = (
            self._spreadsheets.values()
            .batchGetByDataFilter(spreadsheetId=spreadsheet_id, body=batch_get_values_by_data_filter_request_body)
            .execute()
        )
        return result.get('valueRanges', [])

    def write_to_sheet(self, spreadsheet_id, data_filter_value_range):
        batch_update_values_by_data_filter_request_body = {
            'include_values_in_response': False,
            'data': [data_filter_value_range],
            'value_input_option': 'USER_ENTERED',
        }
        result = (
            self._spreadsheets.values()
            .batchUpdateByDataFilter(spreadsheetId=spreadsheet_id, body=batch_update_values_by_data_filter_request_body)
            .execute()
        )
        logger.debug('batchUpdateByDataFilter response: %s', result)
        return result
