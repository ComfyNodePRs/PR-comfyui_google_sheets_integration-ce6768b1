import os
from .utils import get_sheets_credentials, log_message
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

class GoogleSheetsWriter:
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

    def write_sheet(self, spreadsheet_id, range, client_secrets_file, STORE):
        try:
            creds = get_sheets_credentials(client_secrets_file)
            service = build('sheets', 'v4', credentials=creds)
            
            sheet = service.spreadsheets()
            
            # Rozdzielamy arkusz i kolumnę
            sheet_name, column = range.split('!')
            
            # Pobieramy dane z całej kolumny
            result = sheet.values().get(spreadsheetId=spreadsheet_id, range=f"{sheet_name}!{column}:{column}").execute()
            values = result.get('values', [])
            
            # Znajdujemy pierwszą pustą komórkę
            first_empty_row = len(values) + 1
            
            # Przygotowujemy dane do zapisu (cała zawartość STORE jako jedna komórka)
            body = {
                'values': [[STORE]]  # Cała zawartość STORE w jednej komórce
            }
            
            # Zapisujemy dane
            result = sheet.values().update(
                spreadsheetId=spreadsheet_id, 
                range=f"{sheet_name}!{column}{first_empty_row}",
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()
            
            updated_cells = result.get('updatedCells')
            log_message(f"Data written to sheet. Updated {updated_cells} cell.", 'info')
            
            return (f"Data successfully written to {sheet_name}!{column}{first_empty_row}.",)
        
        except HttpError as e:
            log_message(f"An HTTP error occurred: {e.resp.status} {e.content}", 'error')
            return (f'An HTTP error occurred: {e.resp.status} {e.content}',)
        except Exception as e:
            log_message(f"An error occurred: {str(e)}", 'error')
            log_message(f"Error type: {type(e).__name__}", 'debug')
            log_message(f"Error args: {e.args}", 'debug')
            return (f'An error occurred: {str(e)}',)