from datetime import datetime


def get_user_date_range(start_input: str | None = None, end_input: str | None = None):
    if start_input is None:
        start_input = input("Enter start date (MM/DD/YYYY) or press Enter for today: ")
    if end_input is None:
        end_input = input("Enter end date (MM/DD/YYYY) or press Enter for same day: ")

    start = datetime.today() if not start_input else datetime.strptime(start_input, "%m/%d/%Y")
    end = datetime.strptime(end_input, "%m/%d/%Y") if end_input else start
    end = end.replace(hour=23, minute=59, second=59)

    return start.isoformat() + "Z", end.isoformat() + "Z"


def get_events(calendar_service, calendar_id: str, start: str, end: str):
    return (
        calendar_service.events()
        .list(
            calendarId=calendar_id,
            timeMin=start,
            timeMax=end,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
        .get("items", [])
    )