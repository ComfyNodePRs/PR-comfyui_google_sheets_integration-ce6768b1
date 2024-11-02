import os
from .utils import get_sheets_credentials, log_message
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

class GoogleSheetsReader:
    @classmethod
    def INPUT_TYPES(s):
        default_secrets_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'client_secret.json')
        return {
            "required": {
                "spreadsheet_id": ("STRING", {"default": ""}),
                "range": ("STRING", {"default": ""}),
                "client_secrets_file": ("STRING", {"default": default_secrets_path})
            }
        }
    
    RETURN_TYPES = ("STRING",)
    FUNCTION = "read_sheet"
    OUTPUT_NODE = True
    CATEGORY = "Utilities"
    OUTPUT_IS_LIST = (True,)

    def read_sheet(self, spreadsheet_id, range, client_secrets_file):
        try:
            creds = get_sheets_credentials(client_secrets_file)
            service = build('sheets', 'v4', credentials=creds)
            
            sheet = service.spreadsheets()
            result = sheet.values().get(spreadsheetId=spreadsheet_id, range=range).execute()
            values = result.get('values', [])
            
            if not values:
                log_message("No data found in the specified range", 'warning')
                return ([],)
            else:
                log_message(f"Successfully read {len(values)} rows of data", 'info')
                return ([','.join(map(str, row)) for row in values],)
        
        except HttpError as e:
            log_message(f"An HTTP error occurred: {e.resp.status} {e.content}", 'error')
            return ([f'An HTTP error occurred: {e.resp.status} {e.content}'],)
        except Exception as e:
            log_message(f"An error occurred: {str(e)}", 'error')
            log_message(f"Error type: {type(e).__name__}", 'debug')
            log_message(f"Error args: {e.args}", 'debug')
            return ([f'An error occurred: {str(e)}'],)