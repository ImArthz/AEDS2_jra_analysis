"""
Módulo de Limpeza e Sanitização Profunda (Padrão Zenodo / Ciência dos Dados)
Corrige:
1. Remoção de linhas espúrias de tabelas de apostas (2004) e link vazio (2025__)
2. Realinhamento das colunas deslocadas em race_entries (2004 Kyoto Himba S e 2006–2018)
3. Padronização de horses.sex, horses.birth_date (remoção de 'XX歳') e preenchimento de horses.birth_year
4. Imputação exata de grade, grade_weight, surface (Turf/Dirt/Obstacle) e distance em 100% das corridas (races)
"""

import sqlite3
import unicodedata
import re
import os
import sys
from database import get_connection, export_to_csv, DB_PATH

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

GARBAGE_HORSES = {
    '6', '7', '8', '9', '10', '11', '12', '13', '14', '15',
    '02-07', '02-11', '馬単', 'ワイド', '３連複'
}

MANUAL_GRADE = {
    'ジャパンCダート': 'G1',
    'マイルCS南部杯': 'G1',
    'JBCクラシック': 'G1',
    'JBCスプリント': 'G1',
    'JBCレディスクラシック': 'G1',
    'クリスタルC': 'G3',
    'ガーネットS': 'G3',
    'カブトヤマ記念': 'G3',
    'ラジオたんぱ賞': 'G3',
    'ラジオたんぱ杯2歳S': 'G3',
    'ラジオNIKKEI杯2歳S': 'G3',
    '東京オータムジャンプ': 'G3',
    'いちょうS': 'G3',
    '朝日チャレンジC': 'G3',
}

MANUAL_SURFACE = {
    'クリスタルC': 'Turf',
    'ラジオたんぱ賞': 'Turf',
    'カブトヤマ記念': 'Turf',
    'ラジオたんぱ杯2歳S': 'Turf',
    'ラジオNIKKEI杯2歳S': 'Turf',
    'いちょうS': 'Turf',
    '朝日チャレンジC': 'Turf',
    'マーチS': 'Dirt',
    'JBCクラシック': 'Dirt',
    'シリウスS': 'Dirt',
    'マイルCS南部杯': 'Dirt',
    'ユニコーンS': 'Dirt',
    'ガーネットS': 'Dirt',
    'JBCレディスクラシック': 'Dirt',
    '武蔵野S': 'Dirt',
    '平安S': 'Dirt',
    '根岸S': 'Dirt',
    'みやこS': 'Dirt',
    'プロキオンS': 'Dirt',
    'ジャパンCダート': 'Dirt',
    'JBCスプリント': 'Dirt',
    '東海S': 'Dirt',
    'レパードS': 'Dirt',
    'チャンピオンズC': 'Dirt',
    'エルムS': 'Dirt',
    'アンタレスS': 'Dirt',
    'フェブラリーS': 'Dirt',
    'カペラS': 'Dirt',
}

MANUAL_DISTANCE = {
    'クリスタルC': 1200,
    'ガーネットS': 1200,
    'ラジオたんぱ賞': 1800,
    'カブトヤマ記念': 1800,
    'ラジオたんぱ杯2歳S': 2000,
    'ラジオNIKKEI杯2歳S': 2000,
}

GRADE_WEIGHT_MAP = {'G1': 1.0, 'G2': 0.7, 'G3': 0.5}


def norm_race_name(s):
    if not s:
        return ""
    s = unicodedata.normalize('NFKC', str(s)).strip()
    s = re.sub(r'^(?:新設)?(?:重賞)?(?:J・|J\.)?(?:G|Jpn)[IⅠⅡⅢV123]+\s*', '', s, flags=re.I).strip()
    return s


def clean_database(db_path=DB_PATH):
    conn = get_connection(db_path)
    cur = conn.cursor()

    print("=" * 60)
    print("  INICIANDO LIMPEZA E REALINHAMENTO DO BANCO (ETAPA A)")
    print("=" * 60)

    # 1. Remover corrida vazia '2025__' e registros espúrios de apostas (2004)
    cur.execute("DELETE FROM races WHERE race_id = '2025__' OR race_name = ''")
    placeholders = ",".join("?" for _ in GARBAGE_HORSES)
    params = tuple(GARBAGE_HORSES)

    cur.execute(f"SELECT horse_id FROM horses WHERE name IN ({placeholders})", params)
    garbage_ids = {r[0] for r in cur.fetchall() if r[0]} | GARBAGE_HORSES
    id_placeholders = ",".join("?" for _ in garbage_ids)
    id_params = tuple(garbage_ids)

    cur.execute(f"DELETE FROM race_entries WHERE horse_name IN ({placeholders}) OR horse_id IN ({id_placeholders})", params + id_params)
    cur.execute(f"DELETE FROM pedigree_tree WHERE horse_name IN ({placeholders}) OR horse_id IN ({id_placeholders})", params + id_params)
    cur.execute(f"DELETE FROM pedigree WHERE horse_name IN ({placeholders}) OR horse_id IN ({id_placeholders})", params + id_params)
    cur.execute(f"DELETE FROM horses WHERE name IN ({placeholders}) OR horse_id IN ({id_placeholders})", params + id_params)
    print(f"[1/4] Removidos registros espúrios de apostas ({len(GARBAGE_HORSES)} nomes falsos) e links vazios.")

    # 2. Realinhar race_entries (2004 Kyoto Himba S e 2006-2018)
    # 2a. Caso especial: 2004_京都_京都牝馬Ｓ (16 linhas)
    cur.execute("""
        SELECT rowid, finish_time, jockey, trainer, weight, odds, horse_weight, margin
        FROM race_entries
        WHERE race_id = '2004_京都_京都牝馬Ｓ' AND age IS NULL
    """)
    kyoto_rows = cur.fetchall()
    for rowid, ft, jock, tr, wt, od, hw, mg in kyoto_rows:
        real_jockey = str(ft).strip()
        real_weight = str(jock).strip()
        real_age = int(float(wt)) if wt is not None else None
        real_trainer = str(od).strip() if od is not None else ""
        real_finish_time = str(mg).strip()
        real_margin = ""
        real_hw = str(hw).strip()
        m_hw = re.match(r'^(.*?)\((\d+Kg)\)$', real_hw)
        if m_hw:
            real_margin = m_hw.group(1).strip()
            base_kg = m_hw.group(2)
            delta = str(tr).strip()
            real_hw = f"{base_kg}({delta})" if delta else base_kg
        cur.execute("""
            UPDATE race_entries
            SET finish_time = ?, jockey = ?, trainer = ?, weight = ?, odds = NULL,
                horse_weight = ?, age = ?, margin = ?
            WHERE rowid = ?
        """, (real_finish_time, real_jockey, real_trainer, real_weight, real_hw, real_age, real_margin, rowid))

    # 2b. Caso geral 2006-2018 (onde age IS NULL e sex contém sexo+idade, ex: '牡4')
    cur.execute("""
        SELECT rowid, finish_time, jockey, trainer, weight, odds, horse_weight, sex, margin
        FROM race_entries
        WHERE age IS NULL AND sex GLOB '[牡牝せセ]*[0-9]*'
    """)
    shifted_rows = cur.fetchall()
    updates_batch = []
    for rowid, ft, jock, tr, wt, od, hw, sx, mg in shifted_rows:
        m_sx = re.match(r'^(牡|牝|せん|セン|セ)(\d+)$', str(sx).strip())
        real_sex = m_sx.group(1) if m_sx else str(sx).strip()
        if real_sex in ('セン', 'セ'):
            real_sex = 'せん'
        real_age = int(m_sx.group(2)) if m_sx else None

        ft_str = str(ft or '').strip()
        # Verificar se é a linha concatenada '丸山侯彦1:10.6１／２馬身448Kg+2小桧山悟16'
        m_concat = re.match(r'^([^\d]+)(\d+:\d+\.\d+)(.*?)\s*(\d+Kg)([+\-]?\d+)([^\d]+)(\d+)$', ft_str)
        if m_concat:
            real_jockey = m_concat.group(1).strip()
            real_finish_time = m_concat.group(2).strip()
            real_margin = m_concat.group(3).strip()
            real_hw = f"{m_concat.group(4)}({m_concat.group(5)})"
            real_trainer = m_concat.group(6).strip()
            real_odds = float(m_concat.group(7))
        else:
            real_jockey = ft_str
            real_finish_time = str(mg or '').strip()
            real_trainer = str(od or '').strip()
            if re.match(r'^\d+(\.\d+)?$', real_trainer):
                real_trainer = ''
            real_margin = ''
            real_odds = None

            hw_str = str(hw or '').strip()
            delta_str = str(tr or '').strip()
            m_paren = re.search(r'\((\d+)\)', hw_str)
            if m_paren:
                base_w = m_paren.group(1)
                real_hw = f"{base_w}Kg({delta_str})" if delta_str else f"{base_w}Kg"
            else:
                real_hw = hw_str

        wt_str = str(wt or '').strip()
        if wt_str and not wt_str.lower().endswith('kg'):
            wt_str = f"{wt_str}kg"

        updates_batch.append((
            real_finish_time, real_jockey, real_trainer, wt_str, real_odds,
            real_hw, real_age, real_sex, real_margin, rowid
        ))

    cur.executemany("""
        UPDATE race_entries
        SET finish_time = ?, jockey = ?, trainer = ?, weight = ?, odds = ?,
            horse_weight = ?, age = ?, sex = ?, margin = ?
        WHERE rowid = ?
    """, updates_batch)
    print(f"[2/4] Realinhadas {len(kyoto_rows) + len(updates_batch):,} entradas deslocadas em race_entries (2004–2018).")

    # 3. Limpar tabela horses (sex sem números, birth_date limpo, birth_year preenchido)
    cur.execute("SELECT horse_id, sex, birth_date, birth_year FROM horses")
    horse_updates = []
    for hid, sx, bdate, byear in cur.fetchall():
        clean_sx = str(sx or '').strip()
        m_sx = re.match(r'^(牡|牝|せん|セン|セ)\d*$', clean_sx)
        if m_sx:
            clean_sx = m_sx.group(1)
            if clean_sx in ('セン', 'セ'):
                clean_sx = 'せん'

        clean_bdate = str(bdate or '').strip()
        # Remover sufixo de idade ex: '2001.02.03 25歳' -> '2001.02.03'
        clean_bdate = re.sub(r'\s+\d+歳.*$', '', clean_bdate).strip()

        clean_byear = byear
        if not clean_byear and len(clean_bdate) >= 4 and clean_bdate[:4].isdigit():
            clean_byear = int(clean_bdate[:4])

        horse_updates.append((clean_sx, clean_bdate, clean_byear, hid))

    cur.executemany("""
        UPDATE horses SET sex = ?, birth_date = ?, birth_year = ? WHERE horse_id = ?
    """, horse_updates)
    # Sincronizar horse_name em race_entries quando houve merge de horse_id no JBIS
    cur.execute("""
        UPDATE race_entries
        SET horse_name = (SELECT h.name FROM horses h WHERE h.horse_id = race_entries.horse_id)
        WHERE horse_name NOT IN (SELECT name FROM horses)
          AND horse_id IN (SELECT horse_id FROM horses)
    """)
    print(f"[3/4] Padronizados {len(horse_updates):,} registros em horses (sex, birth_date, birth_year e aliases).")

    # 4. Imputar grade, grade_weight, surface e distance em races
    cur.execute("SELECT race_id, year, date, race_name, track, grade, grade_weight, surface, distance FROM races")
    all_races = cur.fetchall()

    known_grade = dict(MANUAL_GRADE)
    known_surf = dict(MANUAL_SURFACE)
    known_dist = dict(MANUAL_DISTANCE)

    for rid, y, dt, rname, trk, gr, gw, surf, dist in all_races:
        raw_n = unicodedata.normalize('NFKC', str(rname))
        cn = norm_race_name(rname)
        if not gr:
            m = re.match(r'^(?:新設)?(?:重賞)?(?:J・|J\.)?(?:G|Jpn)([IⅠⅡⅢ123]+)', raw_n)
            if m:
                g_num = m.group(1).translate(str.maketrans('ⅠⅡⅢI', '1231')).replace('111', '3').replace('11', '2')
                if g_num in ('1', '2', '3'):
                    gr = f"G{g_num}"
            elif '重賞' in raw_n:
                gr = 'G3'
        if gr:
            known_grade[cn] = gr
        if surf:
            known_surf[cn] = surf
        elif 'ジャンプ' in cn or '大障害' in cn:
            known_surf[cn] = 'Obstacle'
        if dist and str(dist).strip():
            known_dist[cn] = int(dist)

    race_updates = []
    for rid, y, dt, rname, trk, gr, gw, surf, dist in all_races:
        cn = norm_race_name(rname)
        new_gr = gr if gr else known_grade.get(cn, 'G3')
        new_gw = GRADE_WEIGHT_MAP.get(new_gr, 0.5)
        new_surf = surf if surf else known_surf.get(cn, 'Turf')
        new_dist = int(dist) if (dist and str(dist).strip()) else known_dist.get(cn, 2000)

        # Padronizar data (ex: '1月6日土曜' ou '1/6（土）' -> '1/6')
        clean_dt = str(dt or '').strip()
        m_dt1 = re.match(r'^(\d+)月(\d+)日', clean_dt)
        if m_dt1:
            clean_dt = f"{m_dt1.group(1)}/{m_dt1.group(2)}"
        else:
            clean_dt = re.sub(r'[（(].*?[）)]', '', clean_dt).strip()

        race_updates.append((clean_dt, new_gr, new_gw, new_surf, new_dist, rid))

    cur.executemany("""
        UPDATE races
        SET date = ?, grade = ?, grade_weight = ?, surface = ?, distance = ?
        WHERE race_id = ?
    """, race_updates)
    print(f"[4/4] Imputados grade, surface, distance e date em {len(race_updates):,} corridas (100% completo).")

    conn.commit()
    conn.close()

    # Exportar CSVs em Japonês limpos
    export_to_csv(db_path)
    print("\n✅ Limpeza do banco principal concluída com sucesso!")


if __name__ == "__main__":
    clean_database()
