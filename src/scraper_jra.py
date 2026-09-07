"""
Módulo de Web Scraping da JRA (Japan Racing Association)
Extrai histórico oficial de corridas G1 e Top 3 com checkpointing e delay seguro.
"""

import sys
import os
import re
import time
import urllib.parse
import requests
from bs4 import BeautifulSoup
from database import get_connection, init_db, export_to_csv

# Configura codificação de saída para UTF-8 no Windows
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

HTTP_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
BASE_JRA = "https://www.jra.go.jp"

def fetch_html(url):
    """Baixa HTML com detecção inteligente de encoding (Shift_JIS / UTF-8)."""
    try:
        r = requests.get(url, headers=HTTP_HEADERS, timeout=15)
        r.encoding = r.apparent_encoding or "shift_jis"
        return r.text
    except Exception as e:
        print(f"[ERRO] Falha ao baixar {url}: {e}")
        return None

def extract_g1_calendar(year):
    """Extrai a lista de corridas G1 do ano informado."""
    url = f"{BASE_JRA}/datafile/seiseki/replay/{year}/g1.html"
    html = fetch_html(url)
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")
    races = []

    # Procura linhas de tabela com links para resultados
    for tr in soup.find_all("tr"):
        tds = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
        if len(tds) < 5:
            continue

        date_str = tds[0]
        race_name = tds[1]

        # Filtro de linhas válidas da tabela oficial
        if not race_name or not ("/" in date_str or "月" in date_str) or len(date_str) > 20:
            continue

        links = [a["href"] for a in tr.find_all("a", href=True) if "result" in a["href"]]
        if not links:
            continue

        result_rel_url = links[0]
        result_full_url = urllib.parse.urljoin(url, result_rel_url)

        track = tds[2] if len(tds) > 2 else ""
        course_str = ""
        for cell in tds[3:]:
            if "芝" in cell or "ダ" in cell or "障" in cell:
                course_str = cell
                break

        surface = "Dirt" if "ダ" in course_str else ("Turf" if "芝" in course_str else "Obstacle")
        dist_match = re.search(r"(\d[\d,]*)", course_str)
        distance = int(dist_match.group(1).replace(",", "")) if dist_match else 0

        # Gerar race_id limpo
        match_id = re.search(r"result/([a-zA-Z0-9]+)\.html", result_rel_url)
        race_code = match_id.group(1) if match_id else f"race_{len(races)+1}"
        race_id = f"{year}_{race_code}"

        races.append({
            "race_id": race_id,
            "year": year,
            "date": date_str,
            "race_name": race_name,
            "track": track,
            "surface": surface,
            "distance": distance,
            "url": result_full_url
        })

    return races

def extract_race_top3(result_url):
    """Acessa a página de resultado oficial e extrai o Top 3 (1º, 2º e 3º)."""
    html = fetch_html(result_url)
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")
    target_table = None
    target_headers = None

    # Encontra a tabela oficial com 着順 e 馬名 no cabeçalho
    for tbl in soup.find_all("table"):
        for row in tbl.find_all("tr")[:2]:
            heads = [re.sub(r'\s+', '', c.get_text(strip=True)) for c in row.find_all(["th", "td"])]
            if any('着順' in h for h in heads) and any('馬名' in h for h in heads) and len(heads) < 20 and heads[0] in ['着順', '着']:
                target_table = tbl
                target_headers = heads
                break
        if target_table:
            break

    if not target_table:
        return []

    def find_idx(keywords):
        for i, h in enumerate(target_headers):
            for k in keywords:
                if k in h:
                    return i
        return -1

    idx_pos = find_idx(['着順', '着'])
    idx_name = find_idx(['馬名'])
    idx_jockey = find_idx(['騎手'])
    idx_time = find_idx(['タイム'])
    idx_weight = find_idx(['負担重量', '斤量'])
    idx_sex = find_idx(['性齢', '性'])

    entries = []
    seen_positions = set()

    for tr in target_table.find_all("tr")[1:]:
        cells = [c.get_text(strip=True) for c in tr.find_all(["td", "th"])]
        if len(cells) <= max(idx_pos, idx_name) or idx_pos == -1 or idx_name == -1:
            continue

        pos_str = cells[idx_pos].strip()
        if pos_str in ['1', '2', '3'] and pos_str not in seen_positions:
            seen_positions.add(pos_str)
            pos = int(pos_str)
            raw_name = cells[idx_name]
            horse_name = re.sub(r'[\(（][^()（）]+[\)）]', '', raw_name).strip()

            jockey = cells[idx_jockey] if idx_jockey != -1 and len(cells) > idx_jockey else ""
            finish_time = cells[idx_time] if idx_time != -1 and len(cells) > idx_time else ""
            
            weight = 0.0
            if idx_weight != -1 and len(cells) > idx_weight:
                wm = re.search(r'(\d+\.?\d*)', cells[idx_weight])
                if wm:
                    weight = float(wm.group(1))

            sex = ""
            if idx_sex != -1 and len(cells) > idx_sex:
                s_str = cells[idx_sex]
                if '牡' in s_str: sex = '牡'
                elif '牝' in s_str: sex = '牝'
                elif 'セ' in s_str: sex = 'セン'

            entries.append({
                "position": pos,
                "horse_name": horse_name,
                "jockey": jockey,
                "finish_time": finish_time,
                "weight": weight,
                "sex": sex
            })

    return sorted(entries, key=lambda x: x["position"])[:3]

def scrape_jra_period(start_year=2002, end_year=2020, delay=2.0):
    """Executa a raspagem com checkpointing automático."""
    init_db()
    conn = get_connection()
    cur = conn.cursor()

    total_saved_races = 0
    total_saved_entries = 0

    print(f"\n=======================================================")
    print(f"  Iniciando Scraper JRA G1: {start_year} a {end_year}")
    print(f"  Taxa de requisições: 1 req a cada {delay}s (politeness)")
    print(f"=======================================================\n")

    for year in range(start_year, end_year + 1):
        print(f"\n>>> Processando Ano: {year} <<<")
        races = extract_g1_calendar(year)
        print(f"  [Ano {year}] Encontradas {len(races)} corridas G1.")
        time.sleep(delay)

        for race in races:
            # 1. Verifica Checkpoint: corrida já salva?
            cur.execute("SELECT 1 FROM races WHERE url = ?", (race["url"],))
            if cur.fetchone():
                print(f"  [CHECKPOINT] Corrida já existe no banco: {race['race_id']} ({race['race_name']}). Pulando...")
                continue

            print(f"  -> Coletando Top 3: {race['race_id']} - {race['race_name']} ({race['surface']} {race['distance']}m)...")
            top3 = extract_race_top3(race["url"])

            # 2. Inserir Corrida no SQLite
            cur.execute("""
            INSERT OR REPLACE INTO races (race_id, year, date, race_name, track, surface, distance, url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                race["race_id"], race["year"], race["date"], race["race_name"],
                race["track"], race["surface"], race["distance"], race["url"]
            ))

            # 3. Inserir Cavalos e Entradas
            for entry in top3:
                # Inserir cavalo se não existir
                cur.execute("INSERT OR IGNORE INTO horses (horse_id, name, sex) VALUES (?, ?, ?)",
                            (None, entry["horse_name"], entry["sex"]))
                
                # Inserir entrada da corrida
                cur.execute("""
                INSERT OR REPLACE INTO race_entries (race_id, horse_id, horse_name, position, finish_time, jockey, weight)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    race["race_id"], None, entry["horse_name"], entry["position"],
                    entry["finish_time"], entry["jockey"], entry["weight"]
                ))
                total_saved_entries += 1

            conn.commit()
            total_saved_races += 1
            print(f"     ✓ OK: {len(top3)} colocados salvos para {race['race_name']}.")
            time.sleep(delay)

        # Exporta CSV incrementalmente após cada ano concluído
        export_to_csv()

    conn.close()
    print(f"\n=======================================================")
    print(f"  Concluído! Total de corridas salvas nesta sessão: {total_saved_races}")
    print(f"  Total de entradas Top 3 salvas: {total_saved_entries}")
    print(f"=======================================================\n")

if __name__ == "__main__":
    scrape_jra_period(2002, 2020, delay=2.0)
