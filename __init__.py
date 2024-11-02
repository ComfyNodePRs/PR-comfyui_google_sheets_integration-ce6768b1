from .google_sheets_reader import GoogleSheetsReader
from .google_sheets_writer import GoogleSheetsWriter

NODE_CLASS_MAPPINGS = {
    "GoogleSheetsReader": GoogleSheetsReader,
    "GoogleSheetsWriter": GoogleSheetsWriter
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "GoogleSheetsReader": "Google Sheets Reader",
    "GoogleSheetsWriter": "Google Sheets Writer"
}