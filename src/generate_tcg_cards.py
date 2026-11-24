"""
Gerador da Arena Gamificada de Cards & Ranking Interativo (JRA & JBIS TCG Dex Explorer) — v2.0 (QA Hardened)
Converte as matrizes matemáticas (PageRank, Inbreeding F_X, K-Means++ PCA, Ganhos, Sires e Jóqueis)
em uma aplicação web gamificada estilo Trading Card Game (TCG) / Interactive Leaderboard.

Responsivo para Mobile (Android/iOS 360px+) e Desktop (Windows/Linux), com troca instantânea
de idioma 100% completa (Português 🇧🇷 | English 🇺🇸 | 日本語 🇯🇵), busca normalizada (imune a apóstrofos),
filtros de raridade, botão Reset, contador de resultados, 6 Decks de Ranking, Modal 3D Expansível
com Guia Leigo, Gráfico Radar responsivo e Árvore Genealógica Clicável, e Modo Duelo (VS Mode).
"""

import os
import re
import json
import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(BASE_DIR)

CSV_EN_DIR = os.path.join(BASE_DIR, "data", "csv_en")
CSV_JA_DIR = os.path.join(BASE_DIR, "data", "csv")
ANALYSIS_DIR = os.path.join(BASE_DIR, "data", "analysis")
DOCS_DIR = os.path.join(BASE_DIR, "docs")

# Dicionário Katakana/Kanji canônico para Patriarcas Fundadores 5-Gen, Garanhões Internacionais e Jóqueis
CANONICAL_JA_MAP = {
    "Northern Dancer": "ノーザンダンサー",
    "Hail to Reason": "ヘイルトゥリーズン",
    "Nasrullah": "ナスルーラ",
    "Mr. Prospector": "ミスタープロスペクター",
    "Native Dancer": "ネイティヴダンサー",
    "Almahmoud": "アルマームード",
    "Raise a Native": "レイズアネイティヴ",
    "Halo": "ヘイロー",
    "Nearco": "ネアルコ",
    "Nearctic": "ニアークティック",
    "Turn-to": "ターントゥ",
    "Bold Ruler": "ボールドルーラー",
    "Nashua": "ナシュア",
    "Nijinsky": "ニジンスキー",
    "Buckpasser": "バックパッサー",
    "Hyperion": "ハイペリオン",
    "Lyphard": "リファール",
    "Princequillo": "プリンスキロ",
    "Natalma": "ナタルマ",
    "Lady Angela": "レディアンジェラ",
    "Northern Taste": "ノーザンテースト",
    "Tom Fool": "トムフール",
    "Special": "スペシャル",
    "Ribot": "リボー",
    "Princely Gift": "プリンスリーギフト",
    "Never Bend": "ネヴァーベンド",
    "Secretariat": "セクレタリアト",
    "Roberto": "ロベルト",
    "In Reality": "インリアリティ",
    "Nureyev": "ヌレイエフ",
    "Sunday Silence": "サンデーサイレンス",
    "Brian's Time": "ブライアンズタイム",
    "Kingmambo": "キングマンボ",
    "Giant's Causeway": "ジャイアンツコーズウェイ",
    "Singspiel": "シングスピール",
    "Tony Bin": "トニービン",
    "Kurofune": "クロフネ",
    "Symboli Kris S": "シンボリクリスエス",
    "Grass Wonder": "グラスワンダー",
    "El Condor Pasa": "エルコンドルパサー",
    "Taiki Shuttle": "タイキシャトル",
    "End Sweep": "エンドスウィープ",
    "French Deputy": "フレンチデピュティ",
    "Harbinger": "ハービンジャー",
    "Opera House": "オペラハウス",
    "Timber Country": "ティンバーカントリー",
    "Forty Niner": "フォーティナイナー",
    "Wild Rush": "ワイルドラッシュ",
    "Agnes Digital": "アグネスデジタル",
    "Swept Overboard": "スウェプトオーヴァーボード",
    "Danehill": "デインヒル",
    "War Emblem": "ウォーエンブレム",
    "Falbrav": "ファルブラヴ",
    "Chief Bearhart": "チーフベアハート",
    "Commander in Chief": "コマンダーインチーフ",
    "Bago": "バゴ",
    "Storming Home": "ストーミングホーム",
    "Rodrigo de Triano": "ロドリゴデトリアーノ",
    "Kinshasa No Kiseki": "キンシャサノキセキ",
    "Dancing Brave": "ダンシングブレーヴ",
    "Real Shadai": "リアルシャダイ",
    "Lammtarra": "ラムタラ",
    "Afleet": "アフリート",
    "Twining": "トワイニング",
    "Meiner Love": "マイネルラヴ",
    "Star of Cozzene": "スターオブコジーン",
    "Roses in May": "ロージズインメイ",
    "Empire Maker": "エンパイアメーカー",
    "Jade Robbery": "ジェイドロバリー",
    "Paradise Creek": "パラダイスクリーク",
    "Pentire": "ペンタイア",
    "Warning": "ウォーニング",
    "No Attention": "ノーアテンション",
    "Hennessy": "ヘネシー",
    "Elicio": "エリシオ",
    "Yutaka Take": "武豊",
    "Koshiro Take": "武幸四郎",
    "Katsumi Ando": "安藤勝己",
    "M. Demuro": "M.デムーロ",
    "C. Lemaire": "C.ルメール",
    "O. Peslier": "O.ペリエ",
    "R. Moore": "R.ムーア",
    "Yuga Kawada": "川田将雅",
    "Yuichi Fukunaga": "福永祐一",
    "Norihiro Yokoyama": "横山典弘",
    "Masayoshi Ebina": "蛯名正義",
    "Hiroyuki Uchida": "内田博幸",
    "Hirofumi Shii": "四位洋文",
    "Shinji Fujita": "藤田伸二",
    "Kenichi Ikezoe": "池添謙一",
    "Hironobu Tanabe": "田辺裕信",
    "Katsuharu Tanaka": "田中勝春",
    "Yuzo Shirahama": "白浜雄造",
    "Mitsuaki Hayashi": "林満明",
    "Mamoru Ishibashi": "石橋守",
    "Shigefumi Kumazawa": "熊沢重文",
}

SIMP_TO_JA_KANJI = str.maketrans("丰胜谦边滨满桥", "豊勝謙辺浜満橋")


def clean_en_entity(val):
    if pd.isna(val):
        return ""
    s = str(val).strip()
    if "kumazawa" in s.lower() and "heritage" in s.lower():
        return "Shigefumi Kumazawa"
    return s


def clean_ja_entity(val):
    if pd.isna(val):
        return ""
    s = str(val).strip()
    s = re.sub(r"^サラ[\s　]+", "", s)
    s = s.translate(SIMP_TO_JA_KANJI)
    return s.strip()


def build_tcg_dataset():
    print("[TCG Builder v2.0] Carregando bases de dados...")
    races = pd.read_csv(os.path.join(CSV_EN_DIR, "races.csv"), low_memory=False)
    entries = pd.read_csv(os.path.join(CSV_EN_DIR, "race_entries.csv"), low_memory=False)
    entries_ja = pd.read_csv(os.path.join(CSV_JA_DIR, "race_entries.csv"), low_memory=False)
    horses_en = pd.read_csv(os.path.join(CSV_EN_DIR, "horses.csv"), low_memory=False)
    horses_ja = pd.read_csv(os.path.join(CSV_JA_DIR, "horses.csv"), low_memory=False)
    pedigree_en = pd.read_csv(os.path.join(CSV_EN_DIR, "pedigree.csv"), low_memory=False)
    pedigree_ja = pd.read_csv(os.path.join(CSV_JA_DIR, "pedigree.csv"), low_memory=False)
    pr_df = pd.read_csv(os.path.join(ANALYSIS_DIR, "pagerank_full_ranking.csv"), low_memory=False)
    clusters_df = pd.read_csv(os.path.join(ANALYSIS_DIR, "ml_sire_clusters_pca.csv"), low_memory=False)
    inbreed_df = pd.read_csv(os.path.join(ANALYSIS_DIR, "top_inbreeding_ancestors.csv"), low_memory=False)

    # Normalizar erro de tradução literal em race_entries ("Kumazawa Important Cultural Heritage" -> "Shigefumi Kumazawa")
    entries["jockey"] = entries["jockey"].apply(clean_en_entity)
    entries["trainer"] = entries["trainer"].apply(clean_en_entity)

    # Construir dicionário EN -> JA autêntico a partir do pareamento direto das tabelas JA e EN
    en_to_ja = {}

    # 1. Cavalos via horse_id
    id_to_ja = horses_ja.dropna(subset=["horse_id", "name"]).drop_duplicates("horse_id").set_index("horse_id")["name"].to_dict()
    for _, row in horses_en.dropna(subset=["horse_id", "name"]).iterrows():
        hid = row["horse_id"]
        en_n = clean_en_entity(row["name"])
        if hid in id_to_ja and en_n:
            ja_n = clean_ja_entity(id_to_ja[hid])
            if ja_n and not re.match(r"^[A-Za-z0-9\s\.\-\(\)']+$", ja_n):
                en_to_ja[en_n] = ja_n

    # 2. Pedigree (sire_name, dam_name, dam_sire_name) pareado por horse_id
    ped_ja_map = pedigree_ja.dropna(subset=["horse_id"]).drop_duplicates("horse_id").set_index("horse_id").to_dict(orient="index")
    for _, row in pedigree_en.dropna(subset=["horse_id"]).iterrows():
        hid = row["horse_id"]
        if hid in ped_ja_map:
            pja = ped_ja_map[hid]
            for col in ["horse_name", "sire_name", "dam_name", "dam_sire_name"]:
                en_v = clean_en_entity(row.get(col, ""))
                ja_v = clean_ja_entity(pja.get(col, ""))
                if en_v and ja_v and not re.match(r"^[A-Za-z0-9\s\.\-\(\)']+$", ja_v):
                    en_to_ja[en_v] = ja_v
                    en_to_ja[re.sub(r"\([A-Z]{2,4}\)$", "", en_v).strip()] = ja_v

    # 3. Jóqueis e Treinadores pareados por índice de linha em race_entries (mesma ordem de extração)
    if len(entries) == len(entries_ja):
        for en_j, ja_j in zip(entries["jockey"], entries_ja["jockey"]):
            if pd.notna(en_j) and pd.notna(ja_j):
                c_en = clean_en_entity(en_j)
                c_ja = clean_ja_entity(ja_j)
                if c_en and c_ja:
                    en_to_ja[c_en] = c_ja

    # 4. Sobrescrever com o mapa canônico verificado (garante 100% nos 30 patriarcas, sires estrangeiros e jóqueis)
    for k_en, v_ja in CANONICAL_JA_MAP.items():
        en_to_ja[k_en] = v_ja

    def get_ja_name(en_name):
        if not en_name or pd.isna(en_name):
            return ""
        clean = clean_en_entity(en_name)
        no_country = re.sub(r"\([A-Z]{2,4}\)$", "", clean).strip()
        if no_country in CANONICAL_JA_MAP:
            return CANONICAL_JA_MAP[no_country]
        if clean in en_to_ja:
            return en_to_ja[clean]
        if no_country in en_to_ja:
            return en_to_ja[no_country]
        return ""

    # Juntar entries + races para estatísticas detalhadas por cavalo e jóquei
    df = entries.merge(
        races[["race_id", "year", "grade", "grade_weight", "surface", "distance", "track", "race_name"]],
        on="race_id",
        how="left",
    )
    df["pos_num"] = pd.to_numeric(df["position"], errors="coerce")
    df["age_num"] = pd.to_numeric(df["age"], errors="coerce")
    df["year_num"] = pd.to_numeric(df["year"], errors="coerce")
    df["dist_num"] = pd.to_numeric(df["distance"], errors="coerce")
    df["mass_kg"] = df["horse_weight"].astype(str).str.extract(r"^(\d{3})")[0].astype(float)

    # Estimar ano de nascimento exato via (year - age) diretamente das corridas (imune a homônimos antigos!)
    df["est_birth"] = df["year_num"] - df["age_num"]
    birth_est_map = df.dropna(subset=["est_birth"]).groupby("horse_name")["est_birth"].median().round().astype(int).to_dict()

    # Superfície preferida, distância média, peso médio, jóquei principal, treinador principal e melhor corrida
    horse_extra = {}
    for hname, grp in df.groupby("horse_name"):
        surf_mode = grp["surface"].mode()
        pref_surf = str(surf_mode.iloc[0]) if not surf_mode.empty else "Turf"
        avg_dist = int(round(grp["dist_num"].mean())) if grp["dist_num"].notna().any() else 2000
        avg_mass = int(round(grp["mass_kg"].mean())) if grp["mass_kg"].notna().any() else 480
        j_mode = grp["jockey"].dropna().mode()
        top_jockey = clean_en_entity(j_mode.iloc[0]) if not j_mode.empty else "JRA Jockey"
        t_mode = grp["trainer"].dropna().mode()
        top_trainer = clean_en_entity(t_mode.iloc[0]) if not t_mode.empty else "JRA Trainer"

        best_rows = grp.sort_values(by=["pos_num", "grade_weight"], ascending=[True, False])
        if not best_rows.empty:
            br = best_rows.iloc[0]
            rname = str(br["race_name"]) if pd.notna(br["race_name"]) and str(br["race_name"]).strip() else str(br["race_id"])
            sig_race = f"{int(br['year_num'])} {rname} ({br['grade']}) — #{int(br['pos_num']) if pd.notna(br['pos_num']) else '?'}"
        else:
            sig_race = "JRA Graded Entry"

        horse_extra[hname] = {
            "pref_surface": pref_surf,
            "avg_dist": avg_dist,
            "avg_mass": avg_mass,
            "top_jockey": top_jockey,
            "top_trainer": top_trainer,
            "sig_race": sig_race,
        }

    h_meta = horses_en.drop_duplicates(subset=["name"]).set_index("name").to_dict(orient="index")

    pr_df_sorted = pr_df.sort_values(by="pagerank_rank", ascending=True).copy()
    top_pr_names = set(pr_df_sorted.head(260)["horse_name"].tolist())
    top_earn_names = set(pr_df_sorted.sort_values(by="total_earnings_m_yen", ascending=False).head(100)["horse_name"].tolist())
    underdog_names = set(pr_df_sorted[(pr_df_sorted["graded_wins"] == 0) & (pr_df_sorted["graded_podiums"] >= 1) & (pr_df_sorted["pagerank_rank"] <= 500)].head(45)["horse_name"].tolist())
    silver_names = set(pr_df_sorted[(pr_df_sorted["graded_wins"] > 0) & (pr_df_sorted["g1_wins"] == 0) & (pr_df_sorted["pagerank_rank"] <= 150)].head(45)["horse_name"].tolist())

    selected_names = top_pr_names | top_earn_names | underdog_names | silver_names
    sub_horses = pr_df_sorted[pr_df_sorted["horse_name"].isin(selected_names)].drop_duplicates(subset=["horse_name"]).copy()

    max_pr = float(pr_df_sorted["pagerank_scaled"].max())
    max_earn = float(pr_df_sorted["total_earnings_m_yen"].max())

    horse_cards = []
    for _, r in sub_horses.iterrows():
        hname = str(r["horse_name"])
        pr_rank = int(r["pagerank_rank"])
        pr_val = round(float(r["pagerank_scaled"]), 2)
        starts = max(1, int(r["graded_starts"]))
        wins = int(r["graded_wins"])
        g1_wins = int(r["g1_wins"])
        g1_podiums = int(r["g1_podiums"])
        podiums = int(r["graded_podiums"])
        earn_m = round(float(r["total_earnings_m_yen"]), 1)

        earn_est = False
        if earn_m <= 0.1 and (wins > 0 or podiums > 0):
            earn_m = round(g1_wins * 135.0 + (wins - g1_wins) * 52.0 + max(0, podiums - wins) * 24.0, 1)
            earn_est = True

        # Correção de BUG-08: Sempre priorizar birth_est_map (year - age) ou validar compatibilidade biológica (2 <= peak - birth <= 8)
        peak_yr = int(r["peak_year"])
        raw_byear = int(r["birth_year"]) if pd.notna(r["birth_year"]) else 0
        if hname in birth_est_map and (raw_byear < 1985 or not (2 <= (peak_yr - raw_byear) <= 8)):
            byear = birth_est_map[hname]
        elif 2 <= (peak_yr - raw_byear) <= 8:
            byear = raw_byear
        else:
            byear = birth_est_map.get(hname, peak_yr - 4)

        hm = h_meta.get(hname, {})
        color = str(hm.get("color", "")) if pd.notna(hm.get("color")) and str(hm.get("color")).strip() else "Bay"
        breeder = str(hm.get("breeder", "")) if pd.notna(hm.get("breeder")) and str(hm.get("breeder")).strip() else "JRA / JBIS Stud"
        owner = str(hm.get("owner", "")) if pd.notna(hm.get("owner")) and str(hm.get("owner")).strip() else "JRA Registered Owner"

        ex = horse_extra.get(hname, {"pref_surface": "Turf", "avg_dist": 2000, "avg_mass": 480, "top_jockey": "JRA Jockey", "top_trainer": "JRA Trainer", "sig_race": "JRA Graded"})

        stat_pr = int(round(np.clip((pr_val / max_pr) * 100.0, 25, 100)))
        win_rate = round((wins / starts) * 100.0, 1)
        podium_rate = round((podiums / starts) * 100.0, 1)
        stat_win = int(round(np.clip(win_rate * 1.15 + g1_wins * 7.5, 0 if wins == 0 else 20, 100)))
        stat_con = int(round(np.clip(podium_rate * 1.05 + g1_podiums * 2.5, 20, 100)))
        stat_earn = int(round(np.clip(np.sqrt(earn_m / max_earn) * 100.0, 18, 100)))
        stat_sta = int(round(np.clip((ex["avg_dist"] - 1100.0) / (2600.0 - 1100.0) * 100.0, 18, 100)))
        stat_riv = int(round(np.clip((float(r["weighted_degree"]) / 280.0) * 100.0, 25, 100)))

        # Correção de BUG-11: Raridade DIAMOND restrita a cavalos com 0 vitórias Graded MAS >= 1 pódio Graded e PageRank Top 500
        if wins == 0 and podiums >= 1 and pr_rank <= 500:
            rarity = "DIAMOND"
            ovr = int(round(np.clip(82 + (200 - min(200, pr_rank)) * 0.06, 80, 93)))
        elif wins > 0 and g1_wins == 0 and pr_rank <= 110:
            rarity = "SILVER"
            ovr = int(round(np.clip(83 + (110 - min(110, pr_rank)) * 0.08, 81, 92)))
        elif pr_rank <= 18 or g1_wins >= 4 or earn_m >= 1200:
            rarity = "SSR"
            ovr = int(round(np.clip(93 + (g1_wins * 0.7) + (stat_pr * 0.04), 93, 99)))
        elif g1_wins >= 1 or pr_rank <= 85 or earn_m >= 500:
            rarity = "UR"
            ovr = int(round(np.clip(86 + (g1_wins * 1.5) + (stat_pr * 0.05), 86, 93)))
        else:
            rarity = "SR"
            ovr = int(round(np.clip(78 + (wins * 1.2) + (stat_pr * 0.05), 76, 86)))

        if ex["pref_surface"] == "Dirt":
            elem = "Dirt Titan"
        elif ex["avg_dist"] <= 1450:
            elem = "Turf Sprinter"
        elif ex["avg_dist"] <= 1750:
            elem = "Turf Miler"
        elif ex["avg_dist"] >= 2250:
            elem = "Classic Stayer"
        else:
            elem = "Turf Classic"

        horse_cards.append({
            "id": f"H_{pr_rank}",
            "type": "horse",
            "name": hname,
            "ja": get_ja_name(hname),
            "rank": pr_rank,
            "pr": pr_val,
            "ovr": ovr,
            "rarity": rarity,
            "elem": elem,
            "sex": str(r["sex"]),
            "birth": byear,
            "peak": peak_yr,
            "color": color,
            "surf": ex["pref_surface"],
            "dist": ex["avg_dist"],
            "mass": ex["avg_mass"],
            "starts": starts,
            "wins": wins,
            "g1": g1_wins,
            "podiums": podiums,
            "win_rt": win_rate,
            "pod_rt": podium_rate,
            "earn": earn_m,
            "earn_est": earn_est,
            "sire": re.sub(r"\([A-Z]{2,4}\)$", "", str(r["sire"])).strip(),
            "dam": re.sub(r"\([A-Z]{2,4}\)$", "", str(r["dam"])).strip(),
            "damsire": re.sub(r"\([A-Z]{2,4}\)$", "", str(r["dam_sire"])).strip(),
            "jockey": ex["top_jockey"],
            "trainer": ex["top_trainer"],
            "breeder": breeder,
            "owner": owner,
            "fx": round(float(r["inbreeding_fx_pct"]), 2),
            "crosses": str(r["inbreeding_crosses"]) if pd.notna(r["inbreeding_crosses"]) else "Outcross (0.0%)",
            "sig_race": ex["sig_race"],
            "stats": [stat_pr, stat_win, stat_con, stat_earn, stat_sta, stat_riv],
        })

    # 2. SIRE CARDS
    top_progeny_map = {}
    for sname, grp in pr_df_sorted.groupby("sire"):
        clean_s = re.sub(r"\([A-Z]{2,4}\)$", "", str(sname)).strip()
        top_kids = grp.head(5)["horse_name"].tolist()
        top_progeny_map[str(sname)] = top_kids
        top_progeny_map[clean_s] = top_kids

    sire_cards = []
    clusters_sorted = clusters_df.sort_values(by=["unique_progeny", "g1_wins"], ascending=[False, False]).reset_index(drop=True)
    max_prog = float(clusters_sorted["unique_progeny"].max())
    max_s_g1 = max(1.0, float(clusters_sorted["g1_wins"].max()))

    for idx, r in clusters_sorted.iterrows():
        sname = str(r["sire"])
        clean_sname = re.sub(r"\([A-Z]{2,4}\)$", "", sname).strip()
        prog_cnt = int(r["unique_progeny"])
        tot_entries = int(r["total_entries"])
        gwins = int(r["graded_wins"])
        g1wins = int(r["g1_wins"])
        pods = int(r["podiums"])
        w_rt = round(float(r["win_rate_pct"]), 1)
        p_rt = round(float(r["podium_rate_pct"]), 1)
        t_sh = round(float(r["turf_share_pct"]), 1)
        avg_d = int(round(float(r["avg_distance_m"])))
        m_pr = round(float(r["mean_progeny_pagerank"]), 2)
        arch = str(r["cluster_archetype"])

        if g1wins >= 20 or prog_cnt >= 200:
            rarity = "SSR"
            ovr = int(round(np.clip(93 + (g1wins / 10.0), 93, 99)))
        elif g1wins >= 5 or prog_cnt >= 80:
            rarity = "UR"
            ovr = int(round(np.clip(85 + (g1wins * 0.45), 85, 92)))
        else:
            rarity = "SR"
            ovr = int(round(np.clip(77 + (prog_cnt * 0.1), 77, 85)))

        s_stat1 = int(round(np.clip((prog_cnt / max_prog) * 100.0, 20, 100)))
        s_stat2 = int(round(np.clip((g1wins / max_s_g1) * 100.0, 10, 100)))
        s_stat3 = int(round(np.clip(w_rt * 6.0, 20, 100)))
        s_stat4 = int(round(np.clip(p_rt * 3.0, 25, 100)))
        s_stat5 = int(round(np.clip(t_sh, 10, 100)))
        s_stat6 = int(round(np.clip((m_pr / 3.0) * 100.0, 25, 100)))

        sire_cards.append({
            "id": f"S_{idx+1}",
            "type": "sire",
            "name": clean_sname,
            "ja": get_ja_name(sname) or get_ja_name(clean_sname),
            "rank": idx + 1,
            "ovr": ovr,
            "rarity": rarity,
            "archetype": arch,
            "progeny": prog_cnt,
            "entries": tot_entries,
            "wins": gwins,
            "g1": g1wins,
            "podiums": pods,
            "win_rt": w_rt,
            "pod_rt": p_rt,
            "turf_pct": t_sh,
            "dist": avg_d,
            "mean_pr": m_pr,
            "pca1": round(float(r["pca_1"]), 2),
            "pca2": round(float(r["pca_2"]), 2),
            "top_kids": top_progeny_map.get(sname, top_progeny_map.get(clean_sname, [])),
            "stats": [s_stat1, s_stat2, s_stat3, s_stat4, s_stat5, s_stat6],
        })

    # 3. JOCKEY CARDS
    df["is_win"] = (df["pos_num"] == 1).astype(int)
    df["is_g1_win"] = ((df["pos_num"] == 1) & (df["grade"] == "G1")).astype(int)
    df["is_top3"] = (df["pos_num"] <= 3).astype(int)

    j_cards = []
    j_grp = (
        df.dropna(subset=["jockey"])
        .groupby("jockey")
        .agg(
            starts=("race_id", "count"),
            wins=("is_win", "sum"),
            g1_wins=("is_g1_win", "sum"),
            podiums=("is_top3", "sum"),
        )
        .reset_index()
    )
    j_grp = j_grp[j_grp["starts"] >= 20].sort_values(by=["wins", "g1_wins"], ascending=[False, False]).head(60).reset_index(drop=True)
    max_jwins = max(1.0, float(j_grp["wins"].max()))
    max_jg1 = max(1.0, float(j_grp["g1_wins"].max()))

    for idx, r in j_grp.iterrows():
        jname = clean_en_entity(r["jockey"])
        j_sub = df[df["jockey"] == jname]
        partner_horses = j_sub[j_sub["is_win"] == 1]["horse_name"].value_counts().head(4).index.tolist()
        if len(partner_horses) < 3:
            partner_horses = j_sub["horse_name"].value_counts().head(4).index.tolist()

        j_starts = int(r["starts"])
        j_wins = int(r["wins"])
        j_g1 = int(r["g1_wins"])
        j_pods = int(r["podiums"])
        j_wrt = round((j_wins / j_starts) * 100.0, 1)
        j_prt = round((j_pods / j_starts) * 100.0, 1)

        if j_g1 >= 18 or j_wins >= 90:
            rarity = "SSR"
            ovr = int(round(np.clip(92 + (j_g1 / 12.0), 92, 99)))
        elif j_g1 >= 5 or j_wins >= 35:
            rarity = "UR"
            ovr = int(round(np.clip(84 + (j_g1 * 0.4), 84, 91)))
        else:
            rarity = "SR"
            ovr = int(round(np.clip(76 + (j_wins * 0.25), 76, 83)))

        j_st1 = int(round(np.clip((j_wins / max_jwins) * 100.0, 20, 100)))
        j_st2 = int(round(np.clip((j_g1 / max_jg1) * 100.0, 10, 100)))
        j_st3 = int(round(np.clip(j_wrt * 4.5, 20, 100)))
        j_st4 = int(round(np.clip(j_prt * 2.1, 25, 100)))
        j_st5 = int(round(np.clip((j_starts / 1200.0) * 100.0, 20, 100)))
        j_st6 = int(round(np.clip((len(j_sub["horse_name"].unique()) / 350.0) * 100.0, 25, 100)))

        j_cards.append({
            "id": f"J_{idx+1}",
            "type": "jockey",
            "name": jname,
            "ja": get_ja_name(jname),
            "rank": idx + 1,
            "ovr": ovr,
            "rarity": rarity,
            "starts": j_starts,
            "wins": j_wins,
            "g1": j_g1,
            "podiums": j_pods,
            "win_rt": j_wrt,
            "pod_rt": j_prt,
            "partners": partner_horses,
            "stats": [j_st1, j_st2, j_st3, j_st4, j_st5, j_st6],
        })

    # 4. ANCESTOR INBREEDING CARDS
    ancestor_cards = []
    for idx, r in inbreed_df.head(30).iterrows():
        aname = str(r["common_ancestor"])
        clean_a = re.sub(r"\([A-Z]{2,4}\)$", "", aname).strip()
        inb_cnt = int(r["inbred_horses_count"])
        gw = int(r["graded_wins_by_inbred_progeny"])
        rarity = "SSR" if idx < 5 else ("UR" if idx < 14 else "SR")
        ovr = int(round(np.clip(99 - idx * 0.7, 79, 99)))
        ancestor_cards.append({
            "id": f"A_{idx+1}",
            "type": "ancestor",
            "name": clean_a,
            "ja": get_ja_name(clean_a) or get_ja_name(aname),
            "rank": idx + 1,
            "ovr": ovr,
            "rarity": rarity,
            "inbred_horses": inb_cnt,
            "graded_wins": gw,
            "stats": [
                int(round(np.clip((inb_cnt / 4206.0) * 100.0, 20, 100))),
                int(round(np.clip((gw / 1211.0) * 100.0, 20, 100))),
                int(round(np.clip(98 - idx * 2.2, 35, 99))),
                int(round(np.clip((gw / max(1, inb_cnt)) * 280.0, 30, 100))),
                95 if idx < 8 else 80,
                int(round(np.clip(100 - idx * 2.5, 30, 100))),
            ],
        })

    return horse_cards, sire_cards, j_cards, ancestor_cards


def generate_html(horse_cards, sire_cards, j_cards, ancestor_cards):
    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0">
  <title>JRA & JBIS TCG Arena — Gamified PageRank & Pedigree Card Explorer</title>
  <script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>
  <style>
    :root {{
      --bg-deep: #070a12;
      --bg-panel: #0f1626;
      --bg-card: #151e32;
      --border-subtle: #23304d;
      --gold-ssr: #fbbf24;
      --cyan-diamond: #22d3ee;
      --silver-crown: #e2e8f0;
      --purple-ur: #c084fc;
      --blue-sr: #38bdf8;
      --green-turf: #10b981;
      --amber-dirt: #f59e0b;
      --text-primary: #f8fafc;
      --text-secondary: #94a3b8;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      padding: 0;
      background: radial-gradient(circle at 50% 0%, #17203a 0%, #070a12 70%);
      color: var(--text-primary);
      font-family: 'Inter', 'Segoe UI', 'Hiragino Kaku Gothic ProN', 'Noto Sans JP', 'Yu Gothic', 'Meiryo', 'MS PGothic', system-ui, -apple-system, sans-serif;
      min-height: 100vh;
      overflow-x: hidden;
    }}

    /* TOP NAVBAR */
    .navbar {{
      position: sticky;
      top: 0;
      z-index: 100;
      background: rgba(11, 16, 29, 0.94);
      backdrop-filter: blur(14px);
      border-bottom: 1px solid #263354;
      padding: 14px 24px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 12px;
    }}
    .brand-box {{
      display: flex;
      align-items: center;
      gap: 12px;
    }}
    .brand-logo {{
      width: 42px;
      height: 42px;
      border-radius: 12px;
      background: linear-gradient(135deg, #f59e0b, #8b5cf6, #06b6d4);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 22px;
      box-shadow: 0 0 18px rgba(139, 92, 246, 0.5);
      flex-shrink: 0;
    }}
    .brand-text h1 {{
      margin: 0;
      font-size: 19px;
      font-weight: 900;
      letter-spacing: 0.3px;
      background: linear-gradient(90deg, #fbbf24, #38bdf8, #c084fc);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }}
    .brand-text p {{
      margin: 2px 0 0 0;
      font-size: 11.8px;
      color: var(--text-secondary);
    }}
    .nav-actions {{
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
    }}
    .lang-btn {{
      background: #17223b;
      color: #cbd5e1;
      border: 1px solid #2e4068;
      border-radius: 999px;
      padding: 6px 13px;
      font-size: 12px;
      font-weight: 700;
      cursor: pointer;
      transition: all 0.18s ease;
    }}
    .lang-btn:hover {{
      background: #233357;
      color: #fff;
    }}
    .lang-btn.active {{
      background: linear-gradient(90deg, #38bdf8, #818cf8);
      color: #090d16;
      border-color: transparent;
      box-shadow: 0 0 12px rgba(56, 189, 248, 0.45);
    }}
    .superset-link {{
      background: rgba(168, 85, 247, 0.16);
      border: 1px solid rgba(168, 85, 247, 0.5);
      color: #e9d5ff;
      text-decoration: none;
      padding: 6px 14px;
      border-radius: 999px;
      font-size: 12px;
      font-weight: 700;
      transition: all 0.2s;
    }}
    .superset-link:hover {{
      background: rgba(168, 85, 247, 0.32);
    }}

    /* HERO EXPLAINER BANNER FOR LAYPEOPLE */
    .hero-banner {{
      max-width: 1640px;
      margin: 18px auto 10px auto;
      padding: 0 20px;
    }}
    .hero-inner {{
      background: linear-gradient(135deg, rgba(30, 27, 75, 0.78) 0%, rgba(15, 23, 42, 0.92) 100%);
      border: 1px solid #31416b;
      border-radius: 16px;
      padding: 16px 22px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 16px;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.35);
    }}
    .hero-copy {{
      max-width: 920px;
    }}
    .hero-copy h2 {{
      margin: 0 0 6px 0;
      font-size: 16.5px;
      color: #38bdf8;
    }}
    .hero-copy p {{
      margin: 0;
      font-size: 13px;
      line-height: 1.5;
      color: #cbd5e1;
    }}
    .rarity-legend {{
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }}
    .r-pill {{
      padding: 5px 11px;
      border-radius: 8px;
      font-size: 11px;
      font-weight: 800;
      letter-spacing: 0.4px;
      display: flex;
      align-items: center;
      gap: 5px;
    }}
    .r-pill.ssr {{ background: rgba(251, 191, 36, 0.16); border: 1px solid #fbbf24; color: #fde68a; }}
    .r-pill.dia {{ background: rgba(34, 211, 238, 0.16); border: 1px solid #22d3ee; color: #a5f3fc; }}
    .r-pill.sil {{ background: rgba(226, 232, 240, 0.16); border: 1px solid #cbd5e1; color: #f1f5f9; }}
    .r-pill.ur  {{ background: rgba(192, 132, 252, 0.16); border: 1px solid #c084fc; color: #e9d5ff; }}
    .r-pill.sr  {{ background: rgba(56, 189, 248, 0.16); border: 1px solid #38bdf8; color: #bae6fd; }}

    /* DECK TABS & CONTROLS */
    .controls-wrap {{
      max-width: 1640px;
      margin: 0 auto;
      padding: 8px 20px 16px 20px;
    }}
    .deck-tabs {{
      display: flex;
      gap: 10px;
      overflow-x: auto;
      padding-bottom: 8px;
      scrollbar-width: thin;
      -webkit-overflow-scrolling: touch;
    }}
    .deck-tab {{
      background: #121b2e;
      border: 1px solid #263659;
      color: #94a3b8;
      padding: 11px 18px;
      border-radius: 12px;
      font-size: 13px;
      font-weight: 700;
      cursor: pointer;
      white-space: nowrap;
      transition: all 0.2s ease;
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .deck-tab:hover {{
      background: #1b2845;
      color: #f8fafc;
    }}
    .deck-tab.active {{
      background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
      color: #ffffff;
      border-color: #60a5fa;
      box-shadow: 0 4px 18px rgba(124, 58, 237, 0.45);
    }}
    .deck-count {{
      background: rgba(0, 0, 0, 0.35);
      padding: 2px 8px;
      border-radius: 999px;
      font-size: 11px;
    }}

    .filter-bar {{
      margin-top: 10px;
      background: #0f1626;
      border: 1px solid #22304f;
      border-radius: 12px;
      padding: 12px 16px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 12px;
    }}
    .search-box {{
      flex: 1;
      min-width: 220px;
      position: relative;
    }}
    .search-box input {{
      width: 100%;
      background: #17223b;
      border: 1px solid #2e4068;
      color: #fff;
      padding: 9px 14px 9px 36px;
      border-radius: 9px;
      font-size: 13px;
      outline: none;
    }}
    .search-box input:focus {{
      border-color: #38bdf8;
      box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.25);
    }}
    .search-icon {{
      position: absolute;
      left: 11px;
      top: 50%;
      transform: translateY(-50%);
      color: #64748b;
      font-size: 14px;
    }}
    .filter-group {{
      display: flex;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
    }}
    .filter-select {{
      background: #17223b;
      border: 1px solid #2e4068;
      color: #f8fafc;
      padding: 8px 12px;
      border-radius: 9px;
      font-size: 12.5px;
      font-weight: 600;
      cursor: pointer;
      max-width: 100%;
    }}
    .reset-btn {{
      background: #1e293b;
      border: 1px solid #475569;
      color: #cbd5e1;
      padding: 8px 13px;
      border-radius: 9px;
      font-size: 12px;
      font-weight: 700;
      cursor: pointer;
      transition: all 0.15s;
    }}
    .reset-btn:hover {{
      background: #334155;
      color: #fff;
    }}
    .result-counter {{
      font-size: 12px;
      font-weight: 700;
      color: #38bdf8;
      background: rgba(56, 189, 248, 0.1);
      border: 1px solid rgba(56, 189, 248, 0.3);
      padding: 6px 11px;
      border-radius: 8px;
      white-space: nowrap;
    }}
    .vs-banner-bar {{
      background: rgba(245, 158, 11, 0.14);
      border: 1px solid #f59e0b;
      color: #fde68a;
      padding: 7px 14px;
      border-radius: 9px;
      font-size: 12.5px;
      font-weight: 700;
      display: none;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
    }}
    .vs-banner-bar.active {{
      display: flex;
    }}
    .vs-cancel-btn {{
      background: #ef4444;
      color: #fff;
      border: none;
      border-radius: 6px;
      padding: 4px 10px;
      font-size: 11px;
      font-weight: 700;
      cursor: pointer;
    }}

    /* TCG CARD GRID */
    .cards-container {{
      max-width: 1640px;
      margin: 0 auto;
      padding: 4px 20px 48px 20px;
    }}
    .cards-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(282px, 1fr));
      gap: 20px;
    }}

    /* INDIVIDUAL TCG CARD */
    .tcg-card {{
      background: linear-gradient(165deg, #19243d 0%, #0e1525 100%);
      border-radius: 16px;
      padding: 15px;
      position: relative;
      cursor: pointer;
      transition: transform 0.22s cubic-bezier(0.2, 0.8, 0.2, 1), box-shadow 0.22s ease;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      overflow: hidden;
      border: 2px solid #2a3b61;
    }}
    .tcg-card:hover {{
      transform: translateY(-6px) scale(1.015);
    }}
    .tcg-card.rarity-SSR {{
      border-color: #fbbf24;
      background: linear-gradient(165deg, #2b2312 0%, #111827 55%, #1f1735 100%);
      box-shadow: 0 8px 26px rgba(251, 191, 36, 0.22);
    }}
    .tcg-card.rarity-SSR:hover {{
      box-shadow: 0 14px 34px rgba(251, 191, 36, 0.42);
    }}
    .tcg-card.rarity-DIAMOND {{
      border-color: #22d3ee;
      background: linear-gradient(165deg, #0b2938 0%, #0f172a 60%, #162a3a 100%);
      box-shadow: 0 8px 26px rgba(34, 211, 238, 0.24);
    }}
    .tcg-card.rarity-SILVER {{
      border-color: #cbd5e1;
      background: linear-gradient(165deg, #242c3d 0%, #0f172a 70%);
      box-shadow: 0 8px 22px rgba(226, 232, 240, 0.16);
    }}
    .tcg-card.rarity-UR {{
      border-color: #c084fc;
      background: linear-gradient(165deg, #241438 0%, #0f172a 65%);
      box-shadow: 0 8px 24px rgba(192, 132, 252, 0.2);
    }}
    .tcg-card.rarity-SR {{
      border-color: #38bdf8;
    }}

    /* Card Top Bar */
    .card-top {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 10px;
    }}
    .rank-badge {{
      background: #090d16;
      border: 1px solid #3b4f7d;
      padding: 4px 10px;
      border-radius: 8px;
      font-size: 13px;
      font-weight: 900;
      color: #f8fafc;
    }}
    .rank-badge.top1 {{ background: linear-gradient(90deg, #f59e0b, #fbbf24); color: #090d16; border-color: #fde68a; }}
    .rank-badge.top2 {{ background: linear-gradient(90deg, #94a3b8, #e2e8f0); color: #090d16; border-color: #fff; }}
    .rank-badge.top3 {{ background: linear-gradient(90deg, #b45309, #fb923c); color: #090d16; border-color: #fed7aa; }}

    .ovr-group {{
      display: flex;
      align-items: center;
      gap: 6px;
    }}
    .rarity-tag {{
      font-size: 10.5px;
      font-weight: 900;
      padding: 3px 8px;
      border-radius: 6px;
      letter-spacing: 0.5px;
    }}
    .rarity-tag.SSR {{ background: #fbbf24; color: #090d16; }}
    .rarity-tag.DIAMOND {{ background: #22d3ee; color: #090d16; }}
    .rarity-tag.SILVER {{ background: #e2e8f0; color: #090d16; }}
    .rarity-tag.UR {{ background: #c084fc; color: #090d16; }}
    .rarity-tag.SR {{ background: #38bdf8; color: #090d16; }}

    .ovr-circle {{
      background: rgba(15, 23, 42, 0.9);
      border: 1.5px solid rgba(255, 255, 255, 0.35);
      border-radius: 8px;
      padding: 2px 7px;
      font-size: 12.5px;
      font-weight: 900;
      color: #fff;
    }}

    /* Card Portrait / Crest Area */
    .card-Crest {{
      background: rgba(9, 13, 22, 0.55);
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 12px;
      padding: 12px;
      margin-bottom: 10px;
      display: flex;
      align-items: center;
      gap: 12px;
    }}
    .crest-avatar {{
      width: 52px;
      height: 52px;
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 27px;
      flex-shrink: 0;
      position: relative;
      box-shadow: inset 0 0 12px rgba(255,255,255,0.2);
    }}
    .crest-info {{
      overflow: hidden;
    }}
    .crest-name {{
      margin: 0;
      font-size: 15.5px;
      font-weight: 800;
      color: #ffffff;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }}
    .crest-ja {{
      font-size: 11.5px;
      color: #94a3b8;
      margin-top: 1px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }}
    .crest-meta {{
      margin-top: 5px;
      display: flex;
      gap: 6px;
      flex-wrap: wrap;
    }}
    .meta-chip {{
      background: rgba(30, 41, 59, 0.9);
      border: 1px solid #334155;
      padding: 2px 7px;
      border-radius: 5px;
      font-size: 10.5px;
      color: #cbd5e1;
      font-weight: 600;
    }}
    .meta-chip.turf {{ border-color: #10b981; color: #6ee7b7; }}
    .meta-chip.dirt {{ border-color: #f59e0b; color: #fcd34d; }}

    /* RPG Stat Bars inside Card */
    .stat-bars {{
      display: flex;
      flex-direction: column;
      gap: 6px;
      margin-bottom: 11px;
    }}
    .stat-row {{
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 11px;
    }}
    .stat-label {{
      width: 86px;
      color: #94a3b8;
      font-weight: 700;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }}
    .stat-track {{
      flex: 1;
      height: 7px;
      background: #090d16;
      border-radius: 999px;
      overflow: hidden;
    }}
    .stat-fill {{
      height: 100%;
      border-radius: 999px;
    }}
    .stat-num {{
      width: 32px;
      text-align: right;
      font-weight: 800;
      color: #e2e8f0;
    }}

    /* Card Footer */
    .card-foot {{
      border-top: 1px solid rgba(255, 255, 255, 0.08);
      padding-top: 9px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 11.2px;
      color: #94a3b8;
      gap: 6px;
    }}
    .card-foot b {{ color: #e2e8f0; }}
    .inspect-hint {{
      color: #38bdf8;
      font-weight: 700;
      font-size: 11px;
      white-space: nowrap;
    }}

    /* LOAD MORE BUTTON */
    .load-more-wrap {{
      text-align: center;
      margin-top: 26px;
    }}
    .load-more-btn {{
      background: linear-gradient(90deg, #0284c7, #6366f1);
      color: #fff;
      border: none;
      padding: 11px 28px;
      border-radius: 999px;
      font-size: 13.5px;
      font-weight: 800;
      cursor: pointer;
      box-shadow: 0 4px 16px rgba(99, 102, 241, 0.4);
    }}

    /* EXPANDED CARD MODAL (HOLOGRAPHIC 3D DOSSIER) */
    .modal-backdrop {{
      position: fixed;
      inset: 0;
      background: rgba(4, 7, 15, 0.85);
      backdrop-filter: blur(10px);
      z-index: 999;
      display: none;
      align-items: center;
      justify-content: center;
      padding: 16px;
      overflow-y: auto;
    }}
    .modal-backdrop.open {{
      display: flex;
    }}
    .modal-dialog {{
      background: linear-gradient(155deg, #131c31 0%, #090d16 100%);
      border: 2px solid #38bdf8;
      border-radius: 20px;
      max-width: 1120px;
      width: 100%;
      max-height: 92vh;
      overflow-y: auto;
      padding: 24px;
      position: relative;
      box-shadow: 0 25px 70px rgba(0, 0, 0, 0.75);
      animation: popIn 0.22s cubic-bezier(0.16, 1, 0.3, 1);
    }}
    @keyframes popIn {{
      from {{ transform: scale(0.92); opacity: 0; }}
      to {{ transform: scale(1); opacity: 1; }}
    }}
    .modal-close {{
      position: absolute;
      top: 16px;
      right: 18px;
      background: #1e293b;
      border: 1px solid #475569;
      color: #f8fafc;
      width: 36px;
      height: 36px;
      border-radius: 50%;
      font-size: 18px;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 10;
    }}
    .modal-close:hover {{ background: #ef4444; border-color: #ef4444; }}

    .modal-grid {{
      display: grid;
      grid-template-columns: 1.08fr 1fr;
      gap: 24px;
      margin-top: 8px;
    }}
    .duel-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 14px;
      padding-right: 40px;
      margin-bottom: 16px;
      flex-wrap: wrap;
    }}
    .layperson-note {{
      background: rgba(56, 189, 248, 0.08);
      border-left: 3px solid #38bdf8;
      border-radius: 8px;
      padding: 10px 12px;
      font-size: 12px;
      color: #cbd5e1;
      line-height: 1.45;
      margin-top: 10px;
    }}

    @media (max-width: 860px) {{
      .modal-grid {{ grid-template-columns: 1fr; }}
      .modal-dialog {{ padding: 16px; max-height: 94vh; }}
    }}
    @media (max-width: 640px) {{
      .navbar {{ padding: 12px 14px; }}
      .brand-text h1 {{ font-size: 16px; }}
      .hero-banner, .controls-wrap, .cards-container {{ padding-left: 12px; padding-right: 12px; }}
      .hero-inner {{ padding: 14px; }}
      .filter-bar {{ flex-direction: column; align-items: stretch; padding: 12px; }}
      .search-box {{ width: 100%; min-width: 100%; }}
      .filter-group {{ flex-direction: column; align-items: stretch; width: 100%; }}
      .filter-select, .reset-btn, .result-counter {{ width: 100%; text-align: center; }}
      .cards-grid {{ grid-template-columns: 1fr; gap: 14px; }}
      .duel-header {{ flex-direction: column; align-items: flex-start; padding-right: 32px; }}
      .ped-tree-mini {{ grid-template-columns: 1fr !important; }}
    }}

    .dossier-header {{
      display: flex;
      align-items: center;
      gap: 14px;
      margin-bottom: 16px;
      padding-right: 36px;
      flex-wrap: wrap;
    }}
    .dossier-title h2 {{
      margin: 0;
      font-size: 22px;
      font-weight: 900;
      color: #fff;
    }}
    .dossier-title p {{
      margin: 3px 0 0 0;
      font-size: 13px;
      color: #94a3b8;
    }}

    .dossier-kpis {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(125px, 1fr));
      gap: 10px;
      margin-bottom: 16px;
    }}
    .d-kpi {{
      background: rgba(15, 23, 42, 0.85);
      border: 1px solid #263659;
      border-radius: 10px;
      padding: 10px 12px;
    }}
    .d-kpi span {{
      display: block;
      font-size: 10.5px;
      color: #94a3b8;
      text-transform: uppercase;
      font-weight: 700;
    }}
    .d-kpi strong {{
      display: block;
      font-size: 15.5px;
      color: #f8fafc;
      margin-top: 3px;
    }}

    .pedigree-box {{
      background: rgba(9, 13, 22, 0.75);
      border: 1px solid #283a5e;
      border-radius: 12px;
      padding: 14px;
      margin-bottom: 14px;
    }}
    .pedigree-box h4 {{
      margin: 0 0 10px 0;
      font-size: 13px;
      color: #38bdf8;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }}
    .ped-tree-mini {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
    }}
    .ped-node {{
      background: #151f36;
      border: 1px solid #314675;
      border-radius: 8px;
      padding: 8px 11px;
      font-size: 12px;
    }}
    .ped-node.clickable {{
      cursor: pointer;
      border-color: #38bdf8;
    }}
    .ped-node.clickable:hover {{
      background: #1e2f52;
    }}
    .ped-node small {{
      display: block;
      color: #94a3b8;
      font-size: 10px;
      font-weight: 700;
    }}
    .ped-node b {{
      color: #f8fafc;
    }}

    .modal-radar-box {{
      background: rgba(9, 13, 22, 0.65);
      border: 1px solid #263659;
      border-radius: 14px;
      padding: 14px;
      display: flex;
      flex-direction: column;
      align-items: center;
    }}
    #modalRadarChart {{
      width: 100%;
      height: 330px;
    }}

    .duel-btn {{
      background: linear-gradient(90deg, #f59e0b, #ea580c);
      color: #090d16;
      border: none;
      padding: 10px 18px;
      border-radius: 10px;
      font-size: 13px;
      font-weight: 900;
      cursor: pointer;
      width: 100%;
      margin-top: 10px;
      transition: transform 0.15s;
    }}
    .duel-btn:hover {{
      transform: translateY(-2px);
    }}
  </style>
</head>
<body>

  <!-- STICKY NAVBAR -->
  <nav class="navbar">
    <div class="brand-box">
      <div class="brand-logo">🃏</div>
      <div class="brand-text">
        <h1 id="uiTitle">JRA & JBIS TCG Arena — Ranking Gamificado de Cards</h1>
        <p id="uiSubtitle">Explore PageRank, Linhagens de 5 Gerações, Ganhos e Jóqueis como um Jogo de Cartas Colecionáveis • Clique em qualquer Card para abrir o Dossiê 3D</p>
      </div>
    </div>
    <div class="nav-actions">
      <button class="lang-btn active" id="btnLangPt" onclick="setLanguage('pt')">🇧🇷 PT-BR</button>
      <button class="lang-btn" id="btnLangEn" onclick="setLanguage('en')">🇺🇸 EN</button>
      <button class="lang-btn" id="btnLangJa" onclick="setLanguage('ja')">🇯🇵 日本語</button>
      <a class="superset-link" id="linkSuperset" href="superset_interactive_dashboard.html" onclick="if(location.hostname==='htmlpreview.github.io'){{location.href='https://htmlpreview.github.io/?https://github.com/ImArthz/AEDS2_jra_analysis/blob/main/docs/'+this.getAttribute('href');return false;}}">📊 Dashboard Superset (13 Charts)</a>
    </div>
  </nav>

  <!-- LAYPERSON EXPLAINER BANNER -->
  <section class="hero-banner">
    <div class="hero-inner">
      <div class="hero-copy">
        <h2 id="heroHeading">💡 Como funciona este Jogo de Cards Científico?</h2>
        <p id="heroDesc">Cada cavalo, garanhão reprodutor, jóquei e patriarca fundador de 2002 a 2025 foi transformado em um Card com pontuação Overall (OVR 76–99) calculada por Teoria dos Grafos (PageRank). Cavalos com a raridade especial <b>DIAMOND (Diamante Injustiçado)</b> nunca venceram uma corrida Graded, mas enfrentaram e derrotaram campeões de G1 em pódios históricos!</p>
      </div>
      <div class="rarity-legend">
        <div class="r-pill ssr" id="pillSsr">🌟 SSR MYTHIC (Top PageRank / Lendas G1)</div>
        <div class="r-pill dia" id="pillDia">💎 DIAMOND (0 Vitórias, Altíssimo PageRank!)</div>
        <div class="r-pill sil" id="pillSil">🥈 SILVER CROWN (Reis sem Coroa G1)</div>
        <div class="r-pill ur" id="pillUr">🟣 UR EPIC (Campeões G1)</div>
        <div class="r-pill sr" id="pillSr">🔵 SR RARE (Vencedores Graded)</div>
      </div>
    </div>
  </section>

  <!-- DECK TABS & FILTERS -->
  <section class="controls-wrap">
    <div class="deck-tabs">
      <button class="deck-tab active" id="tab_pagerank" onclick="switchDeck('pagerank')">
        🏆 <span id="lblTabPr">1. Ranking PageRank Global</span> <span class="deck-count" id="cnt_pagerank">0</span>
      </button>
      <button class="deck-tab" id="tab_earnings" onclick="switchDeck('earnings')">
        💰 <span id="lblTabEarn">2. Maiores Premiações (¥ Bilhões)</span> <span class="deck-count" id="cnt_earnings">0</span>
      </button>
      <button class="deck-tab" id="tab_sires" onclick="switchDeck('sires')">
        🧬 <span id="lblTabSires">3. Garanhões Reprodutores (Mais Filhos)</span> <span class="deck-count" id="cnt_sires">0</span>
      </button>
      <button class="deck-tab" id="tab_anomalies" onclick="switchDeck('anomalies')">
        💎 <span id="lblTabAnom">4. Diamantes Injustiçados (0 Vitórias)</span> <span class="deck-count" id="cnt_anomalies">0</span>
      </button>
      <button class="deck-tab" id="tab_jockeys" onclick="switchDeck('jockeys')">
        🏇 <span id="lblTabJock">5. Mestres Jóqueis (Fator Humano)</span> <span class="deck-count" id="cnt_jockeys">0</span>
      </button>
      <button class="deck-tab" id="tab_ancestors" onclick="switchDeck('ancestors')">
        🌳 <span id="lblTabAnc">6. Patriarcas 5-Gerações (Inbreeding F_X)</span> <span class="deck-count" id="cnt_ancestors">0</span>
      </button>
    </div>

    <div class="filter-bar">
      <div class="search-box">
        <span class="search-icon">🔍</span>
        <input type="text" id="searchInput" oninput="applyFilters()" placeholder="Buscar cavalo, pai (ex: Deep Impact), jóquei (ex: Yutaka Take), ano ou nome em Japonês...">
      </div>
      <div class="vs-banner-bar" id="vsBanner">
        <span id="vsBannerText"></span>
        <button class="vs-cancel-btn" id="btnVsCancel" onclick="cancelDuelMode()">✕ Cancelar</button>
      </div>
      <div class="filter-group">
        <select class="filter-select" id="rarityFilter" onchange="applyFilters()">
          <option value="ALL" id="optRarityAll">Todas as Raridades (SSR / DIAMOND / UR / SR)</option>
          <option value="SSR" id="optRaritySsr">🌟 SSR Mythic Legend</option>
          <option value="DIAMOND" id="optRarityDia">💎 Diamond Anomaly (0 Vitórias)</option>
          <option value="SILVER" id="optRaritySil">🥈 Silver Crown (0 G1)</option>
          <option value="UR" id="optRarityUr">🟣 UR Epic</option>
          <option value="SR" id="optRaritySr">🔵 SR Rare</option>
        </select>
        <select class="filter-select" id="surfaceFilter" onchange="applyFilters()">
          <option value="ALL" id="optSurfAll">Todas as Pistas (Grama & Areia)</option>
          <option value="Turf" id="optSurfTurf">🌿 Grama (Turf)</option>
          <option value="Dirt" id="optSurfDirt">🔥 Areia (Dirt)</option>
        </select>
        <select class="filter-select" id="sortSelect" onchange="applyFilters()">
          <option value="DEFAULT" id="optSortDef">Ordenação Padrão do Deck</option>
          <option value="OVR_DESC" id="optSortOvr">Maior Pontuação Geral (OVR 99→75)</option>
          <option value="WINS_DESC" id="optSortWins">Mais Vitórias Graded / G1</option>
          <option value="EARN_DESC" id="optSortEarn">Maior Premiação / Mais Filhos</option>
          <option value="BIRTH_ASC" id="optSortBirth">Ano de Nascimento (Mais Antigos → Novos)</option>
        </select>
        <button class="reset-btn" id="btnResetFilters" onclick="resetAllFilters()">↺ Limpar Filtros</button>
        <span class="result-counter" id="resultCounter">0 Cards</span>
      </div>
    </div>
  </section>

  <!-- CARDS GRID -->
  <main class="cards-container">
    <div class="cards-grid" id="cardsGrid"></div>
    <div class="load-more-wrap" id="loadMoreWrap" style="display:none;">
      <button class="load-more-btn" id="btnLoadMore" onclick="loadMoreCards()">Carregar Mais Cards (+36)</button>
    </div>
  </main>

  <!-- EXPANDED CARD MODAL -->
  <div class="modal-backdrop" id="cardModal" onclick="if(event.target===this)closeModal()">
    <div class="modal-dialog" id="modalDialog">
      <button class="modal-close" onclick="closeModal()" aria-label="Close">✕</button>
      <div id="modalContent"></div>
    </div>
  </div>

  <script>
    const HORSES_DATA = {json.dumps(horse_cards, ensure_ascii=False)};
    const SIRES_DATA = {json.dumps(sire_cards, ensure_ascii=False)};
    const JOCKEYS_DATA = {json.dumps(j_cards, ensure_ascii=False)};
    const ANCESTORS_DATA = {json.dumps(ancestor_cards, ensure_ascii=False)};

    const I18N = {{
      pt: {{
        title: "JRA & JBIS TCG Arena — Ranking Gamificado de Cards",
        subtitle: "Explore PageRank, Linhagens de 5 Gerações, Ganhos e Jóqueis como um Jogo de Cartas • Clique em qualquer Card para abrir o Dossiê 3D",
        linkSuperset: "📊 Dashboard Superset (13 Gráficos)",
        supersetHref: "superset_interactive_dashboard.html",
        heroHeading: "💡 Como funciona este Jogo de Cards Científico?",
        heroDesc: "Cada cavalo, garanhão reprodutor, jóquei e patriarca fundador (2002–2025) foi transformado em um Card com pontuação Overall (OVR 76–99) calculada por Teoria dos Grafos (PageRank). Cards <b>DIAMOND (Diamante Injustiçado)</b> nunca venceram uma corrida Graded, mas derrotaram campeões de G1 em pódios históricos!",
        pillSsr: "🌟 SSR MYTHIC (Top PageRank / Lendas G1)",
        pillDia: "💎 DIAMOND (0 Vitórias, Altíssimo PageRank!)",
        pillSil: "🥈 SILVER CROWN (Reis sem Coroa G1)",
        pillUr: "🟣 UR EPIC (Campeões G1)",
        pillSr: "🔵 SR RARE (Vencedores Graded)",
        tabPr: "1. Ranking PageRank Global",
        tabEarn: "2. Maiores Premiações (¥)",
        tabSires: "3. Garanhões (Mais Filhos)",
        tabAnom: "4. Diamantes Injustiçados",
        tabJock: "5. Mestres Jóqueis",
        tabAnc: "6. Patriarcas 5-Gerações",
        searchPh: "Buscar cavalo, pai (ex: Deep Impact), jóquei (ex: Yutaka Take), ano ou nome em Japonês...",
        optRarityAll: "Todas as Raridades (SSR / DIAMOND / UR / SR)",
        optRaritySsr: "🌟 SSR Mythic Legend",
        optRarityDia: "💎 Diamond Anomaly (0 Vitórias)",
        optRaritySil: "🥈 Silver Crown (0 G1)",
        optRarityUr: "🟣 UR Epic",
        optRaritySr: "🔵 SR Rare",
        optSurfAll: "Todas as Pistas (Grama & Areia)",
        optSurfTurf: "🌿 Grama (Turf)",
        optSurfDirt: "🔥 Areia (Dirt)",
        optSortDef: "Ordenação Padrão do Deck",
        optSortOvr: "Maior Pontuação Geral (OVR 99→75)",
        optSortWins: "Mais Vitórias Graded / G1",
        optSortEarn: "Maior Premiação / Mais Filhos",
        optSortBirth: "Ano de Nascimento (Antigos → Novos)",
        btnReset: "↺ Limpar Filtros",
        btnVsCancel: "✕ Cancelar",
        emptyMsg: "Nenhum Card encontrado para este filtro. Clique em 'Limpar Filtros'!",
        counterFmt: (vis, tot) => `Exibindo ${{vis}} de ${{tot}} Cards`,
        btnLoadMore: "Carregar Mais Cards (+36)",
        inspectHint: "🔍 Clique p/ Expandir",
        bornLbl: "Nasc.",
        sireLbl: "Pai",
        startsLbl: "Largadas",
        winsLbl: "Vitórias",
        podiumsLbl: "Pódios",
        progenyLbl: "Filhos Graded",
        inbredLbl: "Cavalos c/ Inbreeding",
        estTag: " (Est.)",
        barPr: "⚔️ PageRank",
        barWinG1: "🏆 Vitória/G1",
        barTop3: "🛡️ Pódio %",
        barEarn: "💰 Premiação",
        barProg: "🧬 Prole",
        barG1Pow: "👑 Força G1",
        barKidsPr: "⚔️ PR Filhos",
        barWins: "🏆 Vitórias",
        barG1Tit: "👑 Títulos G1",
        barSyn: "🏇 Sinergia",
        barInb: "🌳 Inbreed",
        barProgW: "🏆 Vit. Prole",
        barImp: "🧬 Impacto",
        barPrest: "👑 Prestígio",
        chip5Gen: "Patriarca 5-Gen",
        footGradedWins: "Vitórias Graded",
        footStarts: "Largadas",
        footAce: "Parceiro",
        footInbWins: "Vitórias da Prole c/ Inbreeding",
        duelBtn: "⚔️ Comparar com outro Card (Modo Duelo VS)",
        duelPrompt: "⚔️ Modo Duelo ativo! Clique em outro card do mesmo tipo para duelar contra: ",
        duelSameWarn: "⚠️ Escolha um card diferente deste para iniciar o Duelo VS!",
        duelAttrHeader: "📊 Comparação Direta de Atributos (0–100)",
        mGlobalPr: "PageRank Global",
        mBirthPeak: "Nascimento (Pico)",
        mPeakWord: "Pico",
        mGradedRec: "Retrospecto Graded",
        mG1Titles: "Títulos de G1",
        mEarnings: "Premiação Total",
        mBioCoat: "Biometria & Pelagem",
        mSurfDist: "Pista & Distância",
        mWrightFx: "Endogamia Wright F_X",
        mPedHeader: "🧬 Árvore Genealógica Direta & Conexões (Clique no Pai/Avô para abrir o Card dele!)",
        mSireNode: "PAI (SIRE) 🔗",
        mDamNode: "MÃE (DAM)",
        mDamSireNode: "AVÔ MATERNO (DAM'S SIRE) 🔗",
        mTeamNode: "JÓQUEI & TREINADOR PRINCIPAL",
        mSigRace: "🏆 Corrida de Assinatura:",
        mCrosses: "🔬 Cruzamentos Consanguíneos (5-Gen LCA):",
        mBreederOwner: "🏡 Criador / Proprietário:",
        mLayHorse: "💡 <b>Guia Rápido:</b> O <b>PageRank</b> mede o prestígio real considerando a força dos adversários enfrentados. Já o <b>Coeficiente de Wright (F_X)</b> mede a porcentagem de sangue duplicado nas 5 gerações da árvore genealógica.",
        mSireRank: "Ranking Reprodutor",
        mSireProg: "Filhos em Graded",
        mSireStarts: "Largadas dos Filhos",
        mSireWinsG1: "Vitórias Graded / G1",
        mSirePodRt: "Taxa de Pódio",
        mSireTurf: "Afinidade Grama",
        mSireDist: "Distância Média",
        mSirePca: "Coordenadas PCA 2D",
        mSireArchTitle: "🧬 Arquétipo K-Means++ PCA:",
        mSireKidsDesc: "Principais filhos deste garanhão (clique em qualquer filho para abrir o Card dele):",
        mLaySire: "💡 <b>Guia Rápido:</b> Os 106 garanhões foram agrupados automaticamente pelo algoritmo <b>K-Means++ e PCA 2D</b> em 4 arquétipos genéticos (Areia, Velocidade, Clássicos G1 e Longa Distância).",
        mJockRank: "Ranking Jóquei",
        mJockWins: "Vitórias Graded",
        mJockG1: "Títulos de G1",
        mJockPod: "Pódios Top-3",
        mJockWinRt: "Taxa de Vitória",
        mJockStarts: "Total de Montarias",
        mJockPartTitle: "🤝 Rede Bipartida Jóquei ↔ Cavalo (Principais Parceiros Clicáveis)",
        mLayJock: "💡 <b>Guia Rápido:</b> Na nossa <b>Random Forest (ROC-AUC = 0.7260)</b>, a taxa histórica de pódios do jóquei foi a variável #1 mais importante (29.8% da Importância de Gini)!",
        mAncRank: "Patriarca Fundador",
        mAncInb: "Cavalos c/ Inbreeding",
        mAncWins: "Vitórias Graded (Prole)",
        mAncRar: "Raridade Histórica",
        mAncDagTitle: "🌳 Impacto no Grafo Acíclico Direcionado (DAG 5 Gerações — 504.074 Nós)",
        mAncDagDesc: (inb, gw) => `Este ancestral aparece simultaneamente nos lados paterno e materno (Menor Ancestral Comum — LCA) de <b>${{inb}}</b> cavalos de elite da JRA, acumulando <b>${{gw}}</b> vitórias em provas Graded através de cruzamentos consanguíneos planejados (3x4, 4x4 e 4x5).`,
        horseAxes: ["PageRank Prestige", "Letalidade (Vitórias)", "Consistência Pódio", "Poder de Premiação", "Índice Estamina", "Força dos Rivais"],
        sireAxes: ["Volume de Filhos", "Domínio em G1", "Taxa de Vitória", "Taxa de Pódio", "Afinidade Grama", "PageRank dos Filhos"],
        jockeyAxes: ["Vitórias Graded", "Títulos de G1", "Taxa de Vitória", "Consistência Top-3", "Volume de Montarias", "Diversidade Equina"],
        ancAxes: ["Alcance Endogâmico", "Vitórias da Prole", "Impacto Genético", "Eficiência G1", "Presença 5-Gen", "Prestígio Histórico"]
      }},
      en: {{
        title: "JRA & JBIS TCG Arena — Gamified Card Ranking Explorer",
        subtitle: "Explore Sports PageRank, 5-Gen Bloodlines, Earnings & Jockeys as Collectible Cards • Click any Card to open the 3D Dossier",
        linkSuperset: "📊 Superset Dashboard (13 Charts)",
        supersetHref: "superset_interactive_dashboard_en.html",
        heroHeading: "💡 How does this Scientific Trading Card Game work?",
        heroDesc: "Every racehorse, breeding stallion, jockey, and founding patriarch (2002–2025) is modeled as a Collectible Card with an Overall Rating (OVR 76–99) derived from Graph Theory (PageRank). <b>DIAMOND (Underdog Diamond)</b> cards have 0 Graded wins yet repeatedly placed against historic G1 legends!",
        pillSsr: "🌟 SSR MYTHIC (Top PageRank / G1 Legends)",
        pillDia: "💎 DIAMOND (0 Wins, Ultra-High PageRank!)",
        pillSil: "🥈 SILVER CROWN (Uncrowned G1 Kings)",
        pillUr: "🟣 UR EPIC (G1 Champions)",
        pillSr: "🔵 SR RARE (Graded Winners)",
        tabPr: "1. Global PageRank Leaderboard",
        tabEarn: "2. Top Lifetime Earnings (¥)",
        tabSires: "3. Dynasty Sires (Most Progeny)",
        tabAnom: "4. Underdog Diamonds (0 Wins)",
        tabJock: "5. Master Jockeys",
        tabAnc: "6. 5-Gen Founding Patriarchs",
        searchPh: "Search horse, sire (e.g. Deep Impact), jockey (e.g. Yutaka Take), birth year, or Japanese name...",
        optRarityAll: "All Rarities (SSR / DIAMOND / UR / SR)",
        optRaritySsr: "🌟 SSR Mythic Legend",
        optRarityDia: "💎 Diamond Anomaly (0 Wins)",
        optRaritySil: "🥈 Silver Crown (0 G1 Wins)",
        optRarityUr: "🟣 UR Epic",
        optRaritySr: "🔵 SR Rare",
        optSurfAll: "All Surfaces (Turf & Dirt)",
        optSurfTurf: "🌿 Turf",
        optSurfDirt: "🔥 Dirt",
        optSortDef: "Default Deck Ranking",
        optSortOvr: "Highest Overall Rating (OVR 99→75)",
        optSortWins: "Most Graded / G1 Wins",
        optSortEarn: "Highest Earnings / Most Progeny",
        optSortBirth: "Birth Year (Oldest → Newest)",
        btnReset: "↺ Reset Filters",
        btnVsCancel: "✕ Cancel",
        emptyMsg: "No Cards matched this filter. Click 'Reset Filters' to restore!",
        counterFmt: (vis, tot) => `Showing ${{vis}} of ${{tot}} Cards`,
        btnLoadMore: "Load More Cards (+36)",
        inspectHint: "🔍 Click to Expand",
        bornLbl: "Born",
        sireLbl: "Sire",
        startsLbl: "Starts",
        winsLbl: "Wins",
        podiumsLbl: "Podiums",
        progenyLbl: "Graded Progeny",
        inbredLbl: "Inbred Horses",
        estTag: " (Est.)",
        barPr: "⚔️ PageRank",
        barWinG1: "🏆 Win/G1",
        barTop3: "🛡️ Top-3 %",
        barEarn: "💰 Earnings",
        barProg: "🧬 Progeny",
        barG1Pow: "👑 G1 Power",
        barKidsPr: "⚔️ Kids PR",
        barWins: "🏆 Wins",
        barG1Tit: "👑 G1 Titles",
        barSyn: "🏇 Synergy",
        barInb: "🌳 Inbreed",
        barProgW: "🏆 Progeny W",
        barImp: "🧬 Impact",
        barPrest: "👑 Prestige",
        chip5Gen: "5-Gen Patriarch",
        footGradedWins: "Graded Wins",
        footStarts: "Starts",
        footAce: "Partner",
        footInbWins: "Inbred Progeny Wins",
        duelBtn: "⚔️ Compare with another Card (VS Duel Mode)",
        duelPrompt: "⚔️ VS Duel Mode active! Click any other card of the same type to compare against: ",
        duelSameWarn: "⚠️ Pick a different card to start the VS Duel!",
        duelAttrHeader: "📊 Direct Attribute Comparison (0–100)",
        mGlobalPr: "Global PageRank",
        mBirthPeak: "Birth Year (Peak)",
        mPeakWord: "Peak",
        mGradedRec: "Graded Record",
        mG1Titles: "G1 Titles",
        mEarnings: "Career Earnings",
        mBioCoat: "Biometrics & Coat",
        mSurfDist: "Surface & Distance",
        mWrightFx: "Wright Inbreeding F_X",
        mPedHeader: "🧬 Direct Pedigree Tree & Connections (Click Sire / Dam's Sire to open their Card!)",
        mSireNode: "SIRE (FATHER) 🔗",
        mDamNode: "DAM (MOTHER)",
        mDamSireNode: "DAM'S SIRE (MATERNAL GRANDSIRE) 🔗",
        mTeamNode: "PRIMARY JOCKEY & TRAINER",
        mSigRace: "🏆 Signature Race:",
        mCrosses: "🔬 5-Gen Inbreeding Crosses (LCA):",
        mBreederOwner: "🏡 Breeder / Owner:",
        mLayHorse: "💡 <b>Layperson Guide:</b> <b>PageRank</b> measures true competitive prestige weighted by opponent strength. <b>Wright's Coefficient (F_X)</b> measures the percentage of duplicated ancestral blood across 5 generations.",
        mSireRank: "Sire Ranking",
        mSireProg: "Graded Progeny",
        mSireStarts: "Progeny Starts",
        mSireWinsG1: "Graded / G1 Wins",
        mSirePodRt: "Top-3 Podium Rate",
        mSireTurf: "Turf Affinity",
        mSireDist: "Mean Distance",
        mSirePca: "2D PCA Coordinates",
        mSireArchTitle: "🧬 K-Means++ PCA Archetype:",
        mSireKidsDesc: "Top champion offspring of this stallion (click any horse to open its Card):",
        mLaySire: "💡 <b>Layperson Guide:</b> All 106 stallions were automatically segmented via <b>K-Means++ and 2D PCA</b> into 4 genetic archetypes (Dirt Power, Speed/Mile, Elite G1 Dynasties, and Classic Stayers).",
        mJockRank: "Jockey Ranking",
        mJockWins: "Graded Wins",
        mJockG1: "G1 Titles",
        mJockPod: "Top-3 Podiums",
        mJockWinRt: "Win Rate",
        mJockStarts: "Graded Rides",
        mJockPartTitle: "🤝 Bipartite Jockey ↔ Horse Network (Clickable Signature Partners)",
        mLayJock: "💡 <b>Layperson Guide:</b> In our <b>Random Forest classifier (ROC-AUC = 0.7260)</b>, the jockey's prior podium rate was the #1 most influential feature (29.8% relative Gini importance)!",
        mAncRank: "Founding Patriarch",
        mAncInb: "Inbred Horses (LCA)",
        mAncWins: "Progeny Graded Wins",
        mAncRar: "Historical Rarity",
        mAncDagTitle: "🌳 Impact in the 5-Generation Directed Acyclic Graph (504,074 Nodes)",
        mAncDagDesc: (inb, gw) => `This founding ancestor appears simultaneously on both paternal and maternal sides (Lowest Common Ancestor — LCA) of <b>${{inb}}</b> elite JRA racehorses, driving <b>${{gw}}</b> Graded victories through deliberate linebreeding (3x4, 4x4, and 4x5 crosses).`,
        horseAxes: ["PageRank Prestige", "Win Lethality", "Podium Consistency", "Earnings Power", "Stamina Index", "Rivalry Volume"],
        sireAxes: ["Progeny Volume", "G1 Dominance", "Win Rate", "Podium Rate", "Turf Affinity", "Progeny PageRank"],
        jockeyAxes: ["Graded Wins", "G1 Titles", "Win Rate", "Top-3 Consistency", "Ride Volume", "Horse Diversity"],
        ancAxes: ["Inbreeding Reach", "Progeny Wins", "Genetic Impact", "G1 Efficiency", "5-Gen Presence", "Historical Prestige"]
      }},
      ja: {{
        title: "JRA & JBIS TCG アリーナ — 競走馬・血統カードランキング",
        subtitle: "PageRank・5代血統・獲得賞金・騎手をトレーディングカード形式で可視化 • カードをクリックすると3D詳細ドシエが開きます",
        linkSuperset: "📊 Superset ダッシュボード (全13チャート)",
        supersetHref: "superset_interactive_dashboard_ja.html",
        heroHeading: "💡 科学データ・トレーディングカード（TCG）の仕組み",
        heroDesc: "2002〜2025年の全重賞競走馬・種牡馬・騎手・5代基礎種牡馬をグラフ理論（PageRank）に基づく総合レート（OVR 76–99）付きカードとしてモデル化。特別レアリティ <b>DIAMOND（無冠の名馬）</b> は重賞0勝ながらG1戦線で強豪を破り続けた名脇役を示します！",
        pillSsr: "🌟 SSR MYTHIC (最高峰PageRank / G1レジェンド)",
        pillDia: "💎 DIAMOND (無冠の名馬: 重賞0勝・超高PR!)",
        pillSil: "🥈 SILVER CROWN (G1未勝利の名脇役)",
        pillUr: "🟣 UR EPIC (G1タイトルホルダー)",
        pillSr: "🔵 SR RARE (重賞ウィナー)",
        tabPr: "1. 総合PageRankランキング",
        tabEarn: "2. 生涯獲得賞金ランキング",
        tabSires: "3. 種牡馬（産駒数・G1勝利）",
        tabAnom: "4. 無冠の名馬（重賞0勝・高PR）",
        tabJock: "5. トップ騎手カード",
        tabAnc: "6. 5代血統・基礎種牡馬 (F_X)",
        searchPh: "馬名、種牡馬（例: Deep Impact）、騎手（例: 武豊）、生年、日本語名で検索...",
        optRarityAll: "全レアリティ (SSR / DIAMOND / UR / SR)",
        optRaritySsr: "🌟 SSR Mythic Legend (神話級)",
        optRarityDia: "💎 Diamond Anomaly (無冠の名馬・0勝)",
        optRaritySil: "🥈 Silver Crown (G1未勝利の名馬)",
        optRarityUr: "🟣 UR Epic (G1王者)",
        optRaritySr: "🔵 SR Rare (重賞馬)",
        optSurfAll: "全馬場 (芝 & ダート)",
        optSurfTurf: "🌿 芝 (Turf)",
        optSurfDirt: "🔥 ダート (Dirt)",
        optSortDef: "デッキ標準ランキング順",
        optSortOvr: "総合レート順 (OVR 99→75)",
        optSortWins: "重賞・G1勝利数順",
        optSortEarn: "獲得賞金・産駒数順",
        optSortBirth: "生年順 (古い順 → 新しい順)",
        btnReset: "↺ フィルタ解除",
        btnVsCancel: "✕ キャンセル",
        emptyMsg: "条件に一致するカードが見つかりません。「フィルタ解除」をクリックしてください。",
        counterFmt: (vis, tot) => `全 ${{tot}} 枚中 ${{vis}} 枚を表示`,
        btnLoadMore: "さらにカードを表示 (+36枚)",
        inspectHint: "🔍 クリックで詳細拡大",
        bornLbl: "生年",
        sireLbl: "父",
        startsLbl: "重賞出走",
        winsLbl: "重賞勝鞍",
        podiumsLbl: "3着以内",
        progenyLbl: "重賞産駒",
        inbredLbl: "インブリード頭数",
        estTag: " (推定)",
        barPr: "⚔️ PageRank",
        barWinG1: "🏆 勝率/G1",
        barTop3: "🛡️ 複勝率 %",
        barEarn: "💰 獲得賞金",
        barProg: "🧬 産駒規模",
        barG1Pow: "👑 G1制覇力",
        barKidsPr: "⚔️ 産駒PR",
        barWins: "🏆 重賞勝鞍",
        barG1Tit: "👑 G1勝利",
        barSyn: "🏇 騎乗相性",
        barInb: "🌳 近交浸透",
        barProgW: "🏆 産駒勝鞍",
        barImp: "🧬 血統影響",
        barPrest: "👑 歴史威信",
        chip5Gen: "5代血統基礎種牡馬",
        footGradedWins: "重賞勝利",
        footStarts: "出走",
        footAce: "代表パートナー",
        footInbWins: "インブリード産駒重賞勝鞍",
        duelBtn: "⚔️ 他のカードと能力比較（VSデュエルモード）",
        duelPrompt: "⚔️ VSデュエルモード起動中！比較したい同じカテゴリのカードをクリック: ",
        duelSameWarn: "⚠️ 比較するには別のカードを選択してください！",
        duelAttrHeader: "📊 6次元能力ステータス直接比較 (0–100)",
        mGlobalPr: "総合PageRank順位",
        mBirthPeak: "生年 (ピーク年)",
        mPeakWord: "ピーク",
        mGradedRec: "重賞通算成績",
        mG1Titles: "G1タイトル数",
        mEarnings: "生涯獲得賞金",
        mBioCoat: "馬体重・毛色",
        mSurfDist: "主戦馬場・平均距離",
        mWrightFx: "ライト近交係数 F_X",
        mPedHeader: "🧬 血統構成＆コネクション（父・母父をクリックすると該当カードへジャンプします！）",
        mSireNode: "父 (SIRE) 🔗",
        mDamNode: "母 (DAM)",
        mDamSireNode: "母父 (DAM'S SIRE) 🔗",
        mTeamNode: "主戦騎手 & 管理調教師",
        mSigRace: "🏆 代表ベストレース:",
        mCrosses: "🔬 5代血統インブリードクロス (LCA):",
        mBreederOwner: "🏡 生産牧場 / 馬主:",
        mLayHorse: "💡 <b>初心者ガイド:</b> <b>PageRank</b>は対戦相手の強さを考慮した真の実力指標です。<b>ライトの近交係数 (F_X)</b>は5代血統内で同一祖先が重複する割合（奇跡の血量 6.25%＝3×4クロス等）を示します。",
        mSireRank: "種牡馬ランキング",
        mSireProg: "重賞出走産駒数",
        mSireStarts: "産駒重賞延べ出走",
        mSireWinsG1: "重賞勝鞍 (うちG1)",
        mSirePodRt: "産駒複勝率 (勝率)",
        mSireTurf: "芝コース出走比率",
        mSireDist: "産駒平均距離",
        mSirePca: "2次元PCA座標",
        mSireArchTitle: "🧬 K-Means++ PCA 遺伝的アーキタイプ:",
        mSireKidsDesc: "主な代表産駒（馬名をクリックするとその競走馬カードを開きます）:",
        mLaySire: "💡 <b>初心者ガイド:</b> 主要種牡馬106頭は<b>K-Means++法と主成分分析 (PCA)</b> により4つの系統（ダートパワー型、芝スプリント・マイル型、G1クラシック王朝型、芝ステイヤー型）に自動分類されています。",
        mJockRank: "騎手ランキング",
        mJockWins: "重賞勝利数",
        mJockG1: "G1制覇数",
        mJockPod: "重賞3着以内",
        mJockWinRt: "重賞勝率",
        mJockStarts: "重賞騎乗数",
        mJockPartTitle: "🤝 騎手 ↔ 競走馬 二部グラフ（クリックで代表コンビ馬のカードへ）",
        mLayJock: "💡 <b>初心者ガイド:</b> 私たちの<b>ランダムフォレスト予測モデル (ROC-AUC = 0.7260)</b> において、騎手の過去重賞複勝率は全特徴量の中で第1位（Gini重要度 29.8%）の決定力を持ちます！",
        mAncRank: "基礎種牡馬ランク",
        mAncInb: "インブリード競走馬数",
        mAncWins: "該当産駒の重賞勝鞍",
        mAncRar: "歴史的レアリティ",
        mAncDagTitle: "🌳 5代血統有向非巡回グラフ（DAG — 504,074ノード）における遺伝的支配力",
        mAncDagDesc: (inb, gw) => `この基礎祖先はJRA重賞出走馬 <b>${{inb}}</b> 頭の父系・母系双方に共通祖先（LCA）として出現し、計画的なインブリード（3×4、4×4、4×5クロス等）を通じて重賞 <b>${{gw}}</b> 勝を生み出しています。`,
        horseAxes: ["PageRank威信", "勝率・決定力", "複勝安定度", "獲得賞金力", "スタミナ指数", "G1対戦強度"],
        sireAxes: ["重賞産駒数", "G1制覇力", "産駒勝率", "産駒複勝率", "芝適性度", "産駒平均PR"],
        jockeyAxes: ["重賞勝利数", "G1タイトル", "重賞勝率", "3着内安定度", "騎乗数", "騎乗馬多様性"],
        ancAxes: ["インブリード浸透", "産駒重賞勝鞍", "遺伝的影響力", "G1効率", "5代出現頻度", "歴史的威信"]
      }}
    }};

    let currentLang = 'pt';
    let currentDeck = 'pagerank';
    let filteredList = [];
    let visibleLimit = 36;
    let modalChartInstance = null;
    let duelCard1 = null;
    let activeModalState = null;

    // Normalizador de nomes imune a apóstrofos (' / ’) e códigos de país ((USA), (GB), etc.)
    function normName(s) {{
      if (!s) return '';
      return String(s)
        .replace(/\\([A-Z]{{2,4}}\\)/gi, '')
        .replace(/[’'`]/g, '')
        .replace(/\\s+/g, ' ')
        .trim()
        .toLowerCase();
    }}

    // Populate deck counts
    const anomaliesDeck = HORSES_DATA.filter(h => h.rarity === 'DIAMOND' || h.rarity === 'SILVER').sort((a,b) => a.rank - b.rank);
    const earningsDeck = [...HORSES_DATA].sort((a,b) => b.earn - a.earn);
    document.getElementById('cnt_pagerank').textContent = HORSES_DATA.length;
    document.getElementById('cnt_earnings').textContent = earningsDeck.length;
    document.getElementById('cnt_sires').textContent = SIRES_DATA.length;
    document.getElementById('cnt_anomalies').textContent = anomaliesDeck.length;
    document.getElementById('cnt_jockeys').textContent = JOCKEYS_DATA.length;
    document.getElementById('cnt_ancestors').textContent = ANCESTORS_DATA.length;

    function getBaseDeck() {{
      if (currentDeck === 'pagerank') return [...HORSES_DATA].sort((a,b) => a.rank - b.rank);
      if (currentDeck === 'earnings') return [...earningsDeck];
      if (currentDeck === 'sires') return [...SIRES_DATA];
      if (currentDeck === 'anomalies') return [...anomaliesDeck];
      if (currentDeck === 'jockeys') return [...JOCKEYS_DATA];
      if (currentDeck === 'ancestors') return [...ANCESTORS_DATA];
      return [...HORSES_DATA];
    }}

    function switchDeck(deckName) {{
      currentDeck = deckName;
      visibleLimit = 36;
      document.querySelectorAll('.deck-tab').forEach(b => b.classList.remove('active'));
      const activeBtn = document.getElementById('tab_' + deckName);
      if (activeBtn) activeBtn.classList.add('active');
      document.getElementById('sortSelect').value = 'DEFAULT';
      applyFilters();
    }}

    function resetAllFilters() {{
      document.getElementById('searchInput').value = '';
      document.getElementById('rarityFilter').value = 'ALL';
      document.getElementById('surfaceFilter').value = 'ALL';
      document.getElementById('sortSelect').value = 'DEFAULT';
      visibleLimit = 36;
      applyFilters();
    }}

    function setLanguage(lang) {{
      if (!I18N[lang]) lang = 'pt';
      currentLang = lang;
      document.documentElement.lang = lang === 'pt' ? 'pt-BR' : lang;
      document.querySelectorAll('.lang-btn').forEach(b => b.classList.remove('active'));
      const btnId = 'btnLang' + lang.charAt(0).toUpperCase() + lang.slice(1);
      if (document.getElementById(btnId)) document.getElementById(btnId).classList.add('active');

      const t = I18N[lang];
      document.getElementById('uiTitle').textContent = t.title;
      document.getElementById('uiSubtitle').textContent = t.subtitle;
      const supLink = document.getElementById('linkSuperset');
      supLink.textContent = t.linkSuperset;
      supLink.href = t.supersetHref;
      document.getElementById('heroHeading').textContent = t.heroHeading;
      document.getElementById('heroDesc').innerHTML = t.heroDesc;
      document.getElementById('pillSsr').textContent = t.pillSsr;
      document.getElementById('pillDia').textContent = t.pillDia;
      document.getElementById('pillSil').textContent = t.pillSil;
      document.getElementById('pillUr').textContent = t.pillUr;
      document.getElementById('pillSr').textContent = t.pillSr;
      document.getElementById('lblTabPr').textContent = t.tabPr;
      document.getElementById('lblTabEarn').textContent = t.tabEarn;
      document.getElementById('lblTabSires').textContent = t.tabSires;
      document.getElementById('lblTabAnom').textContent = t.tabAnom;
      document.getElementById('lblTabJock').textContent = t.tabJock;
      document.getElementById('lblTabAnc').textContent = t.tabAnc;
      document.getElementById('searchInput').placeholder = t.searchPh;
      document.getElementById('optRarityAll').textContent = t.optRarityAll;
      document.getElementById('optRaritySsr').textContent = t.optRaritySsr;
      document.getElementById('optRarityDia').textContent = t.optRarityDia;
      document.getElementById('optRaritySil').textContent = t.optRaritySil;
      document.getElementById('optRarityUr').textContent = t.optRarityUr;
      document.getElementById('optRaritySr').textContent = t.optRaritySr;
      document.getElementById('optSurfAll').textContent = t.optSurfAll;
      document.getElementById('optSurfTurf').textContent = t.optSurfTurf;
      document.getElementById('optSurfDirt').textContent = t.optSurfDirt;
      document.getElementById('optSortDef').textContent = t.optSortDef;
      document.getElementById('optSortOvr').textContent = t.optSortOvr;
      document.getElementById('optSortWins').textContent = t.optSortWins;
      document.getElementById('optSortEarn').textContent = t.optSortEarn;
      document.getElementById('optSortBirth').textContent = t.optSortBirth;
      document.getElementById('btnResetFilters').textContent = t.btnReset;
      document.getElementById('btnVsCancel').textContent = t.btnVsCancel;
      document.getElementById('btnLoadMore').textContent = t.btnLoadMore;

      // Atualizar banner VS se estiver ativo
      if (duelCard1) {{
        document.getElementById('vsBannerText').innerHTML = t.duelPrompt + `<b>${{duelCard1.name}}</b>`;
      }}

      // Re-renderizar modal aberto se houver (BUG-06 fix)
      if (activeModalState && document.getElementById('cardModal').classList.contains('open')) {{
        if (activeModalState.mode === 'card') {{
          openCardModal(activeModalState.card);
        }} else if (activeModalState.mode === 'duel') {{
          openDuelModal(activeModalState.c1, activeModalState.c2);
        }}
      }}

      renderGrid();
    }}

    function applyFilters() {{
      const rawQ = document.getElementById('searchInput').value.trim();
      const q = normName(rawQ);
      const qLower = rawQ.toLowerCase();
      const rar = document.getElementById('rarityFilter').value;
      const surf = document.getElementById('surfaceFilter').value;
      const sortMode = document.getElementById('sortSelect').value;

      let list = getBaseDeck();
      if (rawQ) {{
        list = list.filter(item => {{
          const rawBlob = [
            item.name, item.ja, item.sire, item.dam, item.damsire,
            item.jockey, item.trainer, item.birth, item.archetype,
            ...(item.top_kids || []), ...(item.partners || [])
          ].filter(Boolean).join(' ');
          return rawBlob.toLowerCase().includes(qLower) || normName(rawBlob).includes(q);
        }});
      }}
      if (rar !== 'ALL') {{
        list = list.filter(item => item.rarity === rar);
      }}
      if (surf !== 'ALL') {{
        list = list.filter(item => {{
          if (item.type === 'horse') return item.surf === surf;
          if (item.type === 'sire') return surf === 'Turf' ? item.turf_pct >= 50 : item.turf_pct < 50;
          return true;
        }});
      }}

      if (sortMode === 'OVR_DESC') list.sort((a,b) => b.ovr - a.ovr);
      else if (sortMode === 'WINS_DESC') list.sort((a,b) => ((b.g1 || 0)*100 + (b.wins || b.graded_wins || 0)) - ((a.g1 || 0)*100 + (a.wins || a.graded_wins || 0)));
      else if (sortMode === 'EARN_DESC') list.sort((a,b) => (b.earn || b.progeny || b.inbred_horses || b.wins || 0) - (a.earn || a.progeny || a.inbred_horses || a.wins || 0));
      else if (sortMode === 'BIRTH_ASC') list.sort((a,b) => (a.birth || a.rank || 9999) - (b.birth || b.rank || 9999));

      filteredList = list;
      renderGrid();
    }}

    function loadMoreCards() {{
      visibleLimit += 36;
      renderGrid();
    }}

    function getAvatarGradient(item) {{
      if (item.rarity === 'DIAMOND') return ['💎', 'linear-gradient(135deg, #06b6d4, #3b82f6)'];
      if (item.rarity === 'SILVER') return ['🥈', 'linear-gradient(135deg, #64748b, #cbd5e1)'];
      if (item.type === 'sire') return ['🧬', 'linear-gradient(135deg, #7c3aed, #ec4899)'];
      if (item.type === 'jockey') return ['🏇', 'linear-gradient(135deg, #0284c7, #10b981)'];
      if (item.type === 'ancestor') return ['🌳', 'linear-gradient(135deg, #d97706, #7c3aed)'];
      if (item.surf === 'Dirt') return ['🔥', 'linear-gradient(135deg, #d97706, #b45309)'];
      if (item.dist <= 1450) return ['⚡', 'linear-gradient(135deg, #0284c7, #38bdf8)'];
      return ['🏆', 'linear-gradient(135deg, #7c3aed, #10b981)'];
    }}

    function renderStatBar(label, val, color) {{
      return `<div class="stat-row">
        <span class="stat-label">${{label}}</span>
        <div class="stat-track"><div class="stat-fill" style="width:${{Math.min(100, Math.max(4, val))}}%;background:${{color}};"></div></div>
        <span class="stat-num">${{val}}</span>
      </div>`;
    }}

    function renderGrid() {{
      const grid = document.getElementById('cardsGrid');
      const t = I18N[currentLang];
      const slice = filteredList.slice(0, visibleLimit);

      document.getElementById('resultCounter').textContent = t.counterFmt(slice.length, filteredList.length);

      if (slice.length === 0) {{
        grid.innerHTML = `<div style="grid-column:1/-1;text-align:center;padding:48px;color:#94a3b8;font-size:15px;">${{t.emptyMsg}}</div>`;
        document.getElementById('loadMoreWrap').style.display = 'none';
        return;
      }}

      grid.innerHTML = slice.map((item, idx) => {{
        const displayRank = currentDeck === 'pagerank' && document.getElementById('sortSelect').value === 'DEFAULT' ? item.rank : (idx + 1);
        const rankCls = displayRank === 1 ? 'top1' : (displayRank === 2 ? 'top2' : (displayRank === 3 ? 'top3' : ''));
        const [icon, grad] = getAvatarGradient(item);

        let chipsHtml = '';
        let barsHtml = '';
        let footLeft = '';

        if (item.type === 'horse') {{
          const sCls = item.surf === 'Dirt' ? 'dirt' : 'turf';
          chipsHtml = `
            <span class="meta-chip">${{t.bornLbl}} ${{item.birth}}</span>
            <span class="meta-chip ${{sCls}}">${{item.surf}} • ${{item.dist}}m</span>
            <span class="meta-chip">${{item.wins}}W / ${{item.podiums}}P (G1: ${{item.g1}})</span>
          `;
          barsHtml =
            renderStatBar(t.barPr, item.stats[0], '#a855f7') +
            renderStatBar(t.barWinG1, item.stats[1], '#fbbf24') +
            renderStatBar(t.barTop3, item.stats[2], '#38bdf8') +
            renderStatBar(t.barEarn, item.stats[3], '#10b981');
          footLeft = `${{t.sireLbl}}: <b>${{item.sire}}</b> • <b>¥${{item.earn}}M${{item.earn_est ? t.estTag : ''}}</b>`;
        }} else if (item.type === 'sire') {{
          const sCls = item.turf_pct >= 50 ? 'turf' : 'dirt';
          chipsHtml = `
            <span class="meta-chip ${{sCls}}">Turf ${{item.turf_pct}}% • ${{item.dist}}m</span>
            <span class="meta-chip">${{t.progenyLbl}}: ${{item.progeny}}</span>
            <span class="meta-chip">G1: ${{item.g1}}</span>
          `;
          barsHtml =
            renderStatBar(t.barProg, item.stats[0], '#38bdf8') +
            renderStatBar(t.barG1Pow, item.stats[1], '#fbbf24') +
            renderStatBar(t.barTop3, item.stats[3], '#10b981') +
            renderStatBar(t.barKidsPr, item.stats[5], '#a855f7');
          footLeft = `<b>${{item.wins}}</b> ${{t.footGradedWins}} • <b>${{item.entries}}</b> ${{t.footStarts}}`;
        }} else if (item.type === 'jockey') {{
          chipsHtml = `
            <span class="meta-chip">${{t.winsLbl}}: ${{item.wins}} (G1: ${{item.g1}})</span>
            <span class="meta-chip">Top-3: ${{item.pod_rt}}%</span>
            <span class="meta-chip">${{t.startsLbl}}: ${{item.starts}}</span>
          `;
          barsHtml =
            renderStatBar(t.barWins, item.stats[0], '#38bdf8') +
            renderStatBar(t.barG1Tit, item.stats[1], '#fbbf24') +
            renderStatBar(t.barTop3, item.stats[3], '#10b981') +
            renderStatBar(t.barSyn, item.stats[5], '#a855f7');
          footLeft = `${{t.footAce}}: <b>${{(item.partners && item.partners[0]) || 'JRA'}}</b>`;
        }} else {{
          chipsHtml = `
            <span class="meta-chip">${{t.chip5Gen}}</span>
            <span class="meta-chip">${{t.inbredLbl}}: ${{item.inbred_horses.toLocaleString()}}</span>
          `;
          barsHtml =
            renderStatBar(t.barInb, item.stats[0], '#f59e0b') +
            renderStatBar(t.barProgW, item.stats[1], '#fbbf24') +
            renderStatBar(t.barImp, item.stats[2], '#a855f7') +
            renderStatBar(t.barPrest, item.stats[5], '#38bdf8');
          footLeft = `${{t.footInbWins}}: <b>${{item.graded_wins.toLocaleString()}}</b>`;
        }}

        return `<article class="tcg-card rarity-${{item.rarity}}" onclick="onCardClick('${{item.id}}')" data-card-id="${{item.id}}">
          <div>
            <div class="card-top">
              <span class="rank-badge ${{rankCls}}">#${{displayRank}}</span>
              <div class="ovr-group">
                <span class="rarity-tag ${{item.rarity}}">${{item.rarity}}</span>
                <span class="ovr-circle">OVR ${{item.ovr}}</span>
              </div>
            </div>
            <div class="card-Crest">
              <div class="crest-avatar" style="background:${{grad}};">${{icon}}</div>
              <div class="crest-info">
                <h3 class="crest-name">${{item.name}}</h3>
                <div class="crest-ja">${{item.ja || item.elem || item.archetype || 'JRA Elite'}}</div>
                <div class="crest-meta">${{chipsHtml}}</div>
              </div>
            </div>
            <div class="stat-bars">${{barsHtml}}</div>
          </div>
          <div class="card-foot">
            <span>${{footLeft}}</span>
            <span class="inspect-hint">${{t.inspectHint}}</span>
          </div>
        </article>`;
      }}).join('');

      document.getElementById('loadMoreWrap').style.display = filteredList.length > visibleLimit ? 'block' : 'none';
    }}

    function findCardById(id) {{
      return HORSES_DATA.find(x => x.id === id)
          || SIRES_DATA.find(x => x.id === id)
          || JOCKEYS_DATA.find(x => x.id === id)
          || ANCESTORS_DATA.find(x => x.id === id);
    }}

    function findCardByName(name) {{
      if (!name) return null;
      const target = normName(name);
      return HORSES_DATA.find(x => normName(x.name) === target)
          || SIRES_DATA.find(x => normName(x.name) === target)
          || ANCESTORS_DATA.find(x => normName(x.name) === target)
          || JOCKEYS_DATA.find(x => normName(x.name) === target);
    }}

    function onCardClick(id) {{
      const card = findCardById(id);
      if (!card) return;
      if (duelCard1) {{
        if (duelCard1.id === card.id) {{
          alert(I18N[currentLang].duelSameWarn);
          return;
        }}
        openDuelModal(duelCard1, card);
        cancelDuelMode();
        return;
      }}
      openCardModal(card);
    }}

    function startDuelMode(id) {{
      const card = findCardById(id);
      if (!card) return;
      duelCard1 = card;
      closeModal();
      const banner = document.getElementById('vsBanner');
      document.getElementById('vsBannerText').innerHTML = I18N[currentLang].duelPrompt + `<b>${{card.name}}</b>`;
      banner.classList.add('active');
    }}

    function cancelDuelMode() {{
      duelCard1 = null;
      document.getElementById('vsBanner').classList.remove('active');
    }}

    function jumpToEntityName(encodedName) {{
      const name = decodeURIComponent(encodedName);
      const target = findCardByName(name);
      if (target) {{
        openCardModal(target);
      }} else {{
        closeModal();
        document.getElementById('searchInput').value = name;
        applyFilters();
      }}
    }}

    function getAxesForType(type, t) {{
      if (type === 'sire') return t.sireAxes;
      if (type === 'jockey') return t.jockeyAxes;
      if (type === 'ancestor') return t.ancAxes;
      return t.horseAxes;
    }}

    function openCardModal(card) {{
      activeModalState = {{ mode: 'card', card: card }};
      const t = I18N[currentLang];
      const modal = document.getElementById('cardModal');
      const content = document.getElementById('modalContent');
      const [icon, grad] = getAvatarGradient(card);

      let detailsHtml = '';
      const radarAxes = getAxesForType(card.type, t);

      if (card.type === 'horse') {{
        const sireCard = findCardByName(card.sire);
        const damsireCard = findCardByName(card.damsire);
        const encSire = encodeURIComponent(card.sire);
        const encDamSire = encodeURIComponent(card.damsire);
        const encJockey = encodeURIComponent(card.jockey);

        detailsHtml = `
          <div class="dossier-kpis">
            <div class="d-kpi"><span>${{t.mGlobalPr}}</span><strong>#${{card.rank}} (${{card.pr}})</strong></div>
            <div class="d-kpi"><span>${{t.mBirthPeak}}</span><strong>${{card.birth}} (${{t.mPeakWord}}: ${{card.peak}})</strong></div>
            <div class="d-kpi"><span>${{t.mGradedRec}}</span><strong>${{card.wins}}W / ${{card.podiums}}P / ${{card.starts}}S</strong></div>
            <div class="d-kpi"><span>${{t.mG1Titles}}</span><strong>${{card.g1}} G1</strong></div>
            <div class="d-kpi"><span>${{t.mEarnings}}</span><strong>¥${{card.earn}}M${{card.earn_est ? t.estTag : ''}}</strong></div>
            <div class="d-kpi"><span>${{t.mBioCoat}}</span><strong>${{card.mass}}kg • ${{card.color}}</strong></div>
            <div class="d-kpi"><span>${{t.mSurfDist}}</span><strong>${{card.surf}} (${{card.dist}}m)</strong></div>
            <div class="d-kpi"><span>${{t.mWrightFx}}</span><strong>${{card.fx}}%</strong></div>
          </div>
          <div class="pedigree-box">
            <h4>${{t.mPedHeader}}</h4>
            <div class="ped-tree-mini">
              <div class="ped-node ${{sireCard ? 'clickable' : ''}}" onclick="jumpToEntityName('${{encSire}}')">
                <small>${{t.mSireNode}}</small>
                <b>${{card.sire}}</b>
              </div>
              <div class="ped-node">
                <small>${{t.mDamNode}}</small>
                <b>${{card.dam}}</b>
              </div>
              <div class="ped-node ${{damsireCard ? 'clickable' : ''}}" onclick="jumpToEntityName('${{encDamSire}}')">
                <small>${{t.mDamSireNode}}</small>
                <b>${{card.damsire}}</b>
              </div>
              <div class="ped-node clickable" onclick="jumpToEntityName('${{encJockey}}')">
                <small>${{t.mTeamNode}} 🔗</small>
                <b>${{card.jockey}} • ${{card.trainer}}</b>
              </div>
            </div>
            <div style="margin-top:10px;font-size:12px;color:#cbd5e1;line-height:1.5;">
              <b>${{t.mSigRace}}</b> ${{card.sig_race}}<br/>
              <b>${{t.mCrosses}}</b> ${{card.crosses}}<br/>
              <b>${{t.mBreederOwner}}</b> ${{card.breeder}} • ${{card.owner}}
            </div>
            <div class="layperson-note">${{t.mLayHorse}}</div>
          </div>
        `;
      }} else if (card.type === 'sire') {{
        const kidsHtml = (card.top_kids || []).map(k =>
          `<span class="meta-chip turf" style="cursor:pointer;padding:4px 9px;font-size:11.5px;" onclick="jumpToEntityName('${{encodeURIComponent(k)}}')">🏇 ${{k}} 🔗</span>`
        ).join(' ');
        detailsHtml = `
          <div class="dossier-kpis">
            <div class="d-kpi"><span>${{t.mSireRank}}</span><strong>#${{card.rank}}</strong></div>
            <div class="d-kpi"><span>${{t.mSireProg}}</span><strong>${{card.progeny}}</strong></div>
            <div class="d-kpi"><span>${{t.mSireStarts}}</span><strong>${{card.entries}}</strong></div>
            <div class="d-kpi"><span>${{t.mSireWinsG1}}</span><strong>${{card.wins}}W (${{card.g1}} G1)</strong></div>
            <div class="d-kpi"><span>${{t.mSirePodRt}}</span><strong>${{card.pod_rt}}% (${{card.win_rt}}%)</strong></div>
            <div class="d-kpi"><span>${{t.mSireTurf}}</span><strong>${{card.turf_pct}}% Turf</strong></div>
            <div class="d-kpi"><span>${{t.mSireDist}}</span><strong>${{card.dist}}m</strong></div>
            <div class="d-kpi"><span>${{t.mSirePca}}</span><strong>(${{card.pca1}}, ${{card.pca2}})</strong></div>
          </div>
          <div class="pedigree-box">
            <h4>${{t.mSireArchTitle}} ${{card.archetype}}</h4>
            <p style="font-size:12.5px;color:#cbd5e1;margin:0 0 10px 0;">${{t.mSireKidsDesc}}</p>
            <div style="display:flex;gap:8px;flex-wrap:wrap;">${{kidsHtml}}</div>
            <div class="layperson-note">${{t.mLaySire}}</div>
          </div>
        `;
      }} else if (card.type === 'jockey') {{
        const partHtml = (card.partners || []).map(k =>
          `<span class="meta-chip turf" style="cursor:pointer;padding:4px 9px;font-size:11.5px;" onclick="jumpToEntityName('${{encodeURIComponent(k)}}')">🏇 ${{k}} 🔗</span>`
        ).join(' ');
        detailsHtml = `
          <div class="dossier-kpis">
            <div class="d-kpi"><span>${{t.mJockRank}}</span><strong>#${{card.rank}}</strong></div>
            <div class="d-kpi"><span>${{t.mJockWins}}</span><strong>${{card.wins}}</strong></div>
            <div class="d-kpi"><span>${{t.mJockG1}}</span><strong>${{card.g1}} G1</strong></div>
            <div class="d-kpi"><span>${{t.mJockPod}}</span><strong>${{card.podiums}} (${{card.pod_rt}}%)</strong></div>
            <div class="d-kpi"><span>${{t.mJockWinRt}}</span><strong>${{card.win_rt}}%</strong></div>
            <div class="d-kpi"><span>${{t.mJockStarts}}</span><strong>${{card.starts}}</strong></div>
          </div>
          <div class="pedigree-box">
            <h4>${{t.mJockPartTitle}}</h4>
            <div style="display:flex;gap:8px;flex-wrap:wrap;">${{partHtml}}</div>
            <div class="layperson-note">${{t.mLayJock}}</div>
          </div>
        `;
      }} else {{
        detailsHtml = `
          <div class="dossier-kpis">
            <div class="d-kpi"><span>${{t.mAncRank}}</span><strong>#${{card.rank}}</strong></div>
            <div class="d-kpi"><span>${{t.mAncInb}}</span><strong>${{card.inbred_horses.toLocaleString()}}</strong></div>
            <div class="d-kpi"><span>${{t.mAncWins}}</span><strong>${{card.graded_wins.toLocaleString()}}</strong></div>
            <div class="d-kpi"><span>${{t.mAncRar}}</span><strong>${{card.rarity}} (OVR ${{card.ovr}})</strong></div>
          </div>
          <div class="pedigree-box">
            <h4>${{t.mAncDagTitle}}</h4>
            <p style="font-size:12.5px;color:#cbd5e1;margin:0;line-height:1.5;">${{t.mAncDagDesc(card.inbred_horses.toLocaleString(), card.graded_wins.toLocaleString())}}</p>
          </div>
        `;
      }}

      content.innerHTML = `
        <div class="dossier-header">
          <div class="crest-avatar" style="background:${{grad}};width:64px;height:64px;font-size:32px;">${{icon}}</div>
          <div class="dossier-title">
            <h2>${{card.name}} <span style="font-size:16px;color:#38bdf8;font-weight:700;">${{card.ja ? '• ' + card.ja : ''}}</span></h2>
            <p><span class="rarity-tag ${{card.rarity}}">${{card.rarity}}</span> • <b>OVR ${{card.ovr}}</b> • ${{card.elem || card.archetype || t.chip5Gen}}</p>
          </div>
        </div>
        <div class="modal-grid">
          <div>${{detailsHtml}}</div>
          <div class="modal-radar-box">
            <div id="modalRadarChart"></div>
            <button class="duel-btn" onclick="startDuelMode('${{card.id}}')">${{t.duelBtn}}</button>
          </div>
        </div>
      `;

      modal.classList.add('open');
      renderModalRadar([{{ name: card.name, value: card.stats, color: '#38bdf8' }}], radarAxes);
    }}

    function openDuelModal(c1, c2) {{
      activeModalState = {{ mode: 'duel', c1: c1, c2: c2 }};
      const t = I18N[currentLang];
      const modal = document.getElementById('cardModal');
      const content = document.getElementById('modalContent');
      const axes = getAxesForType(c1.type, t);

      const rowsHtml = axes.map((axName, i) => {{
        const v1 = c1.stats[i];
        const v2 = c2.stats[i];
        const w1 = v1 >= v2 ? 'color:#fbbf24;font-weight:900;' : 'color:#94a3b8;';
        const w2 = v2 >= v1 ? 'color:#22d3ee;font-weight:900;' : 'color:#94a3b8;';
        return `<div style="display:grid;grid-template-columns:1fr 1.3fr 1fr;align-items:center;padding:8px 10px;border-bottom:1px solid #1e293b;font-size:13px;">
          <div style="text-align:left;${{w1}}">${{v1}} ${{v1 > v2 ? '🏆' : ''}}</div>
          <div style="text-align:center;color:#cbd5e1;font-weight:700;">${{axName}}</div>
          <div style="text-align:right;${{w2}}">${{v2 > v1 ? '🏆' : ''}} ${{v2}}</div>
        </div>`;
      }}).join('');

      content.innerHTML = `
        <div class="duel-header">
          <div>
            <h2 style="margin:0;font-size:20px;color:#fbbf24;">⚔️ ${{c1.name}} (OVR ${{c1.ovr}})</h2>
            <p style="margin:2px 0 0 0;color:#94a3b8;font-size:12px;">Rank #${{c1.rank}} • ${{c1.rarity}} ${{c1.ja ? '• ' + c1.ja : ''}}</p>
          </div>
          <div style="font-size:22px;font-weight:900;color:#f43f5e;">VS</div>
          <div>
            <h2 style="margin:0;font-size:20px;color:#22d3ee;">${{c2.name}} (OVR ${{c2.ovr}}) ⚔️</h2>
            <p style="margin:2px 0 0 0;color:#94a3b8;font-size:12px;">Rank #${{c2.rank}} • ${{c2.rarity}} ${{c2.ja ? '• ' + c2.ja : ''}}</p>
          </div>
        </div>
        <div class="modal-grid">
          <div class="pedigree-box">
            <h4>${{t.duelAttrHeader}}</h4>
            ${{rowsHtml}}
          </div>
          <div class="modal-radar-box">
            <div id="modalRadarChart"></div>
          </div>
        </div>
      `;

      modal.classList.add('open');
      renderModalRadar([
        {{ name: c1.name, value: c1.stats, color: '#fbbf24' }},
        {{ name: c2.name, value: c2.stats, color: '#22d3ee' }}
      ], axes);
    }}

    function renderModalRadar(seriesItems, axesLabels) {{
      setTimeout(() => {{
        const el = document.getElementById('modalRadarChart');
        if (!el) return;
        if (typeof echarts === 'undefined') {{
          setTimeout(() => renderModalRadar(seriesItems, axesLabels), 60);
          return;
        }}
        if (modalChartInstance) modalChartInstance.dispose();
        modalChartInstance = echarts.init(el, 'dark');
        const rSize = window.innerWidth < 520 ? '52%' : '62%';
        modalChartInstance.setOption({{
          backgroundColor: 'transparent',
          tooltip: {{ trigger: 'item' }},
          legend: {{ bottom: 0 }},
          radar: {{
            center: ['50%', '45%'],
            radius: rSize,
            indicator: axesLabels.map(a => ({{ name: a, max: 100 }})),
            axisName: {{ color: '#e2e8f0', fontSize: window.innerWidth < 520 ? 9.5 : 11, fontWeight: 'bold' }}
          }},
          series: [{{
            type: 'radar',
            data: seriesItems.map(s => ({{
              name: s.name,
              value: s.value,
              itemStyle: {{ color: s.color }},
              lineStyle: {{ width: 2.5 }},
              areaStyle: {{ opacity: 0.22 }}
            }}))
          }}]
        }});
      }}, 40);
    }}

    window.addEventListener('resize', () => {{
      if (modalChartInstance) modalChartInstance.resize();
    }});

    function closeModal() {{
      document.getElementById('cardModal').classList.remove('open');
      activeModalState = null;
    }}

    window.addEventListener('keydown', e => {{
      if (e.key === 'Escape') closeModal();
    }});

    // Check URL parameter ?lang=pt|en|ja on boot (BUG-15 fix)
    const urlLang = new URLSearchParams(window.location.search).get('lang');
    if (urlLang && I18N[urlLang]) {{
      setLanguage(urlLang);
    }} else {{
      applyFilters();
    }}
  </script>
</body>
</html>
"""
    out_path = os.path.join(DOCS_DIR, "jra_tcg_arena.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[TCG Builder v2.0] Salvo com sucesso: {out_path} ({len(horse_cards)} cavalos, {len(sire_cards)} garanhões, {len(j_cards)} jóqueis, {len(ancestor_cards)} ancestrais)")


def main():
    h, s, j, a = build_tcg_dataset()
    generate_html(h, s, j, a)


if __name__ == "__main__":
    main()
