from datetime import datetime


def _prompt_for_date_inputs() -> tuple[str, str]:
    start_input = input("Enter start date (MM/DD/YYYY) or press Enter for today: ")
    end_input = input("Enter end date (MM/DD/YYYY) or press Enter for same day: ")
    return start_input, end_input


def _parse_date_range(start_input: str, end_input: str) -> tuple[datetime, datetime]:
    start = datetime.today() if not start_input else datetime.strptime(start_input, "%m/%d/%Y")
    end = datetime.strptime(end_input, "%m/%d/%Y") if end_input else start
    end = end.replace(hour=23, minute=59, second=59)
    return start, end


def get_user_date_range(start_input: str | None = None, end_input: str | None = None) -> tuple[str, str]:
    if start_input is None or end_input is None:
        start_input, end_input = _prompt_for_date_inputs()

    start, end = _parse_date_range(start_input, end_input)
    return start.isoformat() + "Z", end.isoformat() + "Z"


def get_events(calendar_service, calendar_id: str, start: str, end: str) -> list:
    events_query = calendar_service.events().list(
        calendarId=calendar_id,
        timeMin=start,
        timeMax=end,
        singleEvents=True,
        orderBy="startTime",
    )
    response = events_query.execute()
    return response.get("items", [])