import sys
import time
import sqlite3
import re
import traceback
import urllib.request
from urllib.error import HTTPError, URLError
from bs4 import BeautifulSoup

# Import database functions
from database import get_connection, init_db, export_to_csv

# Reconfigure stdout/stderr for Windows UTF-8
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Constants
BASE_URL = 'https://www.jra.go.jp'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}
DELAY = 1.5

def fetch_html(url, retries=3):
    """Fetch HTML with robust error handling and retries."""
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=10) as response:
                return response.read().decode('cp932', errors='replace')
        except HTTPError as e:
            print(f"HTTP Error {e.code} fetching {url}: {e.reason}")
            if e.code in [403, 404]:
                return None # Don't retry on 403/404
        except Exception as e:
            print(f"Error fetching {url}: {e}")
        
        if attempt < retries - 1:
            wait_time = 2 ** attempt
            print(f"Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
            
    print(f"Failed to fetch {url} after {retries} attempts.")
    return None

def parse_grade(race_name):
    """Parse grade and weight from race name."""
    grade_weight = 0.0
    grade = ''
    if 'GⅠ' in race_name or 'ＧⅠ' in race_name or 'G1' in race_name:
        grade = 'G1'
        grade_weight = 1.0
    elif 'GⅡ' in race_name or 'ＧⅡ' in race_name or 'G2' in race_name:
        grade = 'G2'
        grade_weight = 0.7
    elif 'GⅢ' in race_name or 'ＧⅢ' in race_name or 'G3' in race_name:
        grade = 'G3'
        grade_weight = 0.5
    return grade, grade_weight

def parse_weather_going(text):
    """Parse weather and going from text."""
    weather_map = {'晴': 'Fine', '曇': 'Cloudy', '雨': 'Rain', '小雨': 'Light Rain', '雪': 'Snow'}
    going_map = {'良': 'Firm', '稍重': 'Good to Soft', '重': 'Soft', '不良': 'Heavy'}
    
    weather = ''
    for k, v in weather_map.items():
        if f'天候：{k}' in text or f'天候:{k}' in text:
            weather = v
            break
            
    going = ''
    for k, v in going_map.items():
        if f'：{k}' in text or f':{k}' in text:
            going = v
            break
            
    return weather, going

def parse_race_result(html, race_url, race_id, year):
    """Parse the race result page."""
    soup = BeautifulSoup(html, 'html.parser')
    
    # Extract metadata (weather, going)
    weather, going = '', ''
    cell = soup.find('div', class_='cell')
    if cell:
        weather, going = parse_weather_going(cell.get_text())
    
    table = None
    rows = []
    for tbl in soup.find_all('table'):
        r = tbl.find_all('tr', recursive=False)
        if len(r) > 2:
            first_row = r[0]
            if first_row and '馬名' in first_row.get_text():
                table = tbl
                rows = r
                break
            
    if not table or len(rows) < 2:
        return None, weather, going
        
    # Extract headers
    header_cells = rows[0].find_all(['th', 'td'])
    headers = [th.get_text(strip=True) for th in header_cells]
    
    def find_idx(name, default_idx):
        for i, h in enumerate(headers):
            if name in h:
                return i
        return default_idx
        
    pos_idx = find_idx('着順', 0)
    horse_idx = find_idx('馬名', 4)
    sex_idx = find_idx('性', 5)
    age_idx = find_idx('齢', 6)
    weight_idx = find_idx('負担重量', 7)
    jockey_idx = find_idx('騎手', 8)
    time_idx = find_idx('タイム', 9)
    margin_idx = find_idx('着差', 10)
    horse_weight_idx = find_idx('馬体重', 11)
    trainer_idx = find_idx('調教師', 12)
    popularity_idx = find_idx('単勝人気', 13)
    
    entries = []
    
    for row in rows[1:]:
        cells = row.find_all(['th', 'td'])
        if not cells:
            continue
            
        try:
            pos_text = cells[pos_idx].get_text(strip=True)
            try:
                position = int(pos_text)
            except ValueError:
                position = 99 # DNF/DQ
                
            horse_name = cells[horse_idx].get_text(strip=True)
            horse_id = ''
            a_tag = cells[horse_idx].find('a')
            if a_tag and 'href' in a_tag.attrs:
                m = re.search(r'(/meikan/horse/[^/]+/)', a_tag['href'])
                if m:
                    horse_id = m.group(1)
            if not horse_id:
                horse_id = horse_name
                    
            sex = cells[sex_idx].get_text(strip=True)
            age_text = cells[age_idx].get_text(strip=True)
            try:
                age = int(age_text)
            except ValueError:
                age = None
                
            weight = cells[weight_idx].get_text(strip=True)
            jockey = cells[jockey_idx].get_text(strip=True)
            finish_time = cells[time_idx].get_text(strip=True)
            margin = cells[margin_idx].get_text(strip=True)
            
            # The data has TWO cells for horse weight: value and change.
            if len(cells) > horse_weight_idx + 1:
                hw_val = cells[horse_weight_idx].get_text(strip=True)
                hw_change = cells[horse_weight_idx + 1].get_text(strip=True)
                horse_weight = f"{hw_val}({hw_change})" if hw_change else hw_val
            else:
                horse_weight = cells[horse_weight_idx].get_text(strip=True)
                
            # Shift indices by 1 for cells after the split horse weight column
            trainer = cells[trainer_idx + 1].get_text(strip=True) if len(cells) > trainer_idx + 1 else ''
            
            # The 'odds' field in result table is actually popularity rank
            popularity = cells[popularity_idx + 1].get_text(strip=True) if len(cells) > popularity_idx + 1 else ''
            
            # TODO: Parse passing_positions from コーナー通過順位 section
            passing_positions = ''
            
            entry = {
                'race_id': race_id,
                'horse_name': horse_name,
                'horse_id': horse_id,
                'position': position,
                'finish_time': finish_time,
                'jockey': jockey,
                'trainer': trainer,
                'weight': weight,
                'odds': popularity, # Stored in 'odds' field for now
                'horse_weight': horse_weight,
                'age': age,
                'sex': sex,
                'passing_positions': passing_positions,
                'margin': margin
            }
            entries.append(entry)
            
        except Exception as e:
            print(f"Error parsing row in {race_url}: {e}")
            continue
            
    return entries, weather, going

def scrape_year(year, source='graded'):
    """Scrape races for a specific year."""
    conn = get_connection()
    cursor = conn.cursor()
    
    url = f"{BASE_URL}/datafile/seiseki/replay/{year}/jyusyo.html"
    if source == 'g1':
        url = f"{BASE_URL}/datafile/seiseki/replay/{year}/g1.html"
        
    print(f"Fetching {url}")
    html = fetch_html(url)
    
    if not html and source == 'graded':
        print(f"jyusyo.html failed for {year}, trying g1.html fallback...")
        source = 'g1'
        url = f"{BASE_URL}/datafile/seiseki/replay/{year}/g1.html"
        html = fetch_html(url)
        
    if not html:
        print(f"Could not fetch data for {year}")
        return
        
    soup = BeautifulSoup(html, 'html.parser')
    
    result_links = []
    import re
    for a in soup.find_all('a', href=True):
        href = a['href']
        if 'result' in href or re.search(r'\d{2,3}\.html$', href):
            result_links.append(a)
            
    print(f"Found {len(result_links)} race links for {year}")
    
    import urllib.parse
    for i, a in enumerate(result_links):
        href = a['href']
        race_url = urllib.parse.urljoin(url, href)
            
        row = a.find_parent('tr')
        date_str, race_name, track, surface_dist = '', '', '', ''
        
        if row:
            cells = row.find_all(['th', 'td'])
            if len(cells) >= 5:
                date_str = cells[0].get_text(strip=True)
                race_name = cells[1].get_text(strip=True)
                track = cells[2].get_text(strip=True)
                surface_dist = cells[4].get_text(strip=True)
                
        grade, grade_weight = parse_grade(race_name)
        
        surface = 'Turf' if '芝' in surface_dist else 'Dirt' if 'ダート' in surface_dist else ''
        distance = ''
        m = re.search(r'([0-9,]+)', surface_dist)
        if m:
            distance = m.group(1).replace(',', '')
            
        # Create unique race ID
        race_id = f"{year}_{track}_{race_name}"
        
        # Pular se j existe no banco de dados
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM races WHERE race_id = ?", (race_id,))
        if cur.fetchone():
            print(f"Skipping {year} {race_name} (already scraped)")
            continue

        print(f"Scraping {year} {race_name} ({race_url})")
        time.sleep(DELAY)
        
        result_html = fetch_html(race_url)
        if not result_html:
            continue
            
        entries, weather, going = parse_race_result(result_html, race_url, race_id, year)
        
        # Save race
        cursor.execute('''
        INSERT OR REPLACE INTO races (
            race_id, year, date, race_name, track, grade, grade_weight, 
            surface, distance, going, weather, num_runners, url
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            race_id, year, date_str, race_name, track, grade, grade_weight,
            surface, distance, going, weather, len(entries) if entries else 0, race_url
        ))
        
        # Save entries
        if entries:
            for e in entries:
                if not e.get('horse_name'):
                    continue
                try:
                    cursor.execute('INSERT OR IGNORE INTO horses (name, horse_id, sex) VALUES (?, ?, ?)', (e['horse_name'], e['horse_id'], e['sex']))
                    cursor.execute('''
                    INSERT OR REPLACE INTO race_entries (
                        race_id, horse_name, horse_id, position, finish_time,
                        jockey, trainer, weight, odds, horse_weight, age, sex,
                        passing_positions, margin
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        e['race_id'], e['horse_name'], e['horse_id'], e['position'], e['finish_time'],
                        e['jockey'], e['trainer'], e['weight'], e['odds'], e['horse_weight'], 
                        e['age'], e['sex'], e['passing_positions'], e['margin']
                    ))
                except Exception as ex:
                    print(f"FOREIGN KEY ERROR! race_id: {e['race_id']}, horse_name: {e['horse_name']}")
                    raise ex
        
        # Checkpoint: save each race immediately to SQLite
        conn.commit()
        
    print(f"Finished scraping year {year}")
    export_to_csv()

if __name__ == "__main__":
    init_db()
    # Example: run for recent years
    for y in range(2005, 2026):
        scrape_year(y, source='graded')
