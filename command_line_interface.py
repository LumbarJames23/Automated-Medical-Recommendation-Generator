import argparse

def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate recommendation documents and Gmail drafts from Google Calendar events."
    )
    parser.add_argument("--start", help="Start date in MM/DD/YYYY")
    parser.add_argument("--end", help="End date in MM/DD/YYYY")
    parser.add_argument("--today", action="store_true", help="Use today's date")
    return parser.parse_args()