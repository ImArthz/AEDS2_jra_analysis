import sqlite3
import json
import time
import sys
import os
from google import genai
from google.genai import types

sys.stdout.reconfigure(encoding='utf-8')

API_KEY = "YOUR_API_KEY_HERE"
client = genai.Client(api_key=API_KEY)

print("Starting DB scan for unique names...", flush=True)
conn = sqlite3.connect("data/sqlite/jra_graded.db")
cur = conn.cursor()

queries = [
    "SELECT name FROM horses WHERE name IS NOT NULL",
    "SELECT breeder FROM horses WHERE breeder IS NOT NULL",
    "SELECT owner FROM horses WHERE owner IS NOT NULL",
    "SELECT horse_name FROM race_entries WHERE horse_name IS NOT NULL",
    "SELECT jockey FROM race_entries WHERE jockey IS NOT NULL",
    "SELECT trainer FROM race_entries WHERE trainer IS NOT NULL",
    "SELECT ancestor_name FROM pedigree_tree WHERE ancestor_name IS NOT NULL"
]

unique_names = set()
for q in queries:
    cur.execute(q)
    for row in cur.fetchall():
        val = str(row[0]).strip()
        if val:
            unique_names.add(val)

unique_names = list(unique_names)
print(f"Total Katakana/Japanese names found: {len(unique_names)}", flush=True)

trans_dict = {}
if os.path.exists("data/gemini_cache.json"):
    try:
        with open("data/gemini_cache.json", "r", encoding="utf-8") as f:
            trans_dict = json.load(f)
        print(f"Loaded {len(trans_dict)} names from cache.", flush=True)
    except Exception as e:
        print("Error loading cache:", e)

names_to_translate = [n for n in unique_names if n not in trans_dict]
print(f"Remaining to translate: {len(names_to_translate)} names.", flush=True)

batch_size = 200
batches = [names_to_translate[i:i + batch_size] for i in range(0, len(names_to_translate), batch_size)]

prompt = "Translate the following list of Japanese horse racing names and terms to their OFFICIAL English spelling (e.g. ????????? -> Deep Impact). If it is a Japanese person's name, return the correct Hepburn Romaji. Return ONLY a valid JSON dictionary."

if names_to_translate:
    print(f"Starting translation in {len(batches)} batches...", flush=True)
    
    for i, batch in enumerate(batches):
        content_list = chr(10).join(batch)
        
        success = False
        attempts = 0
        while not success:
            try:
                print(f"Processing batch {i+1}/{len(batches)} (Attempt {attempts+1})...", flush=True)
                response = client.models.generate_content(
                    model="gemini-3.6-flash",
                    contents=prompt + chr(10)*2 + content_list,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json"
                    )
                )
                
                raw_text = response.text.strip()
                if raw_text.startswith("`"):
                    raw_text = raw_text.split(chr(10), 1)[1]
                if raw_text.endswith("`"):
                    raw_text = raw_text[:-3]
                    
                batch_dict = json.loads(raw_text)
                trans_dict.update(batch_dict)
                
                with open("data/gemini_cache.json", "w", encoding="utf-8") as f:
                    json.dump(trans_dict, f, ensure_ascii=False, indent=4)
                    
                print(f"Batch {i+1} saved! Sleeping 10s...", flush=True)
                time.sleep(10)
                success = True
            except Exception as e:
                attempts += 1
                error_msg = str(e)
                print(f"\n[ERROR] Failed at batch {i+1}: {error_msg}", flush=True)
                if "503" in error_msg or "429" in error_msg:
                    sleep_time = 30 * attempts
                    print(f"Google API overloaded/rate-limited. Retrying in {sleep_time}s...", flush=True)
                    time.sleep(sleep_time)
                else:
                    print("Fatal error format. Retrying in 30s...", flush=True)
                    time.sleep(30)

print("\nDone! All translations saved to data/gemini_cache.json!", flush=True)
