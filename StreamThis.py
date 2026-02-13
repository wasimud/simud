import cloudscraper
from bs4 import BeautifulSoup
import datetime
import json

# URL to scrape
url = 'https://streamphis.xyz/?id=869'

# Create cloudscraper instance
scraper = cloudscraper.create_scraper()

# Get the page content
response = scraper.get(url)
if response.status_code != 200:
    print(f"Failed to retrieve page: {response.status_code}")
    exit(1)

# Parse HTML
soup = BeautifulSoup(response.text, 'html.parser')

# Find all channel items
groups = []
current_time = datetime.datetime.now().strftime("%H:%M:%S")

for a in soup.find_all('a', class_='ch-item'):
    href = a.get('href')
    if not href or not href.startswith('/?id='):
        continue
    
    channel_id = href.split('=')[1]
    full_url = 'https://streamphis.xyz' + href
    
    # Find the div containing details
    div = a.find('div')
    if not div:
        continue
    
    # Get channel name from <b>
    b = div.find('b')
    if not b:
        continue
    name = b.text.strip()
    
    # Optionally collect events (but not used in output as per pattern)
    # event_div = div.find('div', style="font-size: 0.8em;")
    # events = [child.text.strip() for child in event_div.children if hasattr(child, 'text') and child.text.strip()] if event_div else []
    
    # Create group entry
    groups.append({
        "name": name,
        "info": current_time,
        "online": "true",
        "image": "https://amandastevens.com.au/wp-content/gallery/logos/sky-business.png",
        "userAgent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.1 Mobile/15E148 Safari/605.1.15/Clipbox+/2.2.8",
        "url": full_url,
        "embed": "true",
        "isHost": ""
    })

# Create the main structure
current_date = datetime.date.today().strftime("%d/%m/%Y")
data = {
    "name": "Eventi Streamthis",
    "author": "Simud",
    "info": f"Aggiornata {current_date}",
    "image": "https://image.discovery.indazn.com/ca/v2/ca/image?id=bwpptcm0gux0al2h9ia8wz3fs_image-header_pIt_1762995838000&quality=70",
    "url": "https://raw.githubusercontent.com/wasimud/simud/refs/heads/main/W3U/EventiStream.w3u",
    "stations": groups
}

# Write to file
with open('EventiStream.w3u', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=4, ensure_ascii=False)

print("File EventiStream.w3u created successfully.")
