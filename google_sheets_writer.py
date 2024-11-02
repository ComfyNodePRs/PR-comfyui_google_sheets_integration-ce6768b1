import os
import time
from .utils import get_sheets_credentials, log_message
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

class GoogleSheetsWriter:
    _last_empty_row_cache = {}
    _last_request_time = 0
    _requests_in_current_minute = 0
    _MIN_REQUEST_INTERVAL = 1.1  # seconds between requests
    _MAX_REQUESTS_PER_MINUTE = 55  # keeping buffer from 60 limit
    
    @classmethod
    def INPUT_TYPES(s):
        default_secrets_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'client_secret.json')
        return {
            "required": {
                "spreadsheet_id": ("STRING", {"default": ""}),
                "range": ("STRING", {"default": ""}),
                "client_secrets_file": ("STRING", {"default": default_secrets_path}),
                "STORE": ("STRING", {"multiline": True})
            }
        }
    
    RETURN_TYPES = ("STRING",)
    FUNCTION = "write_sheet"
    OUTPUT_NODE = True
    CATEGORY = "Utilities"
    OUTPUT_IS_LIST = (True,)

    def wait_for_rate_limit(self):
        """Zarządzanie limitami zapytań"""
        current_time = time.time()
        
        # Reset licznika po minucie
        if current_time - self._last_request_time >= 60:
            self._requests_in_current_minute = 0
            self._last_request_time = current_time
        
        # Czekaj jeśli przekroczono limit na minutę
        if self._requests_in_current_minute >= self._MAX_REQUESTS_PER_MINUTE:
            sleep_time = 60 - (current_time - self._last_request_time)
            if sleep_time > 0:
                log_message(f"Rate limit reached, waiting {sleep_time:.2f} seconds...", 'info')
                time.sleep(sleep_time)
                self._requests_in_current_minute = 0
                self._last_request_time = time.time()
        
        # Minimum czasu między zapytaniami
        time_since_last_request = current_time - self._last_request_time
        if time_since_last_request < self._MIN_REQUEST_INTERVAL:
            time.sleep(self._MIN_REQUEST_INTERVAL - time_since_last_request)
        
        self._last_request_time = time.time()
        self._requests_in_current_minute += 1

    def ensure_sheet_size(self, sheet, spreadsheet_id, sheet_name, target_column, target_row):
        try:
            self.wait_for_rate_limit()
            metadata = sheet.get(spreadsheetId=spreadsheet_id, fields='sheets.properties').execute()
            
            sheet_properties = next(
                (s['properties'] for s in metadata['sheets'] if s['properties']['title'] == sheet_name),
                None
            )
            
            if not sheet_properties:
                raise ValueError(f"Sheet '{sheet_name}' not found")
            
            current_rows = sheet_properties.get('gridProperties', {}).get('rowCount', 0)
            current_cols = sheet_properties.get('gridProperties', {}).get('columnCount', 0)
            
            def column_to_number(col_str):
                num = 0
                for c in col_str:
                    num = num * 26 + (ord(c.upper()) - ord('A') + 1)
                return num
            
            target_col_num = column_to_number(target_column)
            
            requests = []
            if target_row > current_rows:
                requests.append({
                    'appendDimension': {
                        'sheetId': sheet_properties['sheetId'],
                        'dimension': 'ROWS',
                        'length': target_row - current_rows
                    }
                })
            
            if target_col_num > current_cols:
                requests.append({
                    'appendDimension': {
                        'sheetId': sheet_properties['sheetId'],
                        'dimension': 'COLUMNS',
                        'length': target_col_num - current_cols
                    }
                })
            
            if requests:
                self.wait_for_rate_limit()
                sheet.batchUpdate(
                    spreadsheetId=spreadsheet_id,
                    body={'requests': requests}
                ).execute()
                log_message(f"Sheet extended to accommodate row {target_row} and column {target_column}", 'info')
                
            return True
            
        except Exception as e:
            log_message(f"Error ensuring sheet size: {str(e)}", 'error')
            return False

    def parse_cell_reference(self, cell_ref):
        column = ''.join(c for c in cell_ref if c.isalpha())
        row = ''.join(c for c in cell_ref if c.isdigit())
        return column, int(row) if row else None

    def get_next_row(self, sheet, spreadsheet_id, sheet_name, column, specified_row=None):
        if specified_row is not None:
            return specified_row
            
        cache_key = f"{spreadsheet_id}_{sheet_name}_{column}"
        
        if cache_key not in self._last_empty_row_cache:
            self.wait_for_rate_limit()
            range_name = f"{sheet_name}!{column}:{column}"
            result = sheet.values().get(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                majorDimension='ROWS'
            ).execute()
            
            values = result.get('values', [])
            self._last_empty_row_cache[cache_key] = len(values) + 1
        else:
            self._last_empty_row_cache[cache_key] += 1
            
        return self._last_empty_row_cache[cache_key]

    def write_sheet(self, spreadsheet_id, range, client_secrets_file, STORE):
        try:
            if '!' not in range:
                raise ValueError("Range must be in format 'Sheet!Column' or 'Sheet!CellReference'")
            
            sheet_name, cell_reference = range.split('!')
            
            if not hasattr(self, '_service'):
                creds = get_sheets_credentials(client_secrets_file)
                self._service = build('sheets', 'v4', credentials=creds)
            
            sheet = self._service.spreadsheets()
            
            column, specified_row = self.parse_cell_reference(cell_reference)
            next_row = self.get_next_row(sheet, spreadsheet_id, sheet_name, column, specified_row)
            
            self.ensure_sheet_size(sheet, spreadsheet_id, sheet_name, column, next_row)
            
            self.wait_for_rate_limit()
            body = {'values': [[STORE]]}
            result = sheet.values().update(
                spreadsheetId=spreadsheet_id,
                range=f"{sheet_name}!{column}{next_row}",
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()
            
            updated_cells = result.get('updatedCells')
            log_message(f"Data written to sheet. Updated {updated_cells} cell.", 'info')
            
            return ([f"Data successfully written to {sheet_name}!{column}{next_row}."],)
            
        except HttpError as e:
            self._last_empty_row_cache = {}
            if e.resp.status == 429:  # Rate limit error
                log_message("Rate limit exceeded, retrying with longer delay...", 'warning')
                time.sleep(2)  # Dodatkowe opóźnienie
                return self.write_sheet(spreadsheet_id, range, client_secrets_file, STORE)
            log_message(f"An HTTP error occurred: {e.resp.status} {e.content}", 'error')
            return ([f'An HTTP error occurred: {e.resp.status} {e.content}'],)
        except Exception as e:
            self._last_empty_row_cache = {}
            log_message(f"An error occurred: {str(e)}", 'error')
            log_message(f"Error type: {type(e).__name__}", 'debug')
            log_message(f"Error args: {e.args}", 'debug')
            return ([f'An error occurred: {str(e)}'],)
