import os
import json
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def get_sheet():
    # Load credentials from environment variable (production)
    # or from file (local development)
    creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON")

    if creds_json:
        creds_dict = json.loads(creds_json)
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    else:
        creds = Credentials.from_service_account_file(
            "credentials.json", scopes=SCOPES
        )

    client = gspread.authorize(creds)
    sheet = client.open_by_key(os.getenv("GOOGLE_SHEET_ID"))
    return sheet.sheet1

def append_lead(session_id: str, name: str = None, email: str = None,
                phone: str = None, interest: str = None):
    try:
        sheet = get_sheet()
        all_rows = sheet.get_all_values()

        for i, row in enumerate(all_rows[1:], start=2):
            if row and row[1] == session_id:
                sheet.update(f"A{i}:G{i}", [[
                    row[0], session_id,
                    name or row[2], email or row[3],
                    phone or row[4], interest or row[5],
                    row[6]
                ]])
                print(f"DEBUG SHEETS: Updated lead for session {session_id[:12]}")
                return

        next_id = len(all_rows)
        sheet.append_row([
            next_id, session_id,
            name or "", email or "",
            phone or "", interest or "",
            datetime.utcnow().strftime("%Y-%m-%d %H:%M")
        ])
        print(f"DEBUG SHEETS: New lead saved — {name} / {email}")

    except Exception as e:
        print(f"DEBUG SHEETS ERROR: {e}")