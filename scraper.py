import os
import re
import json
import requests
from bs4 import BeautifulSoup

# 1. Configuration
TARGET_URL = "https://zakupki.rosatom.ru/?link=procurements"
WEB_APP_URL = os.environ.get("GOOGLE_WEB_APP_URL")

KEYWORDS = [r"\bangladesh\b", r"\brooppur\b", r"\bruppur\b"]
KEYWORD_PATTERN = re.compile("|".join(KEYWORDS), re.IGNORECASE)

def scrape_and_send():
    print("Starting Rosatom Tender Scraper...")
    
    if not WEB_APP_URL:
        print("ERROR: GOOGLE_WEB_APP_URL secret is missing in GitHub Actions!")
        return

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(TARGET_URL, headers=headers, timeout=30)
        print(f"Portal Response Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Failed to fetch portal. Status: {response.status_code}")
            return

        soup = BeautifulSoup(response.text, "html.parser")
        rows = soup.find_all("tr")
        print(f"Total rows found on page: {len(rows)}")
        
        extracted_tenders = []

        for row in rows:
            try:
                cols = row.find_all("td")
                if len(cols) < 6:
                    continue
                
                deadline = cols[0].get_text(strip=True)
                pub_date = cols[1].get_text(strip=True)
                price = cols[2].get_text(strip=True)
                proc_no = cols[3].get_text(strip=True)
                authority = cols[4].get_text(strip=True)
                subject = cols[5].get_text(strip=True)

                # Check keyword match in Subject of Contract
                if KEYWORD_PATTERN.search(subject):
                    extracted_tenders.append({
                        "procNo": proc_no,
                        "pubDate": pub_date,
                        "price": price,
                        "authority": authority,
                        "subject": subject,
                        "deadline": deadline
                    })
            except Exception as ex:
                continue

        print(f"Found {len(extracted_tenders)} matching tenders matching keywords.")

        # Send to Google Apps Script Web App
        if extracted_tenders:
            print("Sending data to Google Sheets Web App...")
            res = requests.post(WEB_APP_URL, json=extracted_tenders, timeout=30)
            print("Response from Google Web App:", res.text)
        else:
            print("No matching tenders found at this moment to sync.")

    except Exception as e:
        print(f"An error occurred during scraping: {str(e)}")

if __name__ == "__main__":
    scrape_and_send()
