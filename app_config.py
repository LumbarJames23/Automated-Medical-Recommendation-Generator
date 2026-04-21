import json
import os
import sys
from typing import Any

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly", "https://www.googleapis.com/auth/gmail.compose"]

TOKEN_PATH = "token.pickle"
CREDENTIALS_PATH = "credentialsCS2.json"

def get_base_dir() -> str:
    """
    Return the directory the app should treat as its runtime root.

    In normal Python runs, this is the directory containing this file.
    In PyInstaller builds, this is the directory containing the executable.
    """
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


BASE_DIR = get_base_dir()


def load_json(filename: str) -> dict[str, Any]:
    path = os.path.join(BASE_DIR, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing configuration file: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


SETTINGS = load_json("settings.json")
RECOMMENDATION_RULES = load_json("recommendations.json")


def build_path(relative_name: str) -> str:
    return os.path.join(BASE_DIR, relative_name)


CALENDAR_ID = SETTINGS["calendar_id"]

CLINIC_NAME = SETTINGS["clinic_name"]
PHONE = SETTINGS["phone"]
WELCOME_EMAIL = SETTINGS["welcome_email"]
OFFICE_EMAIL = SETTINGS["office_email"]
COORDINATOR_EMAIL = SETTINGS["coordinator_email"]
TIMEZONE = SETTINGS["timezone"]

TEMPLATE_DIR = build_path(SETTINGS["template_dir"])
OUTPUT_ROOT = build_path(SETTINGS["output_root"])
EXERCISES_DIR = build_path(SETTINGS["exercises_dir"])
SUPPLEMENTS_DIR = build_path(SETTINGS["supplements_dir"])
HYPERLINKS_DIR = build_path(SETTINGS["hyperlinks_dir"])

IMAGING_DISPLAY_NAMES = SETTINGS["imaging_display_names"]
REGION_DISPLAY_NAMES = SETTINGS["region_display_names"]
REGION_SORT_ORDER = SETTINGS["region_sort_order"]

EMAIL_TEMPLATE_DIR = build_path("email_templates")
NON_SURGICAL_TEMPLATE = os.path.join(EMAIL_TEMPLATE_DIR, "non_surgical_header.html")
SURGICAL_TEMPLATE = os.path.join(EMAIL_TEMPLATE_DIR, "surgical_header.html")