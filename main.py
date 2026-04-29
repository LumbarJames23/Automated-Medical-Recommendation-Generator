import traceback
import sys
from datetime import datetime

from app_config import CALENDAR_ID
from google_auth import build_services
from command_line_interface import parse_args
from google_calendar_events_pull import get_user_date_range, get_events
from event_parser import parse_event_data
from document_generator import generate_documents
from create_gmail_draft import create_gmail_draft


def _resolve_date_range(args) -> tuple[str, str]:
    if args.today:
        return get_user_date_range("", "")
    if args.start or args.end:
        return get_user_date_range(args.start or "", args.end or "")
    return get_user_date_range()


def main():
    args = parse_args()
    calendar_service, gmail_service = build_services()
    start, end = _resolve_date_range(args)

    events = get_events(calendar_service, CALENDAR_ID, start, end)
    print(f"Found {len(events)} events")

    for ev in events:
        title = ev.get("summary", "NO TITLE")

        try:
            parsed = parse_event_data(ev)
            if not parsed:
                continue

            event_start = ev["start"]
            date = datetime.fromisoformat(event_start.get("dateTime", event_start.get("date")))
            generate_documents(date, parsed)
            create_gmail_draft(gmail_service, parsed, date)

        except Exception as e:
            print("\nERROR - Failed processing event:")
            print(f"  TITLE: {title}")
            print(f"  REASON: {e}\n")
            traceback.print_exc()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("\n--- A fatal error occurred ---")
        traceback.print_exc()
        input("\nPress Enter to exit...")
        sys.exit(1)
    else:
        input("\nRecommendations completed. Press Enter to exit...")