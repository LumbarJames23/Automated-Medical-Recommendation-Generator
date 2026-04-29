import os
import re
import html

from app_config import REGION_DISPLAY_NAMES, REGION_SORT_ORDER


def remove_html_tags(text: str) -> str:
    unescaped = html.unescape(text)
    clean = re.sub(r"<.*?>", " ", unescaped)
    return re.sub(r"\s+", " ", clean).strip()


def region_verbose(region: str) -> str:
    return REGION_DISPLAY_NAMES.get(region.upper(), region)


def sort_regions(regions: list[str]) -> list[str]:
    return sorted(regions, key=lambda r: REGION_SORT_ORDER.get(r.upper(), 99))


def title_case_words(text: str) -> str:
    return " ".join(word.capitalize() for word in text.split())


def find_file_case_insensitive(folder: str, target_name: str) -> str | None:
    if not os.path.exists(folder):
        return None

    target_lower = target_name.lower()
    for filename in os.listdir(folder):
        if os.path.splitext(filename)[0].lower() == target_lower:
            return os.path.join(folder, filename)
    return None


def load_text_file(path: str) -> str | None:
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return None


def sanitize_filename(name: str) -> str:
    return re.sub(r'[<>:"/\\|?*]', '', name).strip()