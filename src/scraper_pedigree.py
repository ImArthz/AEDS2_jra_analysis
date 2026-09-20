"""
Módulo de Web Scraping do JBIS (Japan Bloodhorse Information System)
Extrai pedigree de 5 gerações e perfil do cavalo (Ganhos, Criador, Dono, Cor, Nascimento).
"""

import sys
import os
import re
import time
import urllib.parse
import requests
from bs4 import BeautifulSoup
from database import get_connection, init_db, export_to_csv

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}
BASE_JBIS = "https://www.jbis.or.jp"

def search_jbis_horse_id(horse_name, delay=2.0):
    encoded_name = urllib.parse.quote(horse_name)
    for attempt in range(3):
        try:
            url = f"{BASE_JBIS}/horse/result/?sid=horse&keyword={encoded_name}&match=exact"
            r = requests.get(url, headers=HEADERS, timeout=15)
            r.encoding = "utf-8"
            matches = re.findall(r'/horse/(\d{10})/', r.text)
            if matches: return matches[0]

            url_part = f"{BASE_JBIS}/horse/result/?sid=horse&keyword={encoded_name}"
            r_part = requests.get(url_part, headers=HEADERS, timeout=15)
            r_part.encoding = "utf-8"
            matches_part = re.findall(r'/horse/(\d{10})/', r_part.text)
            if matches_part: return matches_part[0]
            return None
        except Exception as e:
            time.sleep(delay * (2 ** attempt))
    return None

def extract_jbis_profile(horse_id):
    """Extrai informações do perfil do cavalo na página inicial."""
    url = f"{BASE_JBIS}/horse/{horse_id}/"
    profile = {
        "birth_date": "", "color": "", "breeder": "", "owner": "", 
        "total_earnings": 0, "total_starts": 0, "total_wins": 0
    }
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.encoding = "utf-8"
        soup = BeautifulSoup(r.text, "html.parser")
        
        # Procurar na tabela de perfil (cabealho dt, valor dd)
        for dt in soup.find_all("dt"):
            label = dt.get_text(strip=True)
            dd = dt.find_next_sibling("dd")
            if not dd: continue
            val = dd.get_text(strip=True)
            
            if "生年月日" in label:
                profile["birth_date"] = val
            elif "毛色" in label:
                profile["color"] = val
            elif "生産牧場" in label:
                profile["breeder"] = val
            elif "馬主" in label:
                profile["owner"] = val
            elif "総賞金" in label:
                # Ex: 48,153.0万円 -> 481,530,000 Yen
                m = re.search(r'([\d,]+(?:\.\d+)?)', val)
                if m:
                    num_str = m.group(1).replace(",", "")
                    profile["total_earnings"] = int(float(num_str) * 10000)
            elif "戦績" in label:
                # Ex: 13戦4勝
                m_st = re.search(r'(\d+)戦', val)
                m_win = re.search(r'(\d+)勝', val)
                if m_st: profile["total_starts"] = int(m_st.group(1))
                if m_win: profile["total_wins"] = int(m_win.group(1))
                
        return profile
    except Exception as e:
        print(f"  [AVISO] Erro ao extrair perfil ID {horse_id}: {e}")
        return profile

def extract_jbis_pedigree_5gen(horse_id, horse_name):
    url = f"{BASE_JBIS}/horse/{horse_id}/pedigree/"
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.encoding = "utf-8"
        soup = BeautifulSoup(r.text, "html.parser")
        
        inner = soup.find("div", class_="data-3__inner")
        if not inner:
            inner = soup.find("table", class_="pedigree") or soup.find("div", id="pedigree")
            if not inner: return None
        
        all_ancestors = []
        for a in inner.find_all("a", href=re.compile(r'/horse/\d{10}/?$')):
            name = a.get_text(strip=True)
            if name and name not in ['血統', '競走', '種', '繁殖', 'English', '産駒', '5代血統表']:
                m = re.search(r'/horse/(\d{10})/?$', a['href'])
                if m: all_ancestors.append((m.group(1), name))
        
        if not all_ancestors: return None
        
        items = inner.find_all("div", class_="data-3__items", recursive=False)
        sire_ancestors, dam_ancestors = [], []
        
        if len(items) >= 2:
            for a in items[0].find_all("a", href=re.compile(r'/horse/\d{10}/?$')):
                name = a.get_text(strip=True)
                if name and name not in ['血統', '競走', '種', '繁殖', 'English', '産駒', '5代血統表']:
                    m = re.search(r'/horse/(\d{10})/?$', a['href'])
                    if m: sire_ancestors.append((m.group(1), name))
            for a in items[1].find_all("a", href=re.compile(r'/horse/\d{10}/?$')):
                name = a.get_text(strip=True)
                if name and name not in ['血統', '競走', '種', '繁殖', 'English', '産駒', '5代血統表']:
                    m = re.search(r'/horse/(\d{10})/?$', a['href'])
                    if m: dam_ancestors.append((m.group(1), name))
        else:
            mid = len(all_ancestors) // 2
            sire_ancestors = all_ancestors[:mid]
            dam_ancestors = all_ancestors[mid:]
        
        def build_line_order(prefix, depth, max_depth):
            if depth > max_depth: return []
            lines = [prefix]
            lines.extend(build_line_order(prefix + "S", depth + 1, max_depth))
            lines.extend(build_line_order(prefix + "D", depth + 1, max_depth))
            return lines
        
        sire_lines = build_line_order("S", 1, 5)
        dam_lines = build_line_order("D", 1, 5)
        
        tree_entries = []
        for i, (anc_id, anc_name) in enumerate(sire_ancestors):
            if i < len(sire_lines):
                tree_entries.append({
                    "horse_id": horse_id, "horse_name": horse_name,
                    "ancestor_id": anc_id, "ancestor_name": anc_name,
                    "generation": len(sire_lines[i]), "line": sire_lines[i]
                })
        for i, (anc_id, anc_name) in enumerate(dam_ancestors):
            if i < len(dam_lines):
                tree_entries.append({
                    "horse_id": horse_id, "horse_name": horse_name,
                    "ancestor_id": anc_id, "ancestor_name": anc_name,
                    "generation": len(dam_lines[i]), "line": dam_lines[i]
                })
        
        legacy = {
            "horse_id": horse_id, "horse_name": horse_name,
            "sire_id": sire_ancestors[0][0] if len(sire_ancestors) > 0 else None,
            "sire_name": sire_ancestors[0][1] if len(sire_ancestors) > 0 else None,
            "dam_id": dam_ancestors[0][0] if len(dam_ancestors) > 0 else None,
            "dam_name": dam_ancestors[0][1] if len(dam_ancestors) > 0 else None,
            "grandsire_id": sire_ancestors[1][0] if len(sire_ancestors) > 1 else None,
            "grandsire_name": sire_ancestors[1][1] if len(sire_ancestors) > 1 else None,
            "dam_sire_id": dam_ancestors[1][0] if len(dam_ancestors) > 1 else None,
            "dam_sire_name": dam_ancestors[1][1] if len(dam_ancestors) > 1 else None,
        }
        
        return {"legacy": legacy, "tree": tree_entries}
    except Exception as e:
        print(f"  [ERRO] Pedigree {horse_name} (ID {horse_id}): {e}")
        return None

def scrape_missing_pedigrees(delay=2.0, max_horses=None):
    init_db()
    conn = get_connection()
    cur = conn.cursor()

    # Busca cavalos que não têm pedigree OU não tiveram o perfil raspado
    cur.execute("""
    SELECT h.name, h.horse_id FROM horses h
    LEFT JOIN pedigree p ON h.name = p.horse_name
    WHERE (p.horse_name IS NULL OR h.profile_scraped = 0)
    AND h.name != ''
    ORDER BY h.name
    """)
    pending = cur.fetchall()

    if max_horses: pending = pending[:max_horses]

    print(f"\n{'='*60}")
    print(f"  JBIS Scraper (Pedigree 5-Gen + Perfil)")
    print(f"  Pendentes: {len(pending)} cavalos")
    print(f"{'='*60}\n")

    for idx, (horse_name, db_horse_id) in enumerate(pending, 1):
        print(f"[{idx}/{len(pending)}] '{horse_name}'...")
        horse_id = search_jbis_horse_id(horse_name, delay)
        time.sleep(delay)

        if not horse_id:
            print(f"   [N/F] No localizado no JBIS.")
            cur.execute("INSERT OR IGNORE INTO pedigree (horse_id, horse_name) VALUES (?, ?)", (db_horse_id, horse_name))
            cur.execute("UPDATE horses SET profile_scraped = 1 WHERE name = ?", (horse_name,))
            conn.commit()
            continue

        # 1. Extrair Perfil
        profile = extract_jbis_profile(horse_id)
        time.sleep(delay)

        # Atualizar tabela horses com perfil
        cur.execute("""
        UPDATE horses SET 
            horse_id = ?, birth_date = ?, color = ?, breeder = ?, 
            owner = ?, total_earnings = ?, total_starts = ?, total_wins = ?, 
            profile_scraped = 1
        WHERE name = ?
        """, (
            horse_id, profile["birth_date"], profile["color"], profile["breeder"],
            profile["owner"], profile["total_earnings"], profile["total_starts"], 
            profile["total_wins"], horse_name
        ))
        
        # 2. Extrair Pedigree
        result = extract_jbis_pedigree_5gen(horse_id, horse_name)
        time.sleep(delay)

        if result:
            leg = result["legacy"]
            cur.execute("""
            INSERT OR REPLACE INTO pedigree (
                horse_id, horse_name, sire_id, sire_name, dam_id, dam_name,
                grandsire_id, grandsire_name, dam_sire_id, dam_sire_name
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                leg["horse_id"], leg["horse_name"], leg["sire_id"], leg["sire_name"],
                leg["dam_id"], leg["dam_name"], leg["grandsire_id"], leg["grandsire_name"],
                leg["dam_sire_id"], leg["dam_sire_name"]
            ))

            for entry in result["tree"]:
                cur.execute("""
                INSERT OR REPLACE INTO pedigree_tree
                (horse_id, horse_name, ancestor_id, ancestor_name, generation, line)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    entry["horse_id"], entry["horse_name"], entry["ancestor_id"], 
                    entry["ancestor_name"], entry["generation"], entry["line"]
                ))
            print(f"   ✓ Perfil e Pedigree salvos ({len(result['tree'])} ancestrais). Ganhos: {profile['total_earnings']:,} ¥")
        else:
            print(f"   [ERRO] Apenas perfil salvo. Falha no Pedigree.")

        conn.commit()
        if idx % 10 == 0: export_to_csv()

    export_to_csv()
    conn.close()
    print(f"\n[JBIS] Finalizado!")

if __name__ == "__main__":
    scrape_missing_pedigrees(delay=2.0)
