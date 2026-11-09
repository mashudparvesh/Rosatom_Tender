import os
import re
import datetime
import requests

WEB_APP_URL = "https://script.google.com/macros/s/AKfycbyQ2hf3Xd3vl7WC0mbwMWuBhpwxpChUVU1GofAaZafwQFiwL7ZiHz-8qfk8h0KIr9-Rcg/exec"
SEARCH_URL = "https://zakupki.rosatom.ru/WebServices/PublicService.svc/GetProcurements"

KEYWORDS = [r"bangladesh", r"rooppur", r"ruppur", r"бангладеш", r"руппур"]
KEYWORD_PATTERN = re.compile("|".join(KEYWORDS), re.IGNORECASE)

def scrape_and_send():
    print("Starting direct procurement search...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Content-Type": "application/json; charset=UTF-8"
    }

    # Fetching latest 300 procurements from portal without tight date restriction to ensure no missing tender
    payload = {
        "params": {
            "PageSize": 300,
            "PageIndex": 0
        }
    }
    
    try:
        response = requests.post(SEARCH_URL, json=payload, headers=headers, timeout=30)
        print(f"Rosatom API Response Status: {response.status_code}")
        
        if response.status_code != 200:
            print("API response failed.")
            return

        res_data = response.json()
        items = res_data.get("d", {}).get("Items", []) if isinstance(res_data.get("d"), dict) else res_data.get("Items", [])
        
        if not items and isinstance(res_data, list):
            items = res_data

        print(f"Total tenders fetched from portal: {len(items)}")
        
        extracted_tenders = []

        for item in items:
            subject = str(item.get("Subject", "") or item.get("subject", ""))
            proc_no = str(item.get("ProcurementNumber", "") or item.get("id", ""))
            pub_date = str(item.get("PublicationDate", "") or item.get("pubDate", ""))
            price = str(item.get("Price", "") or item.get("price", "0.00"))
            authority = str(item.get("CustomerName", "") or item.get("authority", "Rosatom"))
            deadline = str(item.get("SubmissionEndDate", "") or item.get("deadline", ""))

            if KEYWORD_PATTERN.search(subject):
                print(f"-> Matched Tender: {proc_no} | {subject[:50]}...")
                extracted_tenders.append({
                    "procNo": proc_no,
                    "pubDate": pub_date,
                    "price": price,
                    "authority": authority,
                    "subject": subject,
                    "deadline": deadline
                })

        print(f"Total matching tenders found: {len(extracted_tenders)}")

        if extracted_tenders:
            print("Posting matching tenders to Apps Script Web App...")
            res = requests.post(WEB_APP_URL, json=extracted_tenders, timeout=30)
            print("Apps Script Response:", res.text)
        else:
            print("No matching tenders found in the fetched list.")

    except Exception as e:
        print(f"Execution Error: {str(e)}")

if __name__ == "__main__":
    scrape_and_send()
