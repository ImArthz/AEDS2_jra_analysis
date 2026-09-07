"""
Módulo de Web Scraping do JBIS (Japan Bloodhorse Information System)
Extrai árvore de genealogia (Pedigree / DAG) para os cavalos do Top 3.
Possui checkpoint automático e delay seguro para evitar sobrecargas.
"""

import sys
import os
import re
import time
import urllib.parse
import requests
from bs4 import BeautifulSoup
from database import get_connection, init_db, export_to_csv

# Configura codificação UTF-8 para stdout e stderr no Windows
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
BASE_JBIS = "https://www.jbis.or.jp"

def search_jbis_horse_id(horse_name):
    """Busca o ID oficial do cavalo no banco do JBIS."""
    encoded_name = urllib.parse.quote(horse_name)
    url = f"{BASE_JBIS}/horse/result/?sid=horse&keyword={encoded_name}&match=exact"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.encoding = "utf-8"
        matches = re.findall(r'/horse/(\d{10})/', r.text)
        if matches:
            return matches[0]
        # Se não achou exato, tenta busca parcial
        url_part = f"{BASE_JBIS}/horse/result/?sid=horse&keyword={encoded_name}"
        r_part = requests.get(url_part, headers=HEADERS, timeout=15)
        r_part.encoding = "utf-8"
        matches_part = re.findall(r'/horse/(\d{10})/', r_part.text)
        if matches_part:
            return matches_part[0]
    except Exception as e:
        print(f"  [ERRO] Busca JBIS para '{horse_name}': {e}")
    return None

def extract_jbis_pedigree(horse_id, horse_name):
    """Extrai os genitores e avôs da árvore genealógica do JBIS."""
    url = f"{BASE_JBIS}/horse/{horse_id}/pedigree/"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.encoding = "utf-8"
        soup = BeautifulSoup(r.text, "html.parser")
        
        inner = soup.find("div", class_="data-3__inner")
        if not inner:
            return None

        items = inner.find_all("div", class_="data-3__items", recursive=False)
        if len(items) < 2:
            return None

        sire_block = items[0]  # Ramo Paterno
        dam_block = items[1]   # Ramo Materno

        def get_ancestors_in_block(block):
            ancestors = []
            for a in block.find_all("a", href=re.compile(r'/horse/\d{10}/?$')):
                name = a.get_text(strip=True)
                if name and name not in ['血統', '競走', '種', '繁殖', 'English']:
                    m = re.search(r'/horse/(\d{10})/?$', a['href'])
                    if m:
                        ancestors.append((m.group(1), name))
            return ancestors

        sire_list = get_ancestors_in_block(sire_block)
        dam_list = get_ancestors_in_block(dam_block)

        sire_id, sire_name = sire_list[0] if len(sire_list) > 0 else (None, None)
        grandsire_id, grandsire_name = sire_list[1] if len(sire_list) > 1 else (None, None)

        dam_id, dam_name = dam_list[0] if len(dam_list) > 0 else (None, None)
        dam_sire_id, dam_sire_name = dam_list[1] if len(dam_list) > 1 else (None, None)

        return {
            "horse_id": horse_id,
            "horse_name": horse_name,
            "sire_id": sire_id,
            "sire_name": sire_name,
            "dam_id": dam_id,
            "dam_name": dam_name,
            "grandsire_id": grandsire_id,
            "grandsire_name": grandsire_name,
            "dam_sire_id": dam_sire_id,
            "dam_sire_name": dam_sire_name
        }
    except Exception as e:
        print(f"  [ERRO] Extração pedigree {horse_name} (ID {horse_id}): {e}")
        return None

def scrape_missing_pedigrees(delay=2.0, max_horses=None):
    """Consulta cavalos que ainda não têm pedigree cadastrado e preenche a tabela."""
    init_db()
    conn = get_connection()
    cur = conn.cursor()

    # Busca cavalos pendentes
    cur.execute("""
    SELECT DISTINCT horse_name FROM race_entries
    WHERE horse_name NOT IN (SELECT horse_name FROM pedigree)
    AND horse_name != ''
    ORDER BY horse_name
    """)
    pending = [row[0] for row in cur.fetchall()]

    if max_horses:
        pending = pending[:max_horses]

    print(f"\n=======================================================")
    print(f"  Iniciando Scraper de Pedigree (JBIS)")
    print(f"  Total de cavalos pendentes: {len(pending)}")
    print(f"  Intervalo entre requisições: {delay}s")
    print(f"=======================================================\n")

    success_count = 0
    for idx, horse_name in enumerate(pending, 1):
        print(f"[{idx}/{len(pending)}] Pesquisando '{horse_name}'...")
        horse_id = search_jbis_horse_id(horse_name)
        time.sleep(delay)

        if not horse_id:
            print(f"   [AVISO] ID não localizado no JBIS para: {horse_name}")
            continue

        ped_data = extract_jbis_pedigree(horse_id, horse_name)
        time.sleep(delay)

        if ped_data:
            # Atualiza horse_id na tabela horses e race_entries
            cur.execute("UPDATE horses SET horse_id = ? WHERE name = ?", (horse_id, horse_name))
            cur.execute("UPDATE race_entries SET horse_id = ? WHERE horse_name = ?", (horse_id, horse_name))

            # Insere no pedigree
            cur.execute("""
            INSERT OR REPLACE INTO pedigree (
                horse_id, horse_name, sire_id, sire_name, dam_id, dam_name,
                grandsire_id, grandsire_name, dam_sire_id, dam_sire_name
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                ped_data["horse_id"], ped_data["horse_name"],
                ped_data["sire_id"], ped_data["sire_name"],
                ped_data["dam_id"], ped_data["dam_name"],
                ped_data["grandsire_id"], ped_data["grandsire_name"],
                ped_data["dam_sire_id"], ped_data["dam_sire_name"]
            ))
            conn.commit()
            success_count += 1
            print(f"   ✓ Salvo: Pai = {ped_data['sire_name']} | Avô Materno = {ped_data['dam_sire_name']}")

        # Exporta CSV a cada 10 registros
        if idx % 10 == 0:
            export_to_csv()

    export_to_csv()
    conn.close()
    print(f"\n[Pedigree] Finalizado! {success_count} genealogias coletadas e sincronizadas.")

if __name__ == "__main__":
    scrape_missing_pedigrees(delay=2.0)
