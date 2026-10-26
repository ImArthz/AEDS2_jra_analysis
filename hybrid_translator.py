"""
Hybrid Translation Engine (Gemini Multi-Model Pool + Google GTX Batch + JRA Domain Rules)
Traduz 100% dos nomes japoneses do banco jra_graded.db (cavalos, ancestrais 5-gen,
jóqueis, treinadores, criadores, donos e nomes de corridas) para data/gemini_cache.json.
"""

import sqlite3
import json
import time
import sys
import os
import re
import urllib.request
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from google import genai
from google.genai import types

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

API_KEY = os.environ.get("GEMINI_API_KEY", "YOUR_API_KEY_HERE")
CACHE_PATH = "data/gemini_cache.json"
DB_PATH = "data/sqlite/jra_graded.db"

# Regex para detectar caracteres japoneses (Hiragana, Katakana, Kanji, Full-width)
JP_RE = re.compile(r'[\u3000-\u30ff\u4e00-\u9fff\uff00-\uffef]')
COUNTRY_RE = re.compile(r'^(.+?)\s*(\([A-Z]{2,4}\))\s*$')
GARBAGE_NAMES = {'6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '02-07', '02-11', '馬単', 'ワイド', '３連複'}

# Correções de prefixos tradicionais (Kanmei / Crown names) da JRA onde tradutores literais erram
JRA_FIXES = [
    (re.compile(r'\bsymbol\s+li\s*rudolph\b', re.I), 'Symboli Rudolf'),
    (re.compile(r'\bsymbol\s+li\b', re.I), 'Symboli'),
    (re.compile(r'\bsymboli\s*rudolph\b', re.I), 'Symboli Rudolf'),
    (re.compile(r'\bdeep\s+impact\b', re.I), 'Deep Impact'),
    (re.compile(r'\borf[eè]vre\b', re.I), 'Orfevre'),
    (re.compile(r'\buokka\b', re.I), 'Vodka'),
    (re.compile(r'\bmaruzenski\b', re.I), 'Maruzensky'),
    (re.compile(r'\bmeisho\b', re.I), 'Meisho'),
    (re.compile(r'\bnihon\s+pillow?\b', re.I), 'Nihon Pillow'),
]

TITLE_LOWER_WORDS = {'of', 'in', 'the', 'and', 'to', 'for', 'on', 'at', 'by', 'de', 'la', 'du'}


def smart_title_case(s: str) -> str:
    """Formata nomes de cavalos/termos em Title Case preservando siglas e preposições."""
    if not s:
        return s
    s = s.strip()
    for pat, repl in JRA_FIXES:
        s = pat.sub(repl, s)

    # Preservar sufixos corporativos
    words = s.split()
    out = []
    for idx, w in enumerate(words):
        if w.upper() in {'II', 'III', 'IV', 'USA', 'GB', 'IRE', 'FR', 'AUS', 'NZ', 'CAN', 'GER', 'ITY', 'JRA', 'NHK'}:
            out.append(w.upper())
        elif re.match(r'^[A-Z]\.[A-Z]?\.?$', w):
            out.append(w.upper())
        elif w in {'Ltd.', 'Co.,', 'Inc.', 'Corp.'}:
            out.append(w)
        elif idx > 0 and w.lower() in TITLE_LOWER_WORDS:
            out.append(w.lower())
        elif w.islower() or w.isupper():
            out.append(w.capitalize())
        else:
            out.append(w)
    return " ".join(out)


def translate_batch_gemini(client, batch, category_hint="general", models=None):
    """Traduz um lote usando o pool de modelos Gemini."""
    if models is None:
        models = ["gemini-3.5-flash-lite", "gemini-3.5-flash", "gemini-3.7-flash", "gemini-3.6-flash"]

    if category_hint == "people":
        prompt = (
            "Convert the following Japanese horse racing jockeys and trainers into their OFFICIAL "
            "Hepburn Romaji / English name (GivenName FamilyName, e.g. 武豊 -> Yutaka Take, "
            "川田将雅 -> Yuga Kawada, Ｃ．ルメール -> C. Lemaire, 池江泰寿 -> Yasutoshi Ikee). "
            "Return ONLY a valid JSON object mapping each exact input string to its English name."
        )
    elif category_hint == "races":
        prompt = (
            "Translate the following Japanese JRA Graded Race names into their OFFICIAL JRA English race names "
            "(e.g. 弥生賞 -> Yayoi Sho, 中山金杯 -> Nakayama Kimpai, 阪神大賞典 -> Hanshin Daishoten, "
            "GⅢ中山金杯 -> Nakayama Kimpai). "
            "Return ONLY a valid JSON object mapping each exact input string to its English race name."
        )
    else:
        prompt = (
            "Translate the following Japanese horse racing names (racehorses, thoroughbred ancestors, "
            "breeders, and owners) into their OFFICIAL English spelling (e.g. ディープインパクト -> Deep Impact, "
            "(有)社台レースホース -> Shadai Race Horse Co., Ltd., ノーザンファーム -> Northern Farm). "
            "If it is a person's name, use Hepburn Romaji. "
            "Return ONLY a valid JSON object mapping each exact input string to its English string."
        )

    content = prompt + "\n\n" + "\n".join(batch)
    for model_name in models:
        try:
            resp = client.models.generate_content(
                model=model_name,
                contents=content,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.0,
                    http_options=types.HttpOptions(timeout=30000),
                ),
            )
            raw = resp.text.strip()
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            data = json.loads(raw)
            if isinstance(data, dict) and len(data) > 0:
                return {k: smart_title_case(str(v)) for k, v in data.items()}, model_name
        except Exception:
            continue
    return None, None


def translate_batch_gtx(batch):
    """Traduz um lote de strings usando o endpoint GTX em lote com pós-processamento JRA."""
    if not batch:
        return {}
    # Pré-processar prefixos empresariais para ajudar o tradutor
    cleaned_inputs = []
    for item in batch:
        s = item.replace("\n", " ").strip()
        cleaned_inputs.append(s)

    text = "\n".join(cleaned_inputs)
    url = (
        "https://translate.googleapis.com/translate_a/single?client=gtx&sl=ja&tl=en&dt=t&q="
        + urllib.parse.quote(text)
    )
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    full_translated = "".join(seg[0] for seg in data[0] if seg and seg[0])
    lines = full_translated.split("\n")

    if len(lines) != len(batch):
        # Fallback metade por metade se alguma linha quebrou
        if len(batch) > 1:
            mid = len(batch) // 2
            res = {}
            res.update(translate_batch_gtx(batch[:mid]))
            res.update(translate_batch_gtx(batch[mid:]))
            return res
        elif len(lines) >= 1:
            return {batch[0]: smart_title_case(lines[0])}
        return {}

    result = {}
    for orig, tr in zip(batch, lines):
        result[orig] = smart_title_case(tr)
    return result


def collect_Categorized_strings(conn, cache):
    cur = conn.cursor()

    def fetch_col(sql):
        cur.execute(sql)
        out = set()
        for (val,) in cur.fetchall():
            if not val:
                continue
            s = str(val).strip()
            if s in GARBAGE_NAMES:
                continue
            if JP_RE.search(s):
                out.add(s)
        return out

    # 1. Races (310)
    races = fetch_col("SELECT DISTINCT race_name FROM races WHERE race_name IS NOT NULL")

    # 2. People: Jockeys & Trainers (incluindo colunas deslocadas de 2007-2018!)
    jockeys = fetch_col("SELECT DISTINCT jockey FROM race_entries WHERE jockey IS NOT NULL")
    jockeys |= fetch_col("SELECT DISTINCT finish_time FROM race_entries WHERE age IS NULL AND finish_time IS NOT NULL")
    trainers = fetch_col("SELECT DISTINCT trainer FROM race_entries WHERE trainer IS NOT NULL")
    trainers |= fetch_col("SELECT DISTINCT CAST(odds AS TEXT) FROM race_entries WHERE age IS NULL AND odds IS NOT NULL")
    # Remover variações numéricas de peso que estavam em trainer ('+4', '-2', '0')
    people = {p for p in (jockeys | trainers) if not re.match(r'^[+\-]?\d+(\.\d+)?$', p)}

    # 3. Core Horses & Direct Sires/Grandsires/Damsires & Breeders/Owners
    sires = (
        fetch_col("SELECT DISTINCT sire_name FROM pedigree WHERE sire_name IS NOT NULL")
        | fetch_col("SELECT DISTINCT grandsire_name FROM pedigree WHERE grandsire_name IS NOT NULL")
        | fetch_col("SELECT DISTINCT dam_sire_name FROM pedigree WHERE dam_sire_name IS NOT NULL")
    )
    racers = (
        fetch_col("SELECT DISTINCT name FROM horses WHERE name IS NOT NULL")
        | fetch_col("SELECT DISTINCT horse_name FROM race_entries WHERE horse_name IS NOT NULL")
    )
    dams = fetch_col("SELECT DISTINCT dam_name FROM pedigree WHERE dam_name IS NOT NULL")
    breeders_owners = (
        fetch_col("SELECT DISTINCT breeder FROM horses WHERE breeder IS NOT NULL")
        | fetch_col("SELECT DISTINCT owner FROM horses WHERE owner IS NOT NULL")
    )
    ancestors_5gen = fetch_col("SELECT DISTINCT ancestor_name FROM pedigree_tree WHERE ancestor_name IS NOT NULL")

    return {
        "races": sorted(races - set(cache.keys())),
        "people": sorted(people - set(cache.keys())),
        "sires": sorted(sires - set(cache.keys())),
        "racers_owners": sorted((racers | breeders_owners | dams) - sires - people - races - set(cache.keys())),
        "ancestors": sorted(ancestors_5gen - racers - breeders_owners - dams - sires - people - races - set(cache.keys())),
    }


def main():
    os.makedirs("data", exist_ok=True)
    cache = {}
    if os.path.exists(CACHE_PATH):
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            cache = json.load(f)
    print(f"[*] Cache inicial carregado: {len(cache):,} entradas.")

    conn = sqlite3.connect(DB_PATH)
    cats = collect_Categorized_strings(conn, cache)

    # Normalização de sufixos de país: se "サンデーサイレンス" já está traduzido ou vamos traduzir a base,
    # reaproveitamos automaticamente para "サンデーサイレンス(USA)" -> "Sunday Silence(USA)"
    base_to_full = {}
    for cat_name, items in cats.items():
        filtered = []
        for s in items:
            m = COUNTRY_RE.match(s)
            if m:
                base, country = m.group(1).strip(), m.group(2).strip()
                if base in cache:
                    cache[s] = f"{COUNTRY_RE.sub(r'\\1', cache[base]).strip()}{country}"
                    continue
                base_to_full.setdefault(base, []).append((s, country))
                if JP_RE.search(base) and base not in cache:
                    filtered.append(base)
            else:
                filtered.append(s)
        cats[cat_name] = sorted(set(filtered) - set(cache.keys()))

    total_remaining = sum(len(v) for v in cats.values())
    print(f"[*] Total de strings japonesas base para traduzir: {total_remaining:,}")
    for k, v in cats.items():
        print(f"    - {k:15s}: {len(v):,}")

    client = genai.Client(api_key=API_KEY)
    lock = threading.Lock()
    save_counter = [0]

    def save_progress(new_items, source_tag=""):
        if not new_items:
            return
        with lock:
            cache.update(new_items)
            # Propagar sufixos de país (USA), (GB), etc.
            for base_k, tr_v in list(new_items.items()):
                if base_k in base_to_full:
                    clean_tr = COUNTRY_RE.sub(r'\1', tr_v).strip()
                    for full_s, country in base_to_full[base_k]:
                        cache[full_s] = f"{clean_tr}{country}"
            save_counter[0] += 1
            if save_counter[0] % 5 == 0 or source_tag == "FORCE":
                with open(CACHE_PATH, "w", encoding="utf-8") as f:
                    json.dump(cache, f, ensure_ascii=False, indent=2)

    # ETAPA 1: Traduzir Races, People (Jóqueis/Treinadores) e Sires prioritariamente com Gemini (com fallback GTX)
    priority_tasks = [
        ("races", cats["races"], 160),
        ("people", cats["people"], 200),
        ("sires", cats["sires"], 200),
    ]

    for cat_hint, items, bsize in priority_tasks:
        if not items:
            continue
        batches = [items[i:i + bsize] for i in range(0, len(items), bsize)]
        print(f"\n[ETAPA 1 - {cat_hint.upper()}] Traduzindo {len(items)} itens em {len(batches)} lotes (Gemini Priority)...")
        for idx, batch in enumerate(batches, 1):
            t0 = time.time()
            res, used_model = translate_batch_gemini(client, batch, category_hint=cat_hint)
            if res and len(res) >= len(batch) * 0.7:
                # Completar eventuais chaves faltantes do lote via GTX
                missing = [x for x in batch if x not in res]
                if missing:
                    res.update(translate_batch_gtx(missing))
                save_progress(res, "FORCE")
                print(f"  ✓ [{cat_hint} {idx}/{len(batches)}] {len(res)} traduzidos via {used_model} ({time.time()-t0:.1f}s) | Cache: {len(cache):,}")
            else:
                res_gtx = translate_batch_gtx(batch)
                save_progress(res_gtx, "FORCE")
                print(f"  ✓ [{cat_hint} {idx}/{len(batches)}] {len(res_gtx)} traduzidos via Hybrid-GTX ({time.time()-t0:.1f}s) | Cache: {len(cache):,}")

    # ETAPA 2: Tradução Massiva Paralela (Híbrida: Workers Gemini + Workers GTX em paralelo)
    bulk_items = [x for x in (cats["racers_owners"] + cats["ancestors"]) if x not in cache]
    if bulk_items:
        batch_size = 120
        batches = [bulk_items[i:i + batch_size] for i in range(0, len(bulk_items), batch_size)]
        print(f"\n[ETAPA 2 - BULK HÍBRIDO] Traduzindo {len(bulk_items):,} nomes em {len(batches)} lotes paralelos...")

        def process_bulk_batch(idx_batch):
            idx, batch = idx_batch
            t0 = time.time()
            # A cada 4 lotes, tenta usar um modelo Gemini disponível em paralelo; os demais usam GTX ultra-rápido
            if idx % 4 == 0:
                model_choice = [["gemini-3.5-flash-lite", "gemini-3.5-flash", "gemini-3.7-flash"][(idx // 4) % 3]]
                res, used_model = translate_batch_gemini(client, batch, category_hint="general", models=model_choice)
                if res and len(res) >= len(batch) * 0.8:
                    missing = [x for x in batch if x not in res]
                    if missing:
                        res.update(translate_batch_gtx(missing))
                    save_progress(res)
                    return idx, len(res), used_model, time.time() - t0

            # Fast GTX batch
            for attempt in range(3):
                try:
                    res = translate_batch_gtx(batch)
                    save_progress(res)
                    return idx, len(res), "Hybrid-Batch", time.time() - t0
                except Exception as e:
                    time.sleep(1.5 * (attempt + 1))
            return idx, 0, "FAILED", time.time() - t0

        completed = 0
        with ThreadPoolExecutor(max_workers=6) as pool:
            futures = [pool.submit(process_bulk_batch, (i + 1, b)) for i, b in enumerate(batches)]
            for fut in as_completed(futures):
                idx, count, engine, elapsed = fut.result()
                completed += 1
                if completed % 10 == 0 or completed == len(batches) or engine.startswith("gemini"):
                    print(f"  [{completed}/{len(batches)}] Lote #{idx}: {count} nomes via {engine} ({elapsed:.1f}s) | Cache Total: {len(cache):,}", flush=True)

    # Forçar salvamento final e garantir todas as chaves com sufixo de país
    save_progress({}, "FORCE")
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Tradução Híbrida Concluída! Total no cache ({CACHE_PATH}): {len(cache):,} entradas.")
    conn.close()


if __name__ == "__main__":
    main()
