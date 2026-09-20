"""
Módulo de Tradução JP → EN
Cria uma cópia do banco SQLite com todos os campos textuais traduzidos para inglês.
Usa dicionários estáticos (sem API externa) para tradução consistente e rápida.
"""

import sys
import os
import re
import sqlite3
import pandas as pd
from database import get_connection, DB_PATH

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# ================================================================
# DICIONÁRIOS DE TRADUÇÃO
# ================================================================

# Hipódromos
TRACK_MAP = {
    '東京': 'Tokyo', '中山': 'Nakayama', '阪神': 'Hanshin', '京都': 'Kyoto',
    '中京': 'Chukyo', '小倉': 'Kokura', '新潟': 'Niigata', '福島': 'Fukushima',
    '札幌': 'Sapporo', '函館': 'Hakodate',
}

# Superfície
SURFACE_MAP = {
    'Turf': 'Turf', 'Dirt': 'Dirt', 'Obstacle': 'Obstacle',
    '芝': 'Turf', 'ダート': 'Dirt', 'ダ': 'Dirt', '障害': 'Obstacle', '障': 'Obstacle',
}

# Condição da pista
GOING_MAP = {
    '良': 'Firm', '稍重': 'Good to Soft', '稍': 'Good to Soft',
    '重': 'Soft', '不良': 'Heavy', '不': 'Heavy',
    'Firm': 'Firm', 'Good to Soft': 'Good to Soft', 'Soft': 'Soft', 'Heavy': 'Heavy',
}

# Clima
WEATHER_MAP = {
    '晴': 'Fine', '曇': 'Cloudy', '雨': 'Rain', '小雨': 'Light Rain', '雪': 'Snow',
    'Fine': 'Fine', 'Cloudy': 'Cloudy', 'Rain': 'Rain', 'Light Rain': 'Light Rain', 'Snow': 'Snow',
}

# Sexo
SEX_MAP = {
    '牡': 'Male', '牝': 'Female', 'セン': 'Gelding', 'セ': 'Gelding',
    'Male': 'Male', 'Female': 'Female', 'Gelding': 'Gelding',
}

# Grade (normalizar caracteres full-width)
GRADE_MAP = {
    'G1': 'G1', 'G2': 'G2', 'G3': 'G3',
    'GⅠ': 'G1', 'GⅡ': 'G2', 'GⅢ': 'G3',
    'ＧⅠ': 'G1', 'ＧⅡ': 'G2', 'ＧⅢ': 'G3',
}

# Nomes de corridas famosas (principais G1)
RACE_NAME_MAP = {
    'フェブラリーＳ': 'February Stakes', 'フェブラリーS': 'February Stakes',
    '高松宮記念': 'Takamatsunomiya Kinen',
    '大阪杯': 'Osaka Hai',
    '桜花賞': 'Oka Sho (Japanese 1000 Guineas)',
    '皐月賞': 'Satsuki Sho (Japanese 2000 Guineas)',
    '天皇賞（春）': "Emperor's Cup (Spring)", '天皇賞（秋）': "Emperor's Cup (Autumn)",
    'ＮＨＫマイルＣ': 'NHK Mile Cup', 'NHKマイルC': 'NHK Mile Cup',
    'オークス': 'Yushun Himba (Japanese Oaks)',
    '日本ダービー': 'Tokyo Yushun (Japanese Derby)',
    '安田記念': 'Yasuda Kinen',
    '宝塚記念': 'Takarazuka Kinen',
    'スプリンターズＳ': 'Sprinters Stakes', 'スプリンターズS': 'Sprinters Stakes',
    '秋華賞': 'Shuka Sho',
    '菊花賞': 'Kikuka Sho (Japanese St. Leger)',
    'エリザベス女王杯': 'Queen Elizabeth II Cup',
    'マイルチャンピオンシップ': 'Mile Championship',
    'ジャパンＣ': 'Japan Cup', 'ジャパンC': 'Japan Cup',
    'ジャパンＣダート': 'Japan Cup Dirt',
    'チャンピオンズＣ': 'Champions Cup', 'チャンピオンズC': 'Champions Cup',
    '阪神ジュベナイルＦ': 'Hanshin Juvenile Fillies',
    '朝日杯フューチュリティＳ': 'Asahi Hai Futurity Stakes',
    '有馬記念': 'Arima Kinen',
    '中山グランドジャンプ': 'Nakayama Grand Jump',
    '中山大障害': 'Nakayama Daishogai',
    # G2 comuns
    '日経新春杯': 'Nikkei Shinshun Hai',
    '京都記念': 'Kyoto Kinen',
    '阪神大賞典': 'Hanshin Daishoten',
    '産経大阪杯': 'Sankei Osaka Hai',
    '毎日杯': 'Mainichi Hai',
    'スプリングＳ': 'Spring Stakes',
    '青葉賞': 'Aoba Sho',
    'セントライト記念': 'St. Lite Kinen',
    '神戸新聞杯': 'Kobe Shimbun Hai',
    'ローズＳ': 'Rose Stakes',
    'フローラＳ': 'Flora Stakes',
    # G3 comuns
    '中山金杯': 'Nakayama Kimpai',
    '京都金杯': 'Kyoto Kimpai',
    'フェアリーＳ': 'Fairy Stakes', 'フェアリーS': 'Fairy Stakes',
    'シンザン記念': 'Shinzan Kinen',
    '京成杯': 'Keisei Hai',
    '愛知杯': 'Aichi Hai',
    '小倉牝馬Ｓ': 'Kokura Himba Stakes',
}

# Margem de vitória
MARGIN_MAP = {
    'クビ': 'Neck', 'ハナ': 'Nose', 'アタマ': 'Head',
    '大差': 'Distance',
}


def translate_text(text, mapping):
    """Traduz um texto usando dicionário. Retorna original se não encontrar."""
    if not text or pd.isna(text):
        return text
    text = str(text).strip()
    if text in mapping:
        return mapping[text]
    return text


def translate_race_name(name):
    """Traduz nome de corrida. Tenta match exato primeiro, depois parcial."""
    if not name or pd.isna(name):
        return name
    name = str(name).strip()
    
    # Match exato
    if name in RACE_NAME_MAP:
        return RACE_NAME_MAP[name]
    
    # Remover prefixo de grade e tentar de novo
    clean = re.sub(r'^[GＧ][ⅠⅡⅢ123]\s*', '', name).strip()
    if clean in RACE_NAME_MAP:
        return RACE_NAME_MAP[clean]
    
    # Se não encontrou, retornar original (mantém em japonês)
    return name


def translate_margin(margin):
    """Traduz margem de vitória."""
    if not margin or pd.isna(margin):
        return margin
    margin = str(margin).strip()
    
    # Margens exatas
    if margin in MARGIN_MAP:
        return MARGIN_MAP[margin]
    
    # Padrões: "１／２馬身" -> "1/2 lengths"
    m = re.search(r'([\d１２３４５６７８９０]+)(?:[／/]([\d１２３４５６７８９０]+))?馬身', margin)
    if m:
        # Converter full-width para half-width
        def fw_to_hw(s):
            if not s: return ''
            return s.translate(str.maketrans('０１２３４５６７８９', '0123456789'))
        
        whole = fw_to_hw(m.group(1)) if m.group(1) else ''
        frac = fw_to_hw(m.group(2)) if m.group(2) else ''
        
        if frac:
            return f"{whole}/{frac} lengths" if whole else f"1/{frac} lengths"
        return f"{whole} lengths"
    
    # Frações soltas: "１1/4馬身"
    m2 = re.search(r'([\d１-９]+)\s*([\d]+)/([\d]+)\s*馬身', margin)
    if m2:
        return f"{m2.group(1)} {m2.group(2)}/{m2.group(3)} lengths"
    
    return translate_text(margin, MARGIN_MAP)


def create_english_db(source_db=None, target_db=None):
    """Cria uma cópia traduzida do banco em inglês."""
    if source_db is None:
        source_db = DB_PATH
    if target_db is None:
        target_db = source_db.replace('.db', '_en.db')
    
    print(f"\n{'='*60}")
    print(f"  Tradução JP → EN")
    print(f"  Origem:  {source_db}")
    print(f"  Destino: {target_db}")
    print(f"{'='*60}\n")
    
    # Remover destino se existir
    if os.path.exists(target_db):
        os.remove(target_db)
        print("[DB] Banco EN anterior removido.")
    
    conn_src = sqlite3.connect(source_db)
    conn_dst = sqlite3.connect(target_db)
    conn_dst.execute("PRAGMA journal_mode = WAL;")
    
    # 1. Copiar schema
    schema_sql = conn_src.execute("SELECT sql FROM sqlite_master WHERE type='table'").fetchall()
    for (sql,) in schema_sql:
        if sql:
            conn_dst.execute(sql)
    
    # Copiar índices
    idx_sql = conn_src.execute("SELECT sql FROM sqlite_master WHERE type='index' AND sql IS NOT NULL").fetchall()
    for (sql,) in idx_sql:
        try:
            conn_dst.execute(sql)
        except Exception:
            pass
    conn_dst.commit()
    
    # 2. Traduzir e copiar races
    print("[Traduzindo] races...")
    df_races = pd.read_sql_query("SELECT * FROM races", conn_src)
    if not df_races.empty:
        df_races['track'] = df_races['track'].apply(lambda x: translate_text(x, TRACK_MAP))
        df_races['surface'] = df_races['surface'].apply(lambda x: translate_text(x, SURFACE_MAP))
        df_races['going'] = df_races['going'].apply(lambda x: translate_text(x, GOING_MAP))
        df_races['weather'] = df_races['weather'].apply(lambda x: translate_text(x, WEATHER_MAP))
        df_races['grade'] = df_races['grade'].apply(lambda x: translate_text(x, GRADE_MAP))
        df_races['race_name'] = df_races['race_name'].apply(translate_race_name)
        df_races.to_sql('races', conn_dst, if_exists='append', index=False)
        print(f"  ✓ {len(df_races)} corridas traduzidas")
    
    # 3. Traduzir e copiar race_entries
    print("[Traduzindo] race_entries...")
    df_entries = pd.read_sql_query("SELECT * FROM race_entries", conn_src)
    if not df_entries.empty:
        df_entries['sex'] = df_entries['sex'].apply(lambda x: translate_text(x, SEX_MAP))
        df_entries['margin'] = df_entries['margin'].apply(translate_margin)
        # Nomes de cavalos e jóqueis ficam em japonês (são nomes próprios)
        df_entries.to_sql('race_entries', conn_dst, if_exists='append', index=False)
        print(f"  ✓ {len(df_entries)} entradas traduzidas")
    
    # 4. Copiar horses (nomes próprios mantidos em JP)
    print("[Copiando] horses...")
    df_horses = pd.read_sql_query("SELECT * FROM horses", conn_src)
    if not df_horses.empty:
        df_horses['sex'] = df_horses['sex'].apply(lambda x: translate_text(x, SEX_MAP))
        df_horses.to_sql('horses', conn_dst, if_exists='append', index=False)
        print(f"  ✓ {len(df_horses)} cavalos")
    
    # 5. Copiar pedigree (nomes próprios)
    print("[Copiando] pedigree...")
    for table in ['pedigree', 'pedigree_tree']:
        try:
            df = pd.read_sql_query(f"SELECT * FROM {table}", conn_src)
            if not df.empty:
                df.to_sql(table, conn_dst, if_exists='append', index=False)
                print(f"  ✓ {len(df)} registros em {table}")
        except Exception:
            print(f"  - {table}: vazio ou não existe")
    
    conn_src.close()
    conn_dst.close()
    
    print(f"\n✅ Banco traduzido salvo em: {target_db}")
    
    # Exportar CSVs em inglês
    csv_en_dir = os.path.join(os.path.dirname(target_db), '..', 'csv_en')
    os.makedirs(csv_en_dir, exist_ok=True)
    
    conn_en = sqlite3.connect(target_db)
    for table in ['races', 'race_entries', 'horses', 'pedigree', 'pedigree_tree']:
        try:
            df = pd.read_sql_query(f"SELECT * FROM {table}", conn_en)
            out = os.path.join(csv_en_dir, f"{table}.csv")
            df.to_csv(out, index=False, encoding='utf-8-sig')
            print(f"[CSV-EN] {table}: {len(df)} → {out}")
        except Exception:
            pass
    conn_en.close()
    
    return target_db


if __name__ == "__main__":
    create_english_db()
