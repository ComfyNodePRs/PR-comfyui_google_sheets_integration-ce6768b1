import os
from .utils import get_sheets_credentials, log_message
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

class GoogleSheetsCleaner:
    @classmethod
    def INPUT_TYPES(s):
        default_secrets_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'client_secret.json')
        return {
            "required": {
                "spreadsheet_id": ("STRING", {"default": ""}),
                "range": ("STRING", {"default": ""}),
                "client_secrets_file": ("STRING", {"default": default_secrets_path}),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    FUNCTION = "clear_range"
    OUTPUT_NODE = True
    CATEGORY = "Utilities"
    
    def clear_range(self, spreadsheet_id, range, client_secrets_file):
        try:
            creds = get_sheets_credentials(client_secrets_file)
            service = build('sheets', 'v4', credentials=creds)
            
            sheet = service.spreadsheets()
            
            # Sprawdzamy format zakresu
            if '!' not in range:
                raise ValueError("Range must be in format 'Sheet!Range' (e.g., 'Sheet1!A2:B' or 'Sheet1!A2:A')")
            
            sheet_name, column_range = range.split('!')
            
            # Sprawdzamy czy zakres ma format z dwukropkiem
            if ':' in column_range:
                # Zakres jest już określony (np. A2:B)
                full_range = f"{sheet_name}!{column_range}"
            else:
                # Dobieramy zakres do końca arkusza (np. A2 -> A2:A1000)
                full_range = f"{sheet_name}!{column_range}:1000"
            
            # Najpierw pobieramy aktualne wymiary arkusza
            sheet_metadata = sheet.get(
                spreadsheetId=spreadsheet_id,
                ranges=[full_range],
                fields='sheets.properties'
            ).execute()
            
            # Czyścimy wartości w zakresie
            result = sheet.values().clear(
                spreadsheetId=spreadsheet_id,
                range=full_range
            ).execute()
            
            cleared_rows = result.get('clearedRange', 'unknown range')
            log_message(f"Cleared range: {cleared_rows}", 'info')
            
            # Resetujemy cache w GoogleSheetsWriter jeśli istnieje
            if hasattr(self, '_last_empty_row_cache'):
                self._last_empty_row_cache = {}
            
            return ([f"Successfully cleared range: {cleared_rows}"],)
            
        except HttpError as e:
            log_message(f"An HTTP error occurred: {e.resp.status} {e.content}", 'error')
            return ([f'An HTTP error occurred: {e.resp.status} {e.content}'],)
        except Exception as e:
            log_message(f"An error occurred: {str(e)}", 'error')
            log_message(f"Error type: {type(e).__name__}", 'debug')
            log_message(f"Error args: {e.args}", 'debug')
            return ([f'An error occurred: {str(e)}'],)