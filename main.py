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


def main():
    args = parse_args()
    calendar_service, gmail_service = build_services()

    if args.today:
        start, end = get_user_date_range("", "")
    elif args.start or args.end:
        start, end = get_user_date_range(args.start or "", args.end or "")
    else:
        start, end = get_user_date_range()

    events = get_events(calendar_service, CALENDAR_ID, start, end)
    print(f"Found {len(events)} events")

    for ev in events:
        title = ev.get("summary", "NO TITLE")

        try:
            parsed = parse_event_data(ev)
            if not parsed:
                continue

            date = datetime.fromisoformat(
                ev["start"].get("dateTime", ev["start"].get("date"))
            )
            generate_documents(date, parsed)
            create_gmail_draft(gmail_service, parsed, date)

        except Exception as e:
            print("\nERROR - Failed processing event:")
            print(f"  TITLE: {title}")
            print(f"  REASON: {str(e)}\n")
            traceback.print_exc()
            continue


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