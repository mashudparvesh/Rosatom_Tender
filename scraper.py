import os
import re
import datetime
import requests

# 1. Configuration & URLs
TARGET_API_URL = "https://zakupki.rosatom.ru/WebServices/PublicService.svc/GetProcurements"
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbyQ2hf3Xd3vl7WC0mbwMWuBhpwxpChUVU1GofAaZafwQFiwL7ZiHz-8qfk8h0KIr9-Rcg/exec"

# Keywords in English and Russian for Rooppur & Bangladesh
KEYWORDS = [
    r"bangladesh", r"rooppur", r"ruppur",  # English keywords
    r"бангладеш", r"руппур"                 # Russian keywords (Бангладеш, Руппур)
]
KEYWORD_PATTERN = re.compile("|".join(KEYWORDS), re.IGNORECASE)

def scrape_and_send():
    print("Starting Rosatom Official API Scraper with new Web App URL...")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Content-Type": "application/json; charset=UTF-8",
        "Accept": "application/json, text/javascript, */*; q=0.01"
    }

    # Date Range: From 1st day of current month to today
    now = datetime.datetime.now()
    first_day_of_month = now.replace(day=1).strftime("%d.%m.%Y")
    today_date = now.strftime("%d.%m.%Y")
    
    print(f"Fetching tenders from {first_day_of_month} to {today_date} (PageSize: 100)...")

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
        print(f"API Response Status: {response.status_code}")
        
        if response.status_code != 200:
            print("Failed to fetch from Rosatom API.")
            return

        res_data = response.json()
        items = res_data.get("d", {}).get("Items", []) if isinstance(res_data.get("d"), dict) else res_data.get("Items", [])
        
        if not items and isinstance(res_data, list):
            items = res_data

        print(f"Total tenders retrieved from API: {len(items)}")
        
        extracted_tenders = []

        for item in items:
            subject = str(item.get("Subject", "") or item.get("subject", ""))
            proc_no = str(item.get("ProcurementNumber", "") or item.get("id", ""))
            pub_date = str(item.get("PublicationDate", "") or item.get("pubDate", ""))
            price = str(item.get("Price", "") or item.get("price", "0.00"))
            authority = str(item.get("CustomerName", "") or item.get("authority", "Rosatom"))
            deadline = str(item.get("SubmissionEndDate", "") or item.get("deadline", ""))

            # Keyword matching check (English & Russian)
            if KEYWORD_PATTERN.search(subject):
                extracted_tenders.append({
                    "procNo": proc_no,
                    "pubDate": pub_date,
                    "price": price,
                    "authority": authority,
                    "subject": subject,
                    "deadline": deadline
                })

        print(f"Matching tenders found after keyword filter: {len(extracted_tenders)}")

        if extracted_tenders:
            print("Sending matching tenders to Google Sheets Web App...")
            res = requests.post(WEB_APP_URL, json=extracted_tenders, timeout=30)
            print("Google Web App Response:", res.text)
        else:
            print("No matching tenders found for the current month period.")

    except Exception as e:
        print(f"Error during API execution: {str(e)}")

if __name__ == "__main__":
    scrape_and_send()
