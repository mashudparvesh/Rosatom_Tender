import os
import re
import datetime
import requests

# 1. Configuration & URLs
TARGET_API_URL = "https://zakupki.rosatom.ru/WebServices/PublicService.svc/GetProcurements"
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbwlcr0D8GE-RuljYCJhTRRQqkHq0u8xQ_J7BfQtiGkz4ymBL48-2hxVnVZq_ELSY7vYDw/exec"

# Keywords in English and Russian for Rooppur & Bangladesh
KEYWORDS = [
    r"bangladesh", r"rooppur", r"ruppur",  # English keywords
    r"бангладеш", r"руппур"                 # Russian keywords (Бангладеш, Руппур)
]
KEYWORD_PATTERN = re.compile("|".join(KEYWORDS), re.IGNORECASE)

def scrape_and_send():
    print("Starting Rosatom Dynamic API Scraper with multi-language support...")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Content-Type": "application/json; charset=UTF-8",
        "Accept": "application/json, text/javascript, */*; q=0.01"
    }

    # Calculate Current Month Date Range
    now = datetime.datetime.now()
    first_day_of_month = now.replace(day=1).strftime("%d.%m.%Y")
    today_date = now.strftime("%d.%m.%Y")
    
    print(f"Scanning current month tenders from {first_day_of_month} to {today_date} (PageSize: 100)...")

    # Payload matching Rosatom API with increased count (100 items per request)
    payload = {
        "params": {
            "PublicationDateFrom": first_day_of_month,
            "PublicationDateTo": today_date,
            "PageSize": 100,
            "PageIndex": 0
        }
    }
    
    try:
        response = requests.post(TARGET_API_URL, json=payload, headers=headers, timeout=30)
        print(f"Rosatom API Response Code: {response.status_code}")
        
        if response.status_code != 200:
            print("Failed to connect to Rosatom API service.")
            return

        res_data = response.json()
        items = res_data.get("d", {}).get("Items", []) if isinstance(res_data.get("d"), dict) else res_data.get("Items", [])
        
        if not items and isinstance(res_data, list):
            items = res_data

        print(f"Total fetched items for this month: {len(items)}")
        
        extracted_tenders = []

        for item in items:
            subject = str(item.get("Subject", "") or item.get("subject", ""))
            proc_no = str(item.get("ProcurementNumber", "") or item.get("id", ""))
            pub_date = str(item.get("PublicationDate", "") or item.get("pubDate", ""))
            price = str(item.get("Price", "") or item.get("price", "0.00"))
            authority = str(item.get("CustomerName", "") or item.get("authority", "Rosatom"))
            deadline = str(item.get("SubmissionEndDate", "") or item.get("deadline", ""))

            # Match both English and Russian keywords in Subject
            if KEYWORD_PATTERN.search(subject):
                extracted_tenders.append({
                    "procNo": proc_no,
                    "pubDate": pub_date,
                    "price": price,
                    "authority": authority,
                    "subject": subject,
                    "deadline": deadline
                })

        print(f"Found {len(extracted_tenders)} matching tenders after keyword filtering.")

        # Send matched tenders to Google Sheets Web App
        if extracted_tenders:
            print("Sending data to Google Sheets Web App...")
            res = requests.post(WEB_APP_URL, json=extracted_tenders, timeout=30)
            print("Response from Google Web App:", res.text)
        else:
            print("No matching tenders found for current month.")

    except Exception as e:
        print(f"Error while running scraper: {str(e)}")

if __name__ == "__main__":
    scrape_and_send()
