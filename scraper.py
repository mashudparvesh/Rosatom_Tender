import os
import re
import requests
from bs4 import BeautifulSoup
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# 1. Configuration & Keywords
TARGET_URL = "https://zakupki.rosatom.ru/?link=procurements"
KEYWORDS = [r"\bangladesh\b", r"\brooppur\b", r"\bruppur\b"]
KEYWORD_PATTERN = re.compile("|".join(KEYWORDS), re.IGNORECASE)

# 2. Authenticate with Google Sheets using GitHub Secrets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")

# If running via GitHub Secrets, write credentials to temp file or load directly
import json
creds_dict = json.loads(creds_json)
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

# Open your Master Tracker Spreadsheet
spreadsheet = client.open("Tender & Procurement Master Tracker")
sheet = spreadsheet.worksheet("Tender Master Pipeline")

def sync_tenders():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    response = requests.get(TARGET_URL, headers=headers)
    if response.status_code != 200:
        print(f"Failed to fetch portal: {response.status_code}")
        return

    soup = BeautifulSoup(response.text, "html.parser")
    
    # Get existing Procurement Numbers from Column A to prevent duplicates
    existing_proc_nos = sheet.col_values(1) # Column A

    # Parse procurement rows from Rosatom portal structure
    # (Adjust CSS selector based on exact table rows class in portal)
    rows = soup.find_all("tr")
    
    new_count = 0
    for row in rows:
        try:
            cols = row.find_all("td")
            if len(cols) < 6:
                continue
            
            # Extract fields based on Rosatom table columns
            # Col: [Completion Date, Publication Date, Price, Procurement Number, Authority, Subject, Region, Status]
            deadline = cols[0].get_text(strip=True)
            pub_date = cols[1].get_text(strip=True)
            price = cols[2].get_text(strip=True)
            proc_no = cols[3].get_text(strip=True)
            authority = cols[4].get_text(strip=True)
            subject = cols[5].get_text(strip=True)

            # Check keyword match in Subject of Contract
            if KEYWORD_PATTERN.search(subject):
                if proc_no and proc_no not in existing_proc_nos:
                    # Append new row to Google Sheet
                    new_row = [
                        proc_no,
                        pub_date,
                        price,
                        authority,
                        subject,
                        deadline,
                        "In Review",
                        "GitHub-Bot",
                        "Draft"
                    ]
                    sheet.append_row(new_row)
                    existing_proc_nos.append(proc_no)
                    new_count += 1
                    print(f"[Added] Procurement No: {proc_no} - {subject}")
        except Exception as e:
            continue

    print(f"Sync Finished. Total new tenders added: {new_count}")

if __name__ == "__main__":
    sync_tenders()
