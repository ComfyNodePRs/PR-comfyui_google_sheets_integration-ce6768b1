import os
import pickle
import logging
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from cryptography.fernet import Fernet

# Konfiguracja logowania
def setup_logger():
    logger = logging.getLogger('GoogleSheetsPlugin')
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler = logging.FileHandler(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'google_sheets_plugin.log'))
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger

logger = setup_logger()

def log_message(message, level='info'):
    if level == 'debug':
        logger.debug(message)
    elif level == 'info':
        logger.info(message)
    elif level == 'warning':
        logger.warning(message)
    elif level == 'error':
        logger.error(message)
    elif level == 'critical':
        logger.critical(message)

def get_sheets_credentials(client_secrets_file):
    log_message("Getting credentials for Google Sheets", 'info')
    try:
        flow = InstalledAppFlow.from_client_secrets_file(
            client_secrets_file,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        log_message("Successfully created flow from client secrets file", 'debug')
    except Exception as e:
        log_message(f"Error creating flow: {str(e)}", 'error')
        raise
    
    creds = None
    token_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'token.pickle')
    key_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'encryption_key.key')
    
    if not os.path.exists(key_path):
        key = Fernet.generate_key()
        with open(key_path, 'wb') as key_file:
            key_file.write(key)
    else:
        with open(key_path, 'rb') as key_file:
            key = key_file.read()
    
    fernet = Fernet(key)
    
    if os.path.exists(token_path):
        log_message("Loading existing Google Sheets token", 'info')
        try:
            with open(token_path, 'rb') as token:
                encrypted_token = pickle.load(token)
                if isinstance(encrypted_token, bytes):
                    decrypted_token = fernet.decrypt(encrypted_token)
                    creds = pickle.loads(decrypted_token)
                else:
                    log_message("Stored Google Sheets token is not in the expected format. Regenerating.", 'warning')
                    creds = None
        except Exception as e:
            log_message(f"Error loading Google Sheets token: {str(e)}. Regenerating.", 'error')
            creds = None
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            log_message("Refreshing Google Sheets token", 'info')
            creds.refresh(Request())
        else:
            log_message("Getting new Google Sheets token", 'info')
            creds = flow.run_local_server(port=0)
        
        log_message("Saving new Google Sheets token", 'info')
        encrypted_token = fernet.encrypt(pickle.dumps(creds))
        with open(token_path, 'wb') as token:
            pickle.dump(encrypted_token, token)
    
    if not creds:
        log_message("Failed to obtain valid Google Sheets credentials", 'error')
        raise Exception("Failed to obtain valid Google Sheets credentials")
    
    log_message("Google Sheets credentials obtained successfully", 'info')
    log_message(f"Credential type: {type(creds).__name__}", 'debug')
    log_message(f"Token expiry: {creds.expiry}", 'debug')
    return creds