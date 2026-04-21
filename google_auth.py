import os
import pickle

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

from app_config import SCOPES, TOKEN_PATH, CREDENTIALS_PATH


def get_credentials():
    creds = None

    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, "rb") as t:
            creds = pickle.load(t)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_PATH, "wb") as t:
            pickle.dump(creds, t)

    return creds


def build_services():
    creds = get_credentials()
    calendar_service = build("calendar", "v3", credentials=creds)
    gmail_service = build("gmail", "v1", credentials=creds)
    return calendar_service, gmail_service