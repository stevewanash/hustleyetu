import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from typing import List, Dict
import urllib3

# Suppress the InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://www.parliament.go.ke"

async def get_bills() -> List[Dict[str, str]]:
    """
    Scrapes the Kenyan Parliament website for bills.
    Returns a list of dicts: {'title': str, 'url': str}
    """
    url = "https://www.parliament.go.ke/the-national-assembly/house-business/bills"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15, verify=False)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        bills = []
        
        # Look for anchor tags linking to PDF files or containing 'sites/default/files'
        for link in soup.find_all('a', href=True):
            href = link['href']
            text = link.get_text(strip=True)
            
            if href.lower().endswith('.pdf') or 'sites/default/files' in href:
                # Ensure full URL
                full_url = urljoin(BASE_URL, href)

                if len(text) > 5 and 'BILL' in text.upper():  # Filter out short or non-bill links
                    bills.append({'title': text, 'url': full_url})
        
        # Deduplicate based on URL
        unique_bills = list({v['url']: v for v in bills}.values())
        
        # Ensure the demo Motor Vehicle Circulation Tax Bill is always included
        demo_bill = {
            'title': 'The Motor Vehicle Circulation Tax Bill, 2026',
            'url': 'https://www.parliament.go.ke/sites/default/files/2026-06/Motor_Vehicle_Circulation_Tax_Bill_2026.pdf'
        }
        
        if not any(b['url'] == demo_bill['url'] for b in unique_bills):
            unique_bills.insert(0, demo_bill)

        return unique_bills

    except Exception as e:
        print(f"Scraping Error: {e}")
        # Fallback to demo bill if scraper encounters network/site structure issues
        return [{
            'title': 'The Motor Vehicle Circulation Tax Bill, 2026',
            'url': 'https://www.parliament.go.ke/sites/default/files/2026-06/Motor_Vehicle_Circulation_Tax_Bill_2026.pdf'
        }]
