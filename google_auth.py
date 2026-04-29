import os
import pickle

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build, Resource

from app_config import SCOPES, TOKEN_PATH, CREDENTIALS_PATH


def _load_cached_credentials() -> Credentials | None:
    if not os.path.exists(TOKEN_PATH):
        return None
    with open(TOKEN_PATH, "rb") as t:
        return pickle.load(t)


def _refresh_or_create_credentials(creds: Credentials | None) -> Credentials:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        return creds
    flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
    return flow.run_local_server(port=0)


def _save_credentials(creds: Credentials) -> None:
    with open(TOKEN_PATH, "wb") as t:
        pickle.dump(creds, t)


def get_credentials() -> Credentials:
    creds = _load_cached_credentials()
    if not creds or not creds.valid:
        creds = _refresh_or_create_credentials(creds)
        _save_credentials(creds)
    return creds


def build_services() -> tuple[Resource, Resource]:
    creds = get_credentials()
    calendar_service = build("calendar", "v3", credentials=creds)
    gmail_service = build("gmail", "v1", credentials=creds)
    return calendar_service, gmail_service
