# ComfyUI Google Sheets Integration

This custom node allows integration between ComfyUI and Google Sheets, enabling reading from and writing to Google Sheets directly from ComfyUI workflows.

## Installation

1. Clone this repository into the `custom_nodes` directory of your ComfyUI installation:
   ```
   git clone https://github.com/your-username/comfyui_google_sheets_integration.git
   ```

2. Install the required dependencies:
   ```
   pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client cryptography
   ```

3. Set up Google Sheets API and obtain the `client_secret.json` file. Place this file in the `comfyui_google_sheets_integration` directory.

## Usage

### Google Sheets Reader

This node allows you to read data from a Google Sheets spreadsheet.

Inputs:
- `spreadsheet_id`: The ID of the Google Sheets spreadsheet.
- `range`: The range of cells to read (e.g., "Sheet1!A1:B10").
- `client_secrets_file`: Path to your `client_secret.json` file.

Output:
- A list of strings, where each string represents a row from the spreadsheet.

### Google Sheets Writer

This node allows you to write data to a Google Sheets spreadsheet.

Inputs:
- `spreadsheet_id`: The ID of the Google Sheets spreadsheet.
- `range`: The range where the data should be appended.
- `client_secrets_file`: Path to your `client_secret.json` file.
- `STORE`: The data to be written, as a multi-line string with comma-separated values.

Output:
- A string indicating the success or failure of the operation.

## Notes

- Ensure that your Google Sheets API credentials have the necessary permissions for reading and writing.
- The first time you use these nodes, you'll need to authorize the application in your web browser.

## Troubleshooting

If you encounter any issues, check the `google_sheets_plugin.log` file in the plugin directory for detailed error messages.