"""
Geração de Visualizações Avançadas de Ciência dos Dados (Estilo Apache Superset 6.1 & DataViz Project)
Baseado na aula de Visualização de Dados (Prof. Higor Alexandre Duarte Mascarenhas - CEFET-MG).

Gera 4 painéis científicos de alta resolução (300 DPI) em docs/assets/ usando os CSVs traduzidos:
  1. superset_alluvial_sankey_flow.png  : Diagrama de Fluxo Aluvial / Sankey Multicamadas (Sire -> Surface -> Distance -> Grade)
  2. superset_radar_and_sunburst.png    : Radar Chart Hexagonal (Lendas vs Diamante Injustiçado) + Sunburst Hierárquico dos Hipódromos
  3. superset_streamgraph_dynasties.png : Streamgraph / Evolução Temporal das Dinastias Genéticas (2002–2025)
  4. superset_raincloud_and_parallel.png: Split-Violin Biométrico (Massa Corporal x Distância x Piso) + Coordenadas Paralelas (Clusters)

Também gera um Dashboard HTML Interativo standalone com Apache ECharts (motor do Apache Superset 6.1)
em docs/superset_interactive_dashboard.html.
"""

import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.path import Path
import seaborn as sns

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(BASE_DIR)

CSV_EN_DIR = os.path.join(BASE_DIR, "data", "csv_en")
ANALYSIS_DIR = os.path.join(BASE_DIR, "data", "analysis")
ASSETS_DIR = os.path.join(BASE_DIR, "docs", "assets")
os.makedirs(ASSETS_DIR, exist_ok=True)

plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["axes.edgecolor"] = "#cbd5e1"
plt.rcParams["axes.linewidth"] = 0.9


def load_merged_data():
    races = pd.read_csv(os.path.join(CSV_EN_DIR, "races.csv"), low_memory=False)
    entries = pd.read_csv(os.path.join(CSV_EN_DIR, "race_entries.csv"), low_memory=False)
    horses = pd.read_csv(os.path.join(CSV_EN_DIR, "horses.csv"), low_memory=False)
    pedigree = pd.read_csv(os.path.join(CSV_EN_DIR, "pedigree.csv"), low_memory=False)
    pr_df = pd.read_csv(os.path.join(ANALYSIS_DIR, "pagerank_full_ranking.csv"), low_memory=False)
    clusters_df = pd.read_csv(os.path.join(ANALYSIS_DIR, "ml_sire_clusters_pca.csv"), low_memory=False)

    df = entries.merge(
        races[["race_id", "year", "grade", "grade_weight", "surface", "distance", "track", "num_runners"]],
        on="race_id",
        how="left",
    ).merge(
        pedigree[["horse_name", "sire_name", "dam_name", "dam_sire_name"]].drop_duplicates(subset=["horse_name"]),
        on="horse_name",
        how="left",
    )

    df["position_num"] = pd.to_numeric(df["position"], errors="coerce")
    df["distance_num"] = pd.to_numeric(df["distance"], errors="coerce")
    df["horse_mass_kg"] = df["horse_weight"].astype(str).str.extract(r"^(\d{3})")[0].astype(float)

    def dist_cat(d):
        if pd.isna(d):
            return "3. Intermediate (1800-2200m)"
        if d <= 1400:
            return "1. Sprint (<=1400m)"
        if d <= 1600:
            return "2. Mile (1600m)"
        if d <= 2200:
            return "3. Intermediate (1800-2200m)"
        return "4. Long (>=2400m)"

    df["distance_category"] = df["distance_num"].apply(dist_cat)
    return df, races, horses, pr_df, clusters_df


# =====================================================================
# 1. ALLUVIAL / SANKEY MULTI-STAGE FLOW DIAGRAM
# =====================================================================
def draw_bezier_ribbon(ax, x0, y0_bot, y0_top, x1, y1_bot, y1_top, color, alpha=0.52):
    xm = 0.5 * (x0 + x1)
    verts = [
        (x0, y0_bot),
        (xm, y0_bot),
        (xm, y1_bot),
        (x1, y1_bot),
        (x1, y1_top),
        (xm, y1_top),
        (xm, y0_top),
        (x0, y0_top),
        (x0, y0_bot),
    ]
    codes = [
        Path.MOVETO,
        Path.CURVE4,
        Path.CURVE4,
        Path.CURVE4,
        Path.LINETO,
        Path.CURVE4,
        Path.CURVE4,
        Path.CURVE4,
        Path.CLOSEPOLY,
    ]
    patch = patches.PathPatch(Path(verts, codes), facecolor=color, edgecolor="none", alpha=alpha)
    ax.add_patch(patch)


def plot_alluvial_sankey(df):
    top_sires = [
        "Deep Impact",
        "Sunday Silence(USA)",
        "King Kamehameha",
        "Stay Gold",
        "Heart's Cry",
        "Fuji Kiseki",
        "Manhattan Cafe",
        "Sakura Bakushin O",
        "Brian's Time(USA)",
        "Gold Allure",
    ]
    sub = df[df["sire_name"].isin(top_sires) & df["surface"].isin(["Turf", "Dirt"]) & df["grade"].isin(["G1", "G2", "G3"])].copy()

    sire_colors = {
        "Deep Impact": "#7c3aed",
        "Sunday Silence(USA)": "#4f46e5",
        "King Kamehameha": "#2563eb",
        "Stay Gold": "#059669",
        "Heart's Cry": "#10b981",
        "Manhattan Cafe": "#0d9488",
        "Fuji Kiseki": "#0284c7",
        "Sakura Bakushin O": "#38bdf8",
        "Brian's Time(USA)": "#d97706",
        "Gold Allure": "#ea580c",
    }
    surf_colors = {"Turf": "#16a34a", "Dirt": "#d97706"}
    dist_colors = {
        "1. Sprint (<=1400m)": "#0284c7",
        "2. Mile (1600m)": "#2563eb",
        "3. Intermediate (1800-2200m)": "#7c3aed",
        "4. Long (>=2400m)": "#059669",
    }
    grade_colors = {"G1": "#eab308", "G2": "#94a3b8", "G3": "#b45309"}

    fig, ax = plt.subplots(figsize=(16, 8.5), dpi=300)
    ax.set_xlim(-0.25, 3.25)
    ax.set_ylim(-0.06, 1.06)
    ax.axis("off")

    stages = ["sire_name", "surface", "distance_category", "grade"]
    stage_titles = [
        "1. Paternal Lineage (Top 10 Sires)",
        "2. Track Surface",
        "3. Distance Regime",
        "4. Graded Tier",
    ]
    stage_orders = [
        top_sires,
        ["Turf", "Dirt"],
        ["1. Sprint (<=1400m)", "2. Mile (1600m)", "3. Intermediate (1800-2200m)", "4. Long (>=2400m)"],
        ["G1", "G2", "G3"],
    ]
    stage_palettes = [sire_colors, surf_colors, dist_colors, grade_colors]

    total_n = len(sub)
    node_bounds = [{} for _ in range(4)]
    bar_width = 0.11

    # Compute node vertical positions for each stage
    for s_idx, (col, order, pal) in enumerate(zip(stages, stage_orders, stage_palettes)):
        counts = sub[col].value_counts()
        present = [k for k in order if counts.get(k, 0) > 0]
        gap = 0.022 if len(present) > 4 else 0.045
        usable_h = 1.0 - gap * (len(present) - 1)
        y_cursor = 1.0
        for k in present:
            h = (counts[k] / total_n) * usable_h
            y_top = y_cursor
            y_bot = y_cursor - h
            node_bounds[s_idx][k] = {"top": y_top, "bot": y_bot, "h": h, "count": counts[k], "out_cursor": y_top, "in_cursor": y_top}
            rect = patches.FancyBboxPatch(
                (s_idx - bar_width / 2, y_bot),
                bar_width,
                h,
                boxstyle="round,pad=0.003,rounding_size=0.008",
                facecolor=pal.get(k, "#475569"),
                edgecolor="#0f172a",
                linewidth=1.1,
                zorder=5,
            )
            ax.add_patch(rect)

            pct = counts[k] / total_n * 100
            label_clean = k.replace("(USA)", "").replace("1. ", "").replace("2. ", "").replace("3. ", "").replace("4. ", "")
            if s_idx == 0:
                ax.text(s_idx - bar_width / 2 - 0.02, (y_top + y_bot) / 2, f"{label_clean}\n({counts[k]:,} | {pct:.1f}%)",
                        ha="right", va="center", fontsize=9.5, fontweight="bold", color="#0f172a")
            elif s_idx == 3:
                ax.text(s_idx + bar_width / 2 + 0.02, (y_top + y_bot) / 2, f"{label_clean}\n({counts[k]:,} | {pct:.1f}%)",
                        ha="left", va="center", fontsize=10, fontweight="bold", color="#0f172a")
            else:
                ax.text(s_idx, (y_top + y_bot) / 2, f"{label_clean}\n({pct:.1f}%)",
                        ha="center", va="center", fontsize=9.2, fontweight="bold", color="#0f172a",
                        bbox=dict(boxstyle="round,pad=0.22", facecolor="white", edgecolor="#cbd5e1", alpha=0.92), zorder=10)
            y_cursor = y_bot - gap

        ax.text(s_idx, 1.035, stage_titles[s_idx], ha="center", va="bottom", fontsize=11.5, fontweight="bold", color="#1e293b")

    # Draw Bezier ribbons between consecutive stages
    for s_idx in range(3):
        c0, c1 = stages[s_idx], stages[s_idx + 1]
        o0, o1 = stage_orders[s_idx], stage_orders[s_idx + 1]
        pal0 = stage_palettes[s_idx]
        pair_counts = sub.groupby([c0, c1]).size()
        for k0 in o0:
            if k0 not in node_bounds[s_idx]:
                continue
            for k1 in o1:
                if k1 not in node_bounds[s_idx + 1]:
                    continue
                cnt = pair_counts.get((k0, k1), 0)
                if cnt <= 0:
                    continue
                h0 = (cnt / node_bounds[s_idx][k0]["count"]) * node_bounds[s_idx][k0]["h"]
                h1 = (cnt / node_bounds[s_idx + 1][k1]["count"]) * node_bounds[s_idx + 1][k1]["h"]

                y0_top = node_bounds[s_idx][k0]["out_cursor"]
                y0_bot = y0_top - h0
                node_bounds[s_idx][k0]["out_cursor"] = y0_bot

                y1_top = node_bounds[s_idx + 1][k1]["in_cursor"]
                y1_bot = y1_top - h1
                node_bounds[s_idx + 1][k1]["in_cursor"] = y1_bot

                draw_bezier_ribbon(
                    ax,
                    s_idx + bar_width / 2,
                    y0_bot,
                    y0_top,
                    (s_idx + 1) - bar_width / 2,
                    y1_bot,
                    y1_top,
                    color=pal0.get(k0, "#64748b"),
                    alpha=0.45,
                )

    plt.suptitle(
        "Multi-Stage Alluvial Sankey Diagram — Genetic Flow from Sire Lineage to Track Surface, Distance & Grade",
        fontsize=14.5,
        fontweight="bold",
        y=0.98,
        color="#0f172a",
    )
    plt.figtext(
        0.5,
        0.015,
        f"N = {total_n:,} Graded Race Entries across Top 10 Paternal Sires (JRA 2002–2025) • Notice Gold Allure/Brian's Time flowing into Dirt vs. Sakura Bakushin O into Sprint Turf & Deep Impact into Classic G1/G2 Turf",
        ha="center",
        fontsize=9.8,
        color="#475569",
        style="italic",
    )
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    out_path = os.path.join(ASSETS_DIR, "superset_alluvial_sankey_flow.png")
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"[1/4] Salvo: {out_path}")


# =====================================================================
# 2. RADAR / SPIDER CHART (LEGENDS vs UNDERDOG) + HIERARCHICAL SUNBURST
# =====================================================================
def plot_radar_and_sunburst(df, races, pr_df):
    fig = plt.figure(figsize=(16.5, 7.6), dpi=300)

    # --- LEFT: 6-Axis Radar Chart ---
    ax_radar = fig.add_subplot(1, 2, 1, polar=True)
    target_horses = [
        ("Deep Impact", "#7c3aed", "-"),
        ("Gold Ship", "#0284c7", "-"),
        ("Almond Eye", "#e11d48", "-"),
        ("Sounds of Earth (0 Wins, #32 PR)", "#d97706", "--"),
        ("Lord Kanaloa", "#059669", "-"),
    ]

    categories = [
        "PageRank\nPrestige",
        "Graded Win\nRate (%)",
        "Top-3 Podium\nConsistency",
        "Career Earnings\n(Oku-Yen)",
        "Stamina Index\n(Pref. Distance)",
        "G1 Rivalry\nVolume (Starts)",
    ]
    N = len(categories)
    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    angles += angles[:1]

    pr_lookup = pr_df.drop_duplicates(subset=["horse_name"]).set_index("horse_name").to_dict(orient="index")
    horse_avg_dist = df.groupby("horse_name")["distance_num"].mean().to_dict()

    # Reference maxima for 0-100 normalization
    max_pr = pr_df["pagerank_scaled"].max()
    max_earn = pr_df["total_earnings_m_yen"].max()

    ax_radar.set_theta_offset(np.pi / 2)
    ax_radar.set_theta_direction(-1)
    ax_radar.set_xticks(angles[:-1])
    ax_radar.set_xticklabels(categories, fontsize=9.8, fontweight="bold", color="#1e293b")
    ax_radar.set_yticks([20, 40, 60, 80, 100])
    ax_radar.set_yticklabels(["20", "40", "60", "80", "100"], fontsize=8, color="#64748b")
    ax_radar.set_ylim(0, 105)

    for label, color, ls in target_horses:
        raw_name = label.split(" (")[0]
        row = pr_lookup.get(raw_name, {})
        starts = max(1.0, float(row.get("graded_starts", 1.0)))
        wins = float(row.get("graded_wins", 0.0))
        podiums = float(row.get("graded_podiums", 0.0))

        pr_score = min(100.0, (float(row.get("pagerank_scaled", 1.0)) / max_pr) * 100.0)
        win_rate = min(100.0, (wins / starts) * 100.0)
        podium_rate = min(100.0, (podiums / starts) * 100.0)
        earn_score = min(100.0, (float(row.get("total_earnings_m_yen", 0.0)) / max_earn) * 100.0)
        dist_val = float(horse_avg_dist.get(raw_name, 2000.0))
        stamina_score = float(np.clip((dist_val - 1200.0) / (2500.0 - 1200.0) * 100.0, 18.0, 100.0))
        starts_score = min(100.0, (starts / 25.0) * 100.0)

        values = [pr_score, win_rate, podium_rate, earn_score, stamina_score, starts_score]
        values += values[:1]

        ax_radar.plot(angles, values, color=color, linewidth=2.4, linestyle=ls, marker="o", markersize=4, label=label)
        ax_radar.fill(angles, values, color=color, alpha=0.14)

    ax_radar.set_title(
        "Multidimensional Radar Profile — Turf Legends vs. 'Underdog Diamond'",
        fontsize=12.5,
        fontweight="bold",
        pad=26,
        color="#0f172a",
    )
    ax_radar.legend(loc="upper center", bbox_to_anchor=(0.5, -0.13), ncol=2, fontsize=8.8, frameon=True, facecolor="white")

    # --- RIGHT: 3-Ring Hierarchical Sunburst Chart (Surface -> Grade -> Racecourse) ---
    ax_sun = fig.add_subplot(1, 2, 2)
    ax_sun.axis("equal")

    r_clean = races.dropna(subset=["surface", "grade", "track"]).copy()
    r_clean = r_clean[r_clean["surface"].isin(["Turf", "Dirt", "Obstacle"])]

    # Sort hierarchy: Surface -> Grade -> Track
    surf_order = ["Turf", "Dirt", "Obstacle"]
    surf_base_colors = {"Turf": "#16a34a", "Dirt": "#d97706", "Obstacle": "#6366f1"}
    grade_Lightness = {"G1": 0.95, "G2": 0.78, "G3": 0.62}

    ring1_vals, ring1_labels, ring1_colors = [], [], []
    ring2_vals, ring2_labels, ring2_colors = [], [], []
    ring3_vals, ring3_labels, ring3_colors = [], [], []

    import matplotlib.colors as mcolors

    def tint_color(hex_col, factor):
        rgb = np.array(mcolors.to_rgb(hex_col))
        return mcolors.to_hex(np.clip(rgb * factor + (1 - factor) * 0.95, 0, 1))

    total_races = len(r_clean)
    for s in surf_order:
        df_s = r_clean[r_clean["surface"] == s]
        if df_s.empty:
            continue
        ring1_vals.append(len(df_s))
        ring1_labels.append(f"{s}\n({len(df_s)/total_races*100:.1f}%)")
        ring1_colors.append(surf_base_colors[s])

        for g in ["G1", "G2", "G3"]:
            df_sg = df_s[df_s["grade"] == g]
            if df_sg.empty:
                continue
            ring2_vals.append(len(df_sg))
            ring2_labels.append(f"{g}" if len(df_sg) / total_races > 0.025 else "")
            c_g = tint_color(surf_base_colors[s], grade_Lightness[g])
            ring2_colors.append(c_g)

            track_counts = df_sg["track"].value_counts()
            for trk, t_cnt in track_counts.items():
                ring3_vals.append(t_cnt)
                ring3_labels.append(f"{trk} ({t_cnt})" if t_cnt / total_races > 0.022 else "")
                ring3_colors.append(tint_color(c_g, 0.85))

    wedge_props = dict(width=0.26, edgecolor="white", linewidth=1.2)

    ax_sun.pie(
        ring1_vals,
        radius=0.46,
        labels=ring1_labels,
        labeldistance=0.52,
        colors=ring1_colors,
        wedgeprops=dict(width=0.32, edgecolor="white", linewidth=1.5),
        textprops=dict(fontsize=8.5, fontweight="bold", color="#0f172a", ha="center", va="center"),
        startangle=90,
    )
    ax_sun.pie(
        ring2_vals,
        radius=0.74,
        labels=ring2_labels,
        labeldistance=0.81,
        colors=ring2_colors,
        wedgeprops=wedge_props,
        textprops=dict(fontsize=8.2, fontweight="bold", color="#0f172a", ha="center", va="center"),
        startangle=90,
    )
    ax_sun.pie(
        ring3_vals,
        radius=1.02,
        labels=ring3_labels,
        labeldistance=1.08,
        colors=ring3_colors,
        wedgeprops=wedge_props,
        textprops=dict(fontsize=7.8, fontweight="bold", color="#334155"),
        startangle=90,
    )

    ax_sun.set_title(
        "3-Ring Hierarchical Sunburst — Surface → Grade → JRA Racecourse (3,216 Races)",
        fontsize=12.5,
        fontweight="bold",
        pad=24,
        color="#0f172a",
    )

    plt.tight_layout()
    out_path = os.path.join(ASSETS_DIR, "superset_radar_and_sunburst.png")
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"[2/4] Salvo: {out_path}")


# =====================================================================
# 3. STREAMGRAPH / GENERATIONAL SUCCESSION OF SIRE DYNASTIES (2002-2025)
# =====================================================================
def plot_streamgraph_dynasties(df):
    dynasty_sires = [
        "Sunday Silence(USA)",
        "Brian's Time(USA)",
        "Fuji Kiseki",
        "Dance in the Dark",
        "Agnes Tachyon",
        "Manhattan Cafe",
        "King Kamehameha",
        "Stay Gold",
        "Deep Impact",
        "Heart's Cry",
        "Daiwa Major",
        "Lord Kanaloa",
    ]

    pivot = (
        df[df["sire_name"].isin(dynasty_sires)]
        .groupby(["year", "sire_name"])
        .size()
        .unstack(fill_value=0)
        .reindex(columns=dynasty_sires, fill_value=0)
    )
    years = pivot.index.values.astype(int)
    Y = [pivot[col].values.astype(float) for col in dynasty_sires]

    palette = [
        "#1e1b4b",  # Sunday Silence
        "#b45309",  # Brian's Time
        "#0369a1",  # Fuji Kiseki
        "#0f766e",  # Dance in the Dark
        "#0284c7",  # Agnes Tachyon
        "#0d9488",  # Manhattan Cafe
        "#2563eb",  # King Kamehameha
        "#059669",  # Stay Gold
        "#7c3aed",  # Deep Impact
        "#10b981",  # Heart's Cry
        "#38bdf8",  # Daiwa Major
        "#e11d48",  # Lord Kanaloa
    ]

    fig, ax = plt.subplots(figsize=(15.5, 6.8), dpi=300)
    ax.stackplot(
        years,
        Y,
        labels=[s.replace("(USA)", "") for s in dynasty_sires],
        colors=palette,
        baseline="sym",
        alpha=0.88,
        edgecolor="white",
        linewidth=0.7,
    )

    # Annotate key historical epochs
    ax.axvline(2007, color="#334155", linestyle="--", linewidth=1.1, alpha=0.7)
    ax.text(2004.5, ax.get_ylim()[1] * 0.85, "Era I: Sunday Silence\nDirect Offspring Peak", ha="center", fontsize=9.5, fontweight="bold", color="#1e1b4b")

    ax.axvline(2012, color="#334155", linestyle="--", linewidth=1.1, alpha=0.7)
    ax.text(2009.5, ax.get_ylim()[1] * 0.85, "Era II: 1st-Gen Succession\n(Agnes Tachyon / Fuji Kiseki)", ha="center", fontsize=9.5, fontweight="bold", color="#0369a1")

    ax.text(2015.0, ax.get_ylim()[1] * 0.85, "Era III: Deep Impact, King Kamehameha,\nStay Gold & Heart's Cry Hegemony", ha="center", fontsize=10, fontweight="bold", color="#6d28d9")

    ax.set_title(
        "Symmetric Streamgraph — Generational Rise and Succession of the 12 Dominant Sire Dynasties",
        fontsize=13.5,
        fontweight="bold",
        pad=14,
        color="#0f172a",
    )
    ax.set_xlabel("Racing Season (Year)", fontsize=11.5, fontweight="bold")
    ax.set_ylabel("Symmetric Stream Volume (Graded Race Starters)", fontsize=11.5, fontweight="bold")
    ax.set_xticks(range(int(years.min()), int(years.max()) + 1, 1))
    ax.set_xlim(years.min(), years.max())
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.11), ncol=6, fontsize=9.2, frameon=True)
    ax.grid(axis="x", linestyle=":", alpha=0.6)

    plt.tight_layout()
    out_path = os.path.join(ASSETS_DIR, "superset_streamgraph_dynasties.png")
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"[3/4] Salvo: {out_path}")


# =====================================================================
# 4. SPLIT-VIOLIN BIOMETRICS + PARALLEL COORDINATES OF SIRE ARCHETYPES
# =====================================================================
def plot_raincloud_and_parallel(df, clusters_df):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16.5, 6.8), dpi=300, gridspec_kw={"width_ratios": [1.1, 1.15]})

    # --- LEFT: Split-Violin Biometric Mass Distribution (Turf vs Dirt across Distance Regimes) ---
    bio = df[
        df["surface"].isin(["Turf", "Dirt"])
        & df["horse_mass_kg"].between(400, 560)
    ].copy()

    order_dist = [
        "1. Sprint (<=1400m)",
        "2. Mile (1600m)",
        "3. Intermediate (1800-2200m)",
        "4. Long (>=2400m)",
    ]

    sns.violinplot(
        data=bio,
        x="distance_category",
        y="horse_mass_kg",
        hue="surface",
        order=order_dist,
        hue_order=["Turf", "Dirt"],
        split=True,
        inner="quart",
        palette={"Turf": "#10b981", "Dirt": "#f59e0b"},
        cut=0,
        linewidth=1.2,
        ax=ax1,
    )

    # Annotate means
    means = bio.groupby(["distance_category", "surface"])["horse_mass_kg"].mean().unstack()
    for idx, dcat in enumerate(order_dist):
        if dcat in means.index:
            m_t = means.loc[dcat, "Turf"]
            m_d = means.loc[dcat, "Dirt"]
            if pd.notna(m_t):
                ax1.text(idx - 0.16, m_t - 18, f"Turf\n{m_t:.1f}kg", ha="center", va="top", fontsize=8.2, fontweight="bold", color="#065f46",
                         bbox=dict(boxstyle="round,pad=0.18", facecolor="white", alpha=0.85, edgecolor="#10b981"))
            if pd.notna(m_d):
                ax1.text(idx + 0.16, m_d + 16, f"Dirt\n{m_d:.1f}kg", ha="center", va="bottom", fontsize=8.2, fontweight="bold", color="#92400e",
                         bbox=dict(boxstyle="round,pad=0.18", facecolor="white", alpha=0.85, edgecolor="#f59e0b"))

    ax1.set_title(
        "Split-Violin Biometrics — Equine Body Mass (kg) by Distance & Surface",
        fontsize=12.2,
        fontweight="bold",
        color="#0f172a",
    )
    ax1.set_xlabel("Race Distance Regime", fontsize=11, fontweight="bold")
    ax1.set_ylabel("Equine Body Weight at Race Day (kg)", fontsize=11, fontweight="bold")
    ax1.set_xticks(range(4))
    ax1.set_xticklabels(["Sprint\n(<=1400m)", "Mile\n(1600m)", "Intermediate\n(1800-2200m)", "Long\n(>=2400m)"], fontsize=9.8)
    ax1.legend(title="Surface", loc="upper right", frameon=True)

    # --- RIGHT: Parallel Coordinates Plot of the 4 K-Means++ Sire Archetypes ---
    p_cols = ["turf_share_pct", "avg_distance_m", "win_rate_pct", "podium_rate_pct", "g1_win_share_pct", "mean_progeny_pagerank"]
    p_labels = ["Turf Share\n(%)", "Pref. Distance\n(m)", "Win Rate\n(%)", "Top-3 Podium\nRate (%)", "G1 Victory\nShare (%)", "Offspring\nPageRank"]

    c_df = clusters_df.dropna(subset=p_cols).copy()
    # Min-Max normalize each axis to [0, 1] for parallel coordinates
    norm_df = c_df.copy()
    for col in p_cols:
        cmin, cmax = c_df[col].min(), c_df[col].max()
        norm_df[col] = (c_df[col] - cmin) / (cmax - cmin + 1e-9)

    palette_clusters = {
        "Cluster A: Dirt & Sand Power Specialists": "#d97706",
        "Cluster B: Speed & Mile Turf Sires": "#0284c7",
        "Cluster C: Elite Classic & G1 Turf Dynasties": "#7c3aed",
        "Cluster D: Classic Stayers & Long-Distance Sires": "#059669",
    }

    x_axes = np.arange(len(p_cols))
    # Plot individual sire lines
    for _, row in norm_df.iterrows():
        arch = row["cluster_archetype"]
        vals = [row[c] for c in p_cols]
        ax2.plot(x_axes, vals, color=palette_clusters.get(arch, "#64748b"), alpha=0.24, linewidth=1.1)

    # Plot bold cluster centroid lines
    for arch, grp in norm_df.groupby("cluster_archetype"):
        mean_vals = [grp[c].mean() for c in p_cols]
        ax2.plot(x_axes, mean_vals, color=palette_clusters.get(arch, "#0f172a"), alpha=0.98, linewidth=3.2, marker="o", markersize=6, label=arch)

    for x in x_axes:
        ax2.axvline(x, color="#475569", linestyle="-", linewidth=1.0, alpha=0.6)

    ax2.set_xticks(x_axes)
    ax2.set_xticklabels(p_labels, fontsize=9.5, fontweight="bold")
    ax2.set_yticks([0.0, 0.25, 0.5, 0.75, 1.0])
    ax2.set_yticklabels(["Min (0%)", "25%", "Median (50%)", "75%", "Max (100%)"], fontsize=8.5)
    ax2.set_ylim(-0.05, 1.08)
    ax2.set_title(
        "Parallel Coordinates — Multidimensional Signature of the 4 Sire Archetypes",
        fontsize=12.2,
        fontweight="bold",
        color="#0f172a",
    )
    ax2.legend(loc="upper left", fontsize=8.3, frameon=True, facecolor="white", framealpha=0.92)

    plt.tight_layout()
    out_path = os.path.join(ASSETS_DIR, "superset_raincloud_and_parallel.png")
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"[4/4] Salvo: {out_path}")


# =====================================================================
# 5. INTERACTIVE APACHE SUPERSET 6.1 / ECHARTS 12-CHART EXECUTIVE DASHBOARD
# =====================================================================
def generate_superset_html_dashboard(df, races, pr_df, clusters_df):
    inbreed_df = pd.read_csv(os.path.join(ANALYSIS_DIR, "top_inbreeding_ancestors.csv"), low_memory=False)
    feat_df = pd.read_csv(os.path.join(ANALYSIS_DIR, "ml_feature_importance.csv"), low_memory=False)

    # 1. Multi-stage 4-level Sankey data: Top 10 Sires -> Surface -> Distance -> Grade
    top10_sires = [
        "Deep Impact", "Sunday Silence(USA)", "King Kamehameha", "Stay Gold",
        "Heart's Cry", "Fuji Kiseki", "Manhattan Cafe", "Sakura Bakushin O",
        "Brian's Time(USA)", "Gold Allure"
    ]
    sub_sankey = df[
        df["sire_name"].isin(top10_sires)
        & df["surface"].isin(["Turf", "Dirt"])
        & df["grade"].isin(["G1", "G2", "G3"])
    ].copy()

    sankey_links = []
    sankey_nodes_set = set()
    for (s, surf), cnt in sub_sankey.groupby(["sire_name", "surface"]).size().items():
        if cnt >= 3:
            src, tgt = f"Sire: {s.replace('(USA)', '')}", f"Surface: {surf}"
            sankey_links.append({"source": src, "target": tgt, "value": int(cnt)})
            sankey_nodes_set.update([src, tgt])
    for (surf, dcat), cnt in sub_sankey.groupby(["surface", "distance_category"]).size().items():
        if cnt >= 3:
            src, tgt = f"Surface: {surf}", dcat
            sankey_links.append({"source": src, "target": tgt, "value": int(cnt)})
            sankey_nodes_set.update([src, tgt])
    for (dcat, grd), cnt in sub_sankey.groupby(["distance_category", "grade"]).size().items():
        if cnt >= 3:
            src, tgt = dcat, f"Grade: {grd}"
            sankey_links.append({"source": src, "target": tgt, "value": int(cnt)})
            sankey_nodes_set.update([src, tgt])
    sankey_nodes = [{"name": n} for n in sorted(sankey_nodes_set)]

    # 2. PageRank Scatter Quadrant (Top 140 Horses + Underdog Diamonds + Silver Collectors)
    top_pr_sub = pr_df.head(140).copy()
    g1_champs, silver_cols, underdogs = [], [], []
    for _, r in top_pr_sub.iterrows():
        item = {
            "name": str(r["horse_name"]),
            "rank": int(r["pagerank_rank"]),
            "pr": round(float(r["pagerank_scaled"]), 2),
            "wins": int(r["graded_wins"]),
            "g1": int(r["g1_wins"]),
            "podiums": int(r["graded_podiums"]),
            "starts": int(r["graded_starts"]),
            "earn": round(float(r["total_earnings_m_yen"]), 1),
            "sire": str(r["sire"]),
            "fx": round(float(r["inbreeding_fx_pct"]), 2),
            "value": [int(r["graded_wins"]), round(float(r["pagerank_scaled"]), 2), round(float(r["total_earnings_m_yen"]), 1), str(r["horse_name"]), int(r["pagerank_rank"])]
        }
        if int(r["graded_wins"]) == 0:
            underdogs.append(item)
        elif int(r["g1_wins"]) == 0:
            silver_cols.append(item)
        else:
            g1_champs.append(item)

    # 3. Sunburst Tree: Surface -> Grade -> Racecourse
    r_clean = races.dropna(subset=["surface", "grade", "track"]).copy()
    surf_colors_hex = {"Turf": "#10b981", "Dirt": "#f59e0b", "Obstacle": "#6366f1"}
    sunburst_tree = []
    for s in ["Turf", "Dirt", "Obstacle"]:
        df_s = r_clean[r_clean["surface"] == s]
        if df_s.empty:
            continue
        g_children = []
        for g in ["G1", "G2", "G3"]:
            df_sg = df_s[df_s["grade"] == g]
            if df_sg.empty:
                continue
            t_children = [
                {"name": trk, "value": int(cnt)}
                for trk, cnt in df_sg["track"].value_counts().items()
            ]
            g_children.append({"name": f"{s} {g}", "children": t_children})
        sunburst_tree.append({
            "name": s,
            "itemStyle": {"color": surf_colors_hex.get(s, "#38bdf8")},
            "children": g_children
        })

    # 4. Radar Profiles (8 iconic horses)
    pr_lookup = pr_df.drop_duplicates(subset=["horse_name"]).set_index("horse_name").to_dict(orient="index")
    horse_avg_dist = df.groupby("horse_name")["distance_num"].mean().to_dict()
    max_pr = float(pr_df["pagerank_scaled"].max())
    max_earn = float(pr_df["total_earnings_m_yen"].max())
    radar_horses = [
        ("Kitasan Black (#1 PR)", "Kitasan Black", "#38bdf8"),
        ("Deep Impact", "Deep Impact", "#a855f7"),
        ("Gold Ship", "Gold Ship", "#0284c7"),
        ("Almond Eye (#1 Earnings)", "Almond Eye", "#f43f5e"),
        ("Vodka", "Vodka", "#ec4899"),
        ("Orfevre", "Orfevre", "#eab308"),
        ("Lord Kanaloa (Sprint King)", "Lord Kanaloa", "#10b981"),
        ("Sounds of Earth (0 Wins, #32 PR)", "Sounds of Earth", "#f97316"),
    ]
    radar_series_data = []
    for label, hname, col in radar_horses:
        row = pr_lookup.get(hname, {})
        starts = max(1.0, float(row.get("graded_starts", 1.0)))
        wins = float(row.get("graded_wins", 0.0))
        podiums = float(row.get("graded_podiums", 0.0))
        pr_sc = round(min(100.0, (float(row.get("pagerank_scaled", 1.0)) / max_pr) * 100.0), 1)
        win_rt = round(min(100.0, (wins / starts) * 100.0), 1)
        pod_rt = round(min(100.0, (podiums / starts) * 100.0), 1)
        earn_sc = round(min(100.0, (float(row.get("total_earnings_m_yen", 0.0)) / max_earn) * 100.0), 1)
        d_val = float(horse_avg_dist.get(hname, 2000.0))
        stam_sc = round(float(np.clip((d_val - 1200.0) / (2500.0 - 1200.0) * 100.0, 15.0, 100.0)), 1)
        riv_sc = round(min(100.0, (starts / 25.0) * 100.0), 1)
        radar_series_data.append({
            "name": label,
            "value": [pr_sc, win_rt, pod_rt, earn_sc, stam_sc, riv_sc],
            "itemStyle": {"color": col},
            "lineStyle": {"width": 2.5, "type": "dashed" if wins == 0 else "solid"},
            "areaStyle": {"opacity": 0.14}
        })

    # 5. K-Means++ PCA 2D Clusters & 6. Parallel Coordinates (106 Sires)
    pca_series_map = {}
    parallel_data = []
    for _, r in clusters_df.iterrows():
        arch = str(r["cluster_archetype"])
        pca_series_map.setdefault(arch, []).append({
            "name": str(r["sire"]),
            "value": [
                round(float(r["pca_1"]), 3),
                round(float(r["pca_2"]), 3),
                int(r["total_entries"]),
                str(r["sire"]),
                round(float(r["turf_share_pct"]), 1),
                round(float(r["avg_distance_m"]), 0),
                round(float(r["win_rate_pct"]), 2),
                int(r["g1_wins"]),
                round(float(r["mean_progeny_pagerank"]), 2)
            ]
        })
        parallel_data.append({
            "name": str(r["sire"]),
            "archetype": arch,
            "value": [
                round(float(r["turf_share_pct"]), 1),
                round(float(r["avg_distance_m"]), 0),
                round(float(r["win_rate_pct"]), 2),
                round(float(r["podium_rate_pct"]), 2),
                round(float(r["g1_win_share_pct"]), 2),
                round(float(r["mean_progeny_pagerank"]), 2),
                str(r["sire"])
            ]
        })

    # 7. Evolutionary Stream / Stacked Area (2002-2018)
    dynasty_sires = [
        "Sunday Silence(USA)", "Brian's Time(USA)", "Fuji Kiseki", "Dance in the Dark",
        "Agnes Tachyon", "Manhattan Cafe", "King Kamehameha", "Stay Gold",
        "Deep Impact", "Heart's Cry", "Daiwa Major", "Lord Kanaloa"
    ]
    piv_dyn = (
        df[df["sire_name"].isin(dynasty_sires)]
        .groupby(["year", "sire_name"])
        .size()
        .unstack(fill_value=0)
        .reindex(columns=dynasty_sires, fill_value=0)
    )
    stream_years = [int(y) for y in piv_dyn.index.tolist()]
    stream_series = [
        {
            "name": s.replace("(USA)", ""),
            "type": "line",
            "stack": "Total",
            "smooth": True,
            "areaStyle": {"opacity": 0.78},
            "emphasis": {"focus": "series"},
            "data": [int(v) for v in piv_dyn[s].tolist()]
        }
        for s in dynasty_sires
    ]

    # 8. Genetic Distance Specialization Heatmap (Top 12 Sires x 4 Distance Categories)
    top12_heat = [
        "Sakura Bakushin O", "Fuji Kiseki", "Daiwa Major", "Brian's Time(USA)",
        "King Kamehameha", "Sunday Silence(USA)", "Deep Impact", "Manhattan Cafe",
        "Stay Gold", "Heart's Cry", "Dance in the Dark", "Gold Allure"
    ]
    dist_cats = [
        "1. Sprint (<=1400m)", "2. Mile (1600m)",
        "3. Intermediate (1800-2200m)", "4. Long (>=2400m)"
    ]
    ct_heat = pd.crosstab(
        df[df["sire_name"].isin(top12_heat)]["sire_name"],
        df[df["sire_name"].isin(top12_heat)]["distance_category"],
        normalize="index"
    ) * 100.0
    ct_heat = ct_heat.reindex(index=top12_heat, columns=dist_cats, fill_value=0.0)
    heatmap_cells = []
    for y_i, s_name in enumerate(top12_heat):
        for x_i, d_name in enumerate(dist_cats):
            heatmap_cells.append([x_i, y_i, round(float(ct_heat.loc[s_name, d_name]), 1)])
    heatmap_sire_labels = [s.replace("(USA)", "") for s in top12_heat]
    heatmap_dist_labels = ["Sprint (<=1400m)", "Mile (1600m)", "Intermediate (1800-2200m)", "Long (>=2400m)"]

    # 9. Founding Ancestors & Wright's Inbreeding F_X Treemap
    treemap_ancestors = []
    for _, r in inbreed_df.head(18).iterrows():
        treemap_ancestors.append({
            "name": f"{r['common_ancestor']}\n({int(r['inbred_horses_count']):,} inbred horses | {int(r['graded_wins_by_inbred_progeny']):,} wins)",
            "value": int(r["inbred_horses_count"]),
            "inbred_cases": int(r["inbred_horses_count"]),
            "graded_wins": int(r["graded_wins_by_inbred_progeny"]),
        })

    # 10. Top 15 Jockeys Synergy (Wins, G1 Wins, Top-3 Podium Rate %)
    df["is_win"] = (df["position_num"] == 1).astype(int)
    df["is_g1_win"] = ((df["position_num"] == 1) & (df["grade"] == "G1")).astype(int)
    df["is_top3"] = (df["position_num"] <= 3).astype(int)
    j_stats = (
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
    j_stats = j_stats[j_stats["starts"] >= 50].sort_values(by="wins", ascending=False).head(15)
    j_stats["podium_rate"] = (j_stats["podiums"] / j_stats["starts"] * 100.0).round(1)
    jockey_json = j_stats.to_dict(orient="records")

    # 11. Equine Biometrics (Body Mass kg & Mean Speed km/h across Surface & Distance)
    def parse_time_sec(t_str):
        t_str = str(t_str).strip()
        if ":" in t_str:
            parts = t_str.split(":")
            try:
                return float(parts[0]) * 60.0 + float(parts[1])
            except Exception:
                return np.nan
        return np.nan

    df["time_sec"] = df["finish_time"].apply(parse_time_sec)
    df["speed_kmh"] = np.where(
        (df["time_sec"] > 30) & (df["distance_num"] > 800),
        (df["distance_num"] / df["time_sec"]) * 3.6,
        np.nan,
    )
    bio_sub = df[df["surface"].isin(["Turf", "Dirt"]) & df["horse_mass_kg"].between(400, 560)].copy()
    bio_agg = (
        bio_sub.groupby(["distance_category", "surface"])
        .agg(mean_kg=("horse_mass_kg", "mean"), mean_speed=("speed_kmh", "mean"))
        .unstack()
    )
    bio_turf_kg = [round(float(bio_agg.loc[d, ("mean_kg", "Turf")]), 1) for d in dist_cats]
    bio_dirt_kg = [round(float(bio_agg.loc[d, ("mean_kg", "Dirt")]), 1) for d in dist_cats]
    bio_turf_spd = [round(float(bio_agg.loc[d, ("mean_speed", "Turf")]), 2) for d in dist_cats]
    bio_dirt_spd = [round(float(bio_agg.loc[d, ("mean_speed", "Dirt")]), 2) for d in dist_cats]

    # 12. Random Forest Feature Importance
    feat_top12 = feat_df.head(12).iloc[::-1]
    rf_features = feat_top12["feature"].tolist()
    rf_importances = [round(float(v), 2) for v in feat_top12["gini_importance_pct"].tolist()]

    i18n = {
        "pt": {
            "filename": "superset_interactive_dashboard.html",
            "lang": "pt-BR",
            "title": "Apache Superset 6.1 (ECharts Engine) — Suíte Analítica JRA & JBIS",
            "subtitle": "CEFET-MG (Campus Divinópolis) • AEDS 2 & Ciência dos Dados • Autor: Arthur De Oliveira Mendonça • Prof. Higor Alexandre Duarte Mascarenhas",
            "badge_charts": "13 Gráficos Interativos",
            "badge_qa": "QA: 100% Validado (0 Erros)",
            "kpi1_t": "Corridas & Participações", "kpi1_s": "100% Cobertura G1, G2 e G3 JRA (2002–2025)",
            "kpi2_t": "Nós do DAG 5 Gerações", "kpi2_s": "8.209 Puro-Sangues • Bijeção BFS Validada",
            "kpi3_t": "Diamante Injustiçado #1", "kpi3_s": "#32/8.135 em PageRank com 0 Vitórias Graded!",
            "kpi4_t": "Especialização Genética (H1)", "kpi4_s": "Chi² = 2237,5 (Distância) & 740,0 (Superfície)",
            "kpi5_t": "Random Forest Out-of-Time", "kpi5_s": "IC 95% [0.711, 0.739] • Zero Data Leakage",
            "kpi6_t": "Patriarca Fundador #1", "kpi6_s": "4.206 Cavalos Endogâmicos • 1.211 Vitórias",
            "sec1_h": "🌊 1. Fluxo Genético Multicamadas & Arquitetura Hierárquica dos Hipódromos",
            "sec1_s": "Passe o mouse sobre as faixas do Sankey ou clique nas fatias do Sunburst para fazer Drill-Down",
            "c1_t": "Chart 1 — Diagrama Sankey Aluvial de 4 Estágios: Linhagem Paterna → Superfície → Regime de Distância → Grau (G1/G2/G3)",
            "c1_d": "Demonstra como as linhagens de Areia (Gold Allure, Brian's Time), Velocidade (Sakura Bakushin O) e Clássicas (Deep Impact, Sunday Silence) se dividem pelos regimes de prova.",
            "c2_t": "Chart 2 — Sunburst Hierárquico de 3 Anéis (Clique em qualquer fatia para Zoom / Drill-Down!)",
            "c2_d": "Anel Interno: Superfície (Turf 81.9%, Dirt 10.7%, Obstacle 7.4%) → Anel Médio: Grau (G1/G2/G3) → Anel Externo: Os 10 Hipódromos da JRA.",
            "c3_t": "Chart 3 — Comparador Radar Hexagonal de 6 Eixos: Lendas G1 vs. 'Diamante Injustiçado' (Sounds of Earth)",
            "c3_d": "Clique nos nomes na legenda inferior para ligar/desligar qualquer cavalo e comparar seus polígonos de atributos (0–100).",
            "sec2_h": "🕸️ 2. Teoria dos Grafos: PageRank Esportivo ('Diamantes Injustiçados') & Endogamia de Wright (F_X)",
            "sec2_s": "Use o scroll do mouse para dar zoom no quadrante de PageRank ou passe o mouse nos blocos do Treemap Genealógico",
            "c4_t": "Chart 4 — PageRank Quadrant Explorer: Campeões G1 vs. Colecionadores de Prata (0 G1) vs. Diamantes Injustiçados (0 Vitórias)",
            "c4_d": "Eixo X = Vitórias Graded | Eixo Y = PageRank Esportivo | Tamanho da Bolha = Premiação (¥M). Veja Sounds of Earth (#32) e Etariou (#43) no eixo Y (0 vitórias)!",
            "c5_t": "Chart 5 — Top 15 Global Sports PageRank vs. Pódios Acumulados (r = 0.8799)",
            "c5_d": "Comparação em duplo eixo entre o escore PageRank (barras roxas) e o total de pódios Top-3 em corridas Graded (linha azul).",
            "c6_t": "Chart 6 — Treemap Genealógico dos Patriarcas Fundadores (504.074 Nós Ancestrais & Coeficiente de Wright F_X)",
            "c6_d": "Área de cada bloco = Cavalos com endogamia (LCA) naquele ancestral. Passe o mouse para ver as vitórias Graded associadas.",
            "sec3_h": "🧬 3. Clusterização K-Means++ PCA 2D, Coordenadas Paralelas com Filtro Ao Vivo & Sucessão de Dinastias",
            "sec3_s": "No Gráfico 8 (Coordenadas Paralelas), clique e arraste verticalmente sobre qualquer eixo para filtrar os garanhões em tempo real!",
            "c7_t": "Chart 7 — Explorador de Bolhas K-Means++ PCA 2D (106 Garanhões — 63.4% de Variância Explicada)",
            "c7_d": "PC1 (44.1%): Eixo Superfície & Distância | PC2 (19.2%): Eixo Taxa de Vitória & Prestígio G1. Tamanho da bolha = Largadas dos filhos.",
            "c8_t": "Chart 8 — Coordenadas Paralelas com Brush Filter Ao Vivo (Arraste o mouse nos eixos verticais para filtrar!)",
            "c8_d": "Assinatura multidimensional dos 106 garanhões nos 6 indicadores zootécnicos. Selecione uma faixa em qualquer eixo para isolar reprodutores!",
            "c9_t": "Chart 9 — Streamgraph / Área Empilhada: Sucessão Geracional das 12 Grandes Dinastias (2002–2018)",
            "c9_d": "Use o controle deslizante inferior para focar em períodos específicos ou passe o mouse para destacar uma linhagem individual.",
            "c10_t": "Chart 10 — Matriz de Especialização Genética por Distância (Chi² = 2237.5, p < 0.0001, V de Cramér = 0.252)",
            "c10_d": "Proporção (%) das largadas dos filhos de cada garanhão em Sprint (<=1400m), Mile (1600m), Intermediate (1800-2200m) e Long (>=2400m).",
            "sec4_h": "🤖 4. Fator Humano (Jóqueis), Biometria Equina (Massa & Velocidade) & Machine Learning Supervisionado",
            "sec4_s": "Resultados da Random Forest (ROC-AUC = 0.7260 no conjunto de teste cronológico 2016–2018) e análise física por superfície",
            "c11_t": "Chart 11 — O Fator Humano: Top 15 Jóqueis por Vitórias Graded, Títulos de G1 e Taxa de Pódio Top-3 (%)",
            "c11_d": "A taxa histórica prévia do jóquei é a variável #1 mais importante da Random Forest (29.8% da Importância de Gini).",
            "c12_t": "Chart 12 — Biometria Equina & Cinemática: Massa Corporal (kg) vs. Velocidade Média (km/h) em Turf e Dirt",
            "c12_d": "Cavalos de Areia (Dirt, ~496 kg) são ~18 kg mais pesados e musculosos que os de Grama (Turf, ~477 kg), enquanto a Grama proporciona velocidades superiores.",
            "c13_t": "Chart 13 — Random Forest Classifier (CART Ensemble): Importância Relativa de Gini (%) — Test ROC-AUC = 0.7260 (95% CI [0.711, 0.739])",
            "c13_d": "Treino: 2002–2013 | Validação: 2014–2015 | Teste Out-of-Time: 2016–2018 (N = 5.889). Zero Data Leakage com janelas históricas estritamente anteriores.",
        },
        "en": {
            "filename": "superset_interactive_dashboard_en.html",
            "lang": "en",
            "title": "Apache Superset 6.1 (ECharts Engine) — JRA & JBIS Executive Analytics Suite",
            "subtitle": "CEFET-MG (Divinópolis Campus) • AEDS 2 & Data Science • Author: Arthur De Oliveira Mendonça • Advisor: Prof. Higor Alexandre Duarte Mascarenhas",
            "badge_charts": "13 Interactive Charts",
            "badge_qa": "QA: 100% Passed (0 Errors)",
            "kpi1_t": "Graded Races & Entries", "kpi1_s": "100% G1, G2 & G3 JRA Coverage (2002–2025)",
            "kpi2_t": "5-Gen Pedigree DAG Nodes", "kpi2_s": "8,209 Thoroughbreds • BFS Bijection Verified",
            "kpi3_t": "Underdog Diamond #1", "kpi3_s": "Rank #32/8,135 PageRank with 0 Graded Wins!",
            "kpi4_t": "Genetic Specialization (H1)", "kpi4_s": "Chi² = 2237.5 (Distance) & 740.0 (Surface)",
            "kpi5_t": "Random Forest Out-of-Time", "kpi5_s": "95% CI [0.711, 0.739] • Zero Data Leakage",
            "kpi6_t": "Top Founding Patriarch", "kpi6_s": "4,206 Inbred Horses • 1,211 Graded Wins",
            "sec1_h": "🌊 1. Multi-Stage Genetic Flow & Hierarchical Racecourse Architecture",
            "sec1_s": "Hover over Sankey ribbons to highlight genetic paths or click any Sunburst sector to Drill-Down",
            "c1_t": "Chart 1 — 4-Stage Alluvial Sankey Diagram: Paternal Sire → Surface → Distance Regime → Graded Tier (G1/G2/G3)",
            "c1_d": "Illustrates how Dirt power sires (Gold Allure, Brian's Time), Sprint specialists (Sakura Bakushin O), and Classic dynasties (Deep Impact, Sunday Silence) channel into race regimes.",
            "c2_t": "Chart 2 — Interactive 3-Ring Hierarchical Sunburst (Click any sector to Zoom / Drill-Down!)",
            "c2_d": "Inner Ring: Surface (Turf 81.9%, Dirt 10.7%, Obstacle 7.4%) → Middle Ring: Grade (G1/G2/G3) → Outer Ring: All 10 JRA Racecourses.",
            "c3_t": "Chart 3 — 6-Axis Multidimensional Radar Comparator: G1 Legends vs. 'Underdog Diamond' (Sounds of Earth)",
            "c3_d": "Click horse names in the bottom legend to toggle polygons and compare normalized 6-dimensional profiles (0–100).",
            "sec2_h": "🕸️ 2. Graph Theory: Sports PageRank ('Underdog Diamonds') & Wright's Inbreeding (F_X)",
            "sec2_s": "Use mouse wheel to zoom into the PageRank quadrant or hover over Founding Patriarch Treemap blocks",
            "c4_t": "Chart 4 — PageRank Quadrant Explorer: G1 Champions vs. Silver Collectors (0 G1) vs. Underdog Diamonds (0 Wins)",
            "c4_d": "X-Axis = Career Graded Wins | Y-Axis = Sports PageRank | Bubble Size = Lifetime Earnings (¥M). Notice Sounds of Earth (#32) & Etariou (#43) on X = 0!",
            "c5_t": "Chart 5 — Top 15 Global Sports PageRank vs. Career Podiums (r = 0.8799)",
            "c5_d": "Dual-axis comparison between Scaled PageRank score (purple bars) and career Top-3 Graded podiums (blue line).",
            "c6_t": "Chart 6 — Genealogical Founding Patriarchs Treemap (504,074 Ancestral Nodes & Wright's Inbreeding LCA)",
            "c6_d": "Block area = Number of inbred horses sharing that common ancestor (LCA). Hover to inspect associated Graded victories.",
            "sec3_h": "🧬 3. K-Means++ 2D PCA Clustering, Live-Filter Parallel Coordinates & Dynasty Streamgraph",
            "sec3_s": "In Chart 8 (Parallel Coordinates), click and drag vertically along any axis to filter stallions in real time!",
            "c7_t": "Chart 7 — K-Means++ 2D PCA Interactive Bubble Cluster Explorer (106 Sires — 63.4% Variance Explained)",
            "c7_d": "PC1 (44.1%): Surface & Distance Axis | PC2 (19.2%): Win Rate & G1 Prestige Axis. Bubble size = Progeny Graded starts.",
            "c8_t": "Chart 8 — Interactive Parallel Coordinates with Live Brush Filter (Drag vertically on any axis to filter!)",
            "c8_d": "Multidimensional signature of all 106 stallions across 6 breeding metrics. Brush any axis range to isolate sires!",
            "c9_t": "Chart 9 — Evolutionary Stacked Area / Streamgraph: Generational Succession of the 12 Dominant Dynasties (2002–2018)",
            "c9_d": "Use the bottom time slider to zoom into specific eras or hover to highlight an individual paternal dynasty.",
            "c10_t": "Chart 10 — Genetic Distance Specialization Matrix (Chi² = 2237.5, p < 0.0001, Cramér's V = 0.252)",
            "c10_d": "Share (%) of progeny starts across Sprint (<=1400m), Mile (1600m), Intermediate (1800-2200m), and Long (>=2400m).",
            "sec4_h": "🤖 4. Human Factor (Jockeys), Equine Biometrics (Body Mass & Speed) & Supervised Machine Learning",
            "sec4_s": "Out-of-time Random Forest results (Test ROC-AUC = 0.7260 on 2016–2018) and physical kinematics by surface",
            "c11_t": "Chart 11 — The Human Factor: Top 15 Jockeys by Graded Wins, G1 Titles & Top-3 Podium Rate (%)",
            "c11_d": "Prior jockey podium rate is the #1 predictive feature in our Random Forest model (29.8% relative Gini importance).",
            "c12_t": "Chart 12 — Equine Biometrics & Kinematics: Body Mass (kg) vs. Mean Speed (km/h) on Turf and Dirt",
            "c12_d": "Dirt runners (~496 kg) are ~18 kg heavier and more muscular than Turf runners (~477 kg), while Turf yields higher cruising speeds.",
            "c13_t": "Chart 13 — Random Forest Classifier (CART Ensemble): Relative Gini Feature Importance (%) — Test ROC-AUC = 0.7260 (95% CI [0.711, 0.739])",
            "c13_d": "Train: 2002–2013 | Validation: 2014–2015 | Out-of-Time Test: 2016–2018 (N = 5,889). Strict zero data leakage with expanding prior windows.",
        },
        "ja": {
            "filename": "superset_interactive_dashboard_ja.html",
            "lang": "ja",
            "title": "Apache Superset 6.1 (ECharts Engine) — JRA重賞 & JBIS 5代血統 統合分析スイート",
            "subtitle": "CEFET-MG（ミナス・ジェライス連邦技術教育センター）• AEDS 2 & データサイエンス • 著者: Arthur De Oliveira Mendonça • 指導教員: Higor Alexandre Duarte Mascarenhas",
            "badge_charts": "13種類のインタラクティブチャート",
            "badge_qa": "QA検証: 100%合格 (エラー0件)",
            "kpi1_t": "重賞レース数 & 出走延べ頭数", "kpi1_s": "JRA G1・G2・G3 完全網羅 (2002–2025年)",
            "kpi2_t": "5代血統DAG 総ノード数", "kpi2_s": "競走馬 8,209頭 • BFS全単射検証済み",
            "kpi3_t": "無冠の名馬 (Underdog #1)", "kpi3_s": "重賞0勝で全体PageRank 第32位 / 8,135頭！",
            "kpi4_t": "血統による馬場・距離適性 (H1)", "kpi4_s": "Chi² = 2237.5 (距離) & 740.0 (馬場)",
            "kpi5_t": "ランダムフォレスト時系列予測", "kpi5_s": "95%信頼区間 [0.711, 0.739] • データリークゼロ",
            "kpi6_t": "最大基礎種牡馬 (LCA)", "kpi6_s": "インブリード個体 4,206頭 • 重賞1,211勝",
            "sec1_h": "🌊 1. 多段階血統フロー & JRA全10競馬場の階層構造",
            "sec1_s": "サンキーのリボンにマウスを重ねると経路が強調され、サンバーストの扇形をクリックするとドリルダウン（拡大）します",
            "c1_t": "Chart 1 — 4段階サンキー・ダイアグラム：種牡馬系統 → 馬場（芝・ダート） → 距離区分 → グレード（G1/G2/G3）",
            "c1_d": "ダート系統（ゴールドアリュール、ブライアンズタイム）、スプリント系統（サクラバクシンオー）、クラシック王道系統（ディープインパクト）の分岐を可視化。",
            "c2_t": "Chart 2 — 3層階層サンバースト（扇形をクリックするとズーム／ドリルダウンします！）",
            "c2_d": "内円：馬場（芝 81.9%、ダート 10.7%、障害 7.4%） → 中円：グレード（G1/G2/G3） → 外円：JRA全10競馬場。",
            "c3_t": "Chart 3 — 6軸多次元レーダーチャート：G1レジェンド vs. 「無冠の名馬」（サウンズオブアース）",
            "c3_d": "下部凡例の馬名をクリックすると表示／非表示を切り替え、6次元能力ポリゴン（0–100）を比較できます。",
            "sec2_h": "🕸️ 2. グラフ理論：競走PageRank（「無冠の名馬」）& ライトの近交係数 (F_X)",
            "sec2_s": "マウスホイールでPageRank散布図をズーム、またはツリーマップのブロックにカーソルを合わせて詳細を表示",
            "c4_t": "Chart 4 — PageRank象限エクスプローラー：G1王者 vs. シルバーコレクター（G1未勝利） vs. 無冠の名馬（重賞0勝）",
            "c4_d": "X軸 = 重賞勝利数 | Y軸 = 競走PageRank | バブルサイズ = 獲得賞金。X=0軸上に位置するサウンズオブアース（32位）とエタリオウ（43位）に注目！",
            "c5_t": "Chart 5 — 競走PageRank トップ15 vs. 重賞3着以内回数（相関係数 r = 0.8799）",
            "c5_d": "PageRankスコア（紫バー）と重賞3着以内好走回数（青ライン）・重賞勝利数（緑破線）の二軸比較。",
            "c6_t": "Chart 6 — 5代血統 基礎種牡馬ツリーマップ（504,074ノード & 共通祖先インブリード分析）",
            "c6_d": "ブロック面積 = その祖先を共通祖先（LCA）として持つインブリード競走馬数（ノーザンダンサーが圧倒的首位）。",
            "sec3_h": "🧬 3. K-Means++ 2次元PCAクラスタリング、ライブフィルタ付き平行座標 & 種牡馬王朝ストリームグラフ",
            "sec3_s": "Chart 8（平行座標）では、任意の縦軸をマウスで上下にドラッグするとリアルタイムで種牡馬をフィルタリングできます！",
            "c7_t": "Chart 7 — K-Means++ 2次元PCA バブルクラスター（主要種牡馬106頭 — 累積寄与率 63.4%）",
            "c7_d": "第1主成分 PC1 (44.1%): 馬場・距離軸 | 第2主成分 PC2 (19.2%): 勝率・G1威信軸。バブルサイズ = 産駒の重賞出走数。",
            "c8_t": "Chart 8 — ライブブラシフィルタ付き平行座標プロット（縦軸をドラッグして種牡馬を絞り込み！）",
            "c8_d": "主要種牡馬106頭の6指標シグネチャ。任意の軸の範囲をドラッグ選択すると該当する種牡馬のみがハイライトされます！",
            "c9_t": "Chart 9 — 進化ストリームグラフ：12大種牡馬王朝の世代交代と覇権推移（2002–2018年）",
            "c9_d": "下部スライダーで年代を絞り込み可能。サンデーサイレンス直仔世代からディープインパクト・キングカメハメハ黄金時代への移行。",
            "c10_t": "Chart 10 — 種牡馬別・距離適性ヒートマップ（Chi² = 2237.5, p < 0.0001, Cramér's V = 0.252）",
            "c10_d": "各主要種牡馬の産駒におけるスプリント（<=1400m）・マイル（1600m）・中距離（1800-2200m）・長距離（>=2400m）出走比率（%）。",
            "sec4_h": "🤖 4. 人的要因（騎手シナジー）、馬体重バイオメトリクス & 教師あり機械学習（Random Forest）",
            "sec4_s": "時系列分割テスト（2016–2018年）におけるランダムフォレスト予測結果（ROC-AUC = 0.7260）および馬場別の馬体重・速度分析",
            "c11_t": "Chart 11 — 人的要因：重賞勝利数トップ15騎手（総重賞勝利・G1勝利・重賞複勝率 %）",
            "c11_d": "騎手の過去重賞複勝率は、ランダムフォレストモデルにおいて最も重要な予測変数（Gini重要度 29.8%）です。",
            "c12_t": "Chart 12 — 馬体重バイオメトリクス & 走破速度：芝 vs. ダートにおける平均馬体重 (kg) と平均速度 (km/h)",
            "c12_d": "ダート出走馬（平均約496 kg）は芝出走馬（約477 kg）より約18 kg大型で筋肉質である一方、巡航速度は芝が上回ります。",
            "c13_t": "Chart 13 — ランダムフォレスト分類器 (CART Ensemble)：Gini特徴量重要度 (%) — テスト ROC-AUC = 0.7260 (95% CI [0.711, 0.739])",
            "c13_d": "訓練: 2002–2013年 | 検証: 2014–2015年 | テスト: 2016–2018年 (N = 5,889)。未来情報のリークを完全排除した時系列検証。",
        }
    }

    for lang_key, t in i18n.items():
        html_content = f"""<!DOCTYPE html>
<html lang="{t['lang']}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{t['title']}</title>
  <script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>
  <style>
    :root {{
      --bg-dark: #090d16;
      --bg-card: #111827;
      --bg-card-hover: #1e293b;
      --border-col: #1f2937;
      --accent-blue: #38bdf8;
      --accent-purple: #a855f7;
      --accent-green: #10b981;
      --accent-amber: #f59e0b;
      --text-main: #f8fafc;
      --text-muted: #94a3b8;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      font-family: 'Inter', 'Segoe UI', 'Yu Gothic', 'Meiryo', system-ui, -apple-system, sans-serif;
      background: var(--bg-dark);
      color: var(--text-main);
      margin: 0;
      padding: 0;
    }}
    header {{
      background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
      border-bottom: 1px solid #334155;
      padding: 18px 32px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 16px;
    }}
    .brand h1 {{
      margin: 0;
      font-size: 21px;
      font-weight: 800;
      background: linear-gradient(90deg, #38bdf8, #c084fc, #34d399);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }}
    .brand p {{
      margin: 5px 0 0 0;
      color: var(--text-muted);
      font-size: 12.5px;
    }}
    .badges {{
      display: flex;
      gap: 8px;
      align-items: center;
      flex-wrap: wrap;
    }}
    .badge {{
      padding: 6px 12px;
      border-radius: 999px;
      font-size: 12px;
      font-weight: 600;
      background: rgba(56, 189, 248, 0.12);
      border: 1px solid rgba(56, 189, 248, 0.35);
      color: #38bdf8;
      text-decoration: none;
      transition: all 0.15s ease;
    }}
    .badge:hover {{
      transform: translateY(-1px);
      background: rgba(56, 189, 248, 0.22);
    }}
    .badge.lang-active {{
      background: #38bdf8;
      color: #0f172a;
      border-color: #38bdf8;
      font-weight: 800;
    }}
    .badge.zenodo {{
      background: rgba(168, 85, 247, 0.15);
      border-color: rgba(168, 85, 247, 0.45);
      color: #e9d5ff;
    }}
    .container {{
      max-width: 1720px;
      margin: 0 auto;
      padding: 24px 28px 48px 28px;
    }}
    .kpi-row {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
      gap: 16px;
      margin-bottom: 24px;
    }}
    .kpi-card {{
      background: var(--bg-card);
      border: 1px solid var(--border-col);
      border-radius: 12px;
      padding: 16px 18px;
      position: relative;
      overflow: hidden;
      box-shadow: 0 4px 16px rgba(0,0,0,0.35);
    }}
    .kpi-card::before {{
      content: '';
      position: absolute;
      top: 0; left: 0; width: 4px; height: 100%;
      background: var(--accent-blue);
    }}
    .kpi-card.purple::before {{ background: var(--accent-purple); }}
    .kpi-card.green::before {{ background: var(--accent-green); }}
    .kpi-card.amber::before {{ background: var(--accent-amber); }}
    .kpi-title {{ font-size: 11.5px; text-transform: uppercase; letter-spacing: 0.7px; color: var(--text-muted); font-weight: 600; }}
    .kpi-value {{ font-size: 25px; font-weight: 800; margin: 6px 0 4px 0; color: #ffffff; }}
    .kpi-sub {{ font-size: 11.8px; color: #64748b; }}

    .section-header {{
      margin: 28px 0 14px 0;
      padding-bottom: 8px;
      border-bottom: 1px solid #1e293b;
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      flex-wrap: wrap;
      gap: 8px;
    }}
    .section-header h2 {{
      margin: 0;
      font-size: 17px;
      color: #e2e8f0;
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .section-header span {{
      font-size: 12.5px;
      color: var(--text-muted);
    }}

    .grid-2 {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 20px;
      margin-bottom: 22px;
    }}
    .grid-1 {{
      display: grid;
      grid-template-columns: 1fr;
      gap: 20px;
      margin-bottom: 22px;
    }}
    @media (max-width: 1150px) {{
      .grid-2 {{ grid-template-columns: 1fr; }}
    }}
    .card {{
      background: var(--bg-card);
      border: 1px solid #1e293b;
      border-radius: 14px;
      padding: 18px;
      box-shadow: 0 8px 24px rgba(0,0,0,0.35);
    }}
    .card-header {{
      margin-bottom: 10px;
    }}
    .card-header h3 {{
      margin: 0 0 4px 0;
      font-size: 14.8px;
      color: #f1f5f9;
      font-weight: 700;
    }}
    .card-header p {{
      margin: 0;
      font-size: 12px;
      color: #94a3b8;
    }}
    .chart {{ width: 100%; height: 430px; }}
    .chart-tall {{ width: 100%; height: 500px; }}
    footer {{
      text-align: center;
      padding: 24px;
      color: #64748b;
      font-size: 12.5px;
      border-top: 1px solid #1e293b;
    }}
  </style>
</head>
<body>
  <header>
    <div class="brand">
      <h1>🏇 {t['title']}</h1>
      <p>{t['subtitle']}</p>
    </div>
    <div class="badges">
      <a class="badge {'lang-active' if lang_key=='pt' else ''}" href="superset_interactive_dashboard.html" onclick="if(location.hostname==='htmlpreview.github.io'){{location.href='https://htmlpreview.github.io/?https://github.com/ImArthz/AEDS2_jra_analysis/blob/main/docs/superset_interactive_dashboard.html';return false;}}">🇧🇷 PT-BR</a>
      <a class="badge {'lang-active' if lang_key=='en' else ''}" href="superset_interactive_dashboard_en.html" onclick="if(location.hostname==='htmlpreview.github.io'){{location.href='https://htmlpreview.github.io/?https://github.com/ImArthz/AEDS2_jra_analysis/blob/main/docs/superset_interactive_dashboard_en.html';return false;}}">🇺🇸 EN</a>
      <a class="badge {'lang-active' if lang_key=='ja' else ''}" href="superset_interactive_dashboard_ja.html" onclick="if(location.hostname==='htmlpreview.github.io'){{location.href='https://htmlpreview.github.io/?https://github.com/ImArthz/AEDS2_jra_analysis/blob/main/docs/superset_interactive_dashboard_ja.html';return false;}}">🇯🇵 日本語</a>
      <span class="badge">{t['badge_charts']}</span>
      <span class="badge">{t['badge_qa']}</span>
      <a class="badge zenodo" href="https://doi.org/10.5281/zenodo.23681764" target="_blank">DOI: 10.5281/zenodo.23681764</a>
    </div>
  </header>

  <div class="container">
    <!-- KPI METRIC CARDS -->
    <div class="kpi-row">
      <div class="kpi-card">
        <div class="kpi-title">{t['kpi1_t']}</div>
        <div class="kpi-value">3,216 / 33,409</div>
        <div class="kpi-sub">{t['kpi1_s']}</div>
      </div>
      <div class="kpi-card purple">
        <div class="kpi-title">{t['kpi2_t']}</div>
        <div class="kpi-value">504,074</div>
        <div class="kpi-sub">{t['kpi2_s']}</div>
      </div>
      <div class="kpi-card amber">
        <div class="kpi-title">{t['kpi3_t']}</div>
        <div class="kpi-value">Sounds of Earth</div>
        <div class="kpi-sub">{t['kpi3_s']}</div>
      </div>
      <div class="kpi-card green">
        <div class="kpi-title">{t['kpi4_t']}</div>
        <div class="kpi-value">p &lt; 10⁻³⁰⁰</div>
        <div class="kpi-sub">{t['kpi4_s']}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-title">{t['kpi5_t']}</div>
        <div class="kpi-value">0.7260 AUC</div>
        <div class="kpi-sub">{t['kpi5_s']}</div>
      </div>
      <div class="kpi-card purple">
        <div class="kpi-title">{t['kpi6_t']}</div>
        <div class="kpi-value">Northern Dancer</div>
        <div class="kpi-sub">{t['kpi6_s']}</div>
      </div>
    </div>

    <!-- SECTION 1 -->
    <div class="section-header">
      <h2>{t['sec1_h']}</h2>
      <span>{t['sec1_s']}</span>
    </div>
    <div class="grid-1">
      <div class="card">
        <div class="card-header">
          <h3>{t['c1_t']}</h3>
          <p>{t['c1_d']}</p>
        </div>
        <div id="sankeyChart" class="chart-tall"></div>
      </div>
    </div>

    <div class="grid-2">
      <div class="card">
        <div class="card-header">
          <h3>{t['c2_t']}</h3>
          <p>{t['c2_d']}</p>
        </div>
        <div id="sunburstChart" class="chart-tall"></div>
      </div>
      <div class="card">
        <div class="card-header">
          <h3>{t['c3_t']}</h3>
          <p>{t['c3_d']}</p>
        </div>
        <div id="radarChart" class="chart-tall"></div>
      </div>
    </div>

    <!-- SECTION 2 -->
    <div class="section-header">
      <h2>{t['sec2_h']}</h2>
      <span>{t['sec2_s']}</span>
    </div>
    <div class="grid-2">
      <div class="card">
        <div class="card-header">
          <h3>{t['c4_t']}</h3>
          <p>{t['c4_d']}</p>
        </div>
        <div id="quadrantChart" class="chart"></div>
      </div>
      <div class="card">
        <div class="card-header">
          <h3>{t['c5_t']}</h3>
          <p>{t['c5_d']}</p>
        </div>
        <div id="prChart" class="chart"></div>
      </div>
    </div>

    <div class="grid-1">
      <div class="card">
        <div class="card-header">
          <h3>{t['c6_t']}</h3>
          <p>{t['c6_d']}</p>
        </div>
        <div id="treemapChart" class="chart"></div>
      </div>
    </div>

    <!-- SECTION 3 -->
    <div class="section-header">
      <h2>{t['sec3_h']}</h2>
      <span>{t['sec3_s']}</span>
    </div>
    <div class="grid-2">
      <div class="card">
        <div class="card-header">
          <h3>{t['c7_t']}</h3>
          <p>{t['c7_d']}</p>
        </div>
        <div id="pcaChart" class="chart"></div>
      </div>
      <div class="card">
        <div class="card-header">
          <h3>{t['c8_t']}</h3>
          <p>{t['c8_d']}</p>
        </div>
        <div id="parallelChart" class="chart"></div>
      </div>
    </div>

    <div class="grid-2">
      <div class="card">
        <div class="card-header">
          <h3>{t['c9_t']}</h3>
          <p>{t['c9_d']}</p>
        </div>
        <div id="streamChart" class="chart"></div>
      </div>
      <div class="card">
        <div class="card-header">
          <h3>{t['c10_t']}</h3>
          <p>{t['c10_d']}</p>
        </div>
        <div id="heatmapChart" class="chart"></div>
      </div>
    </div>

    <!-- SECTION 4 -->
    <div class="section-header">
      <h2>{t['sec4_h']}</h2>
      <span>{t['sec4_s']}</span>
    </div>
    <div class="grid-2">
      <div class="card">
        <div class="card-header">
          <h3>{t['c11_t']}</h3>
          <p>{t['c11_d']}</p>
        </div>
        <div id="jockeyChart" class="chart"></div>
      </div>
      <div class="card">
        <div class="card-header">
          <h3>{t['c12_t']}</h3>
          <p>{t['c12_d']}</p>
        </div>
        <div id="biometricsChart" class="chart"></div>
      </div>
    </div>

    <div class="grid-1">
      <div class="card">
        <div class="card-header">
          <h3>{t['c13_t']}</h3>
          <p>{t['c13_d']}</p>
        </div>
        <div id="mlChart" class="chart"></div>
      </div>
    </div>
  </div>

  <footer>
    Apache Superset 6.1 / Apache ECharts 5.5 Interactive Suite • Dataset DOI: <a href="https://doi.org/10.5281/zenodo.23681764" style="color:#38bdf8;">10.5281/zenodo.23681764</a> • CEFET-MG (Campus Divinópolis)
  </footer>

  <script>
    function renderAllCharts() {{
      if (typeof echarts === 'undefined') {{
        setTimeout(renderAllCharts, 60);
        return;
      }}
      const charts = [];
      function initChart(id) {{
        const el = document.getElementById(id);
        const prev = echarts.getInstanceByDom(el);
        if (prev) prev.dispose();
        const c = echarts.init(el, 'dark');
        charts.push(c);
        return c;
      }}
      window.addEventListener('resize', () => charts.forEach(c => c.resize()));

    // 1. SANKEY 4-STAGE
    const sankeyChart = initChart('sankeyChart');
    sankeyChart.setOption({{
      backgroundColor: 'transparent',
      tooltip: {{ trigger: 'item', triggerOn: 'mousemove' }},
      series: [{{
        type: 'sankey',
        left: '2%', right: '10%', top: '4%', bottom: '4%',
        nodeWidth: 18,
        nodeGap: 10,
        data: {json.dumps(sankey_nodes)},
        links: {json.dumps(sankey_links)},
        emphasis: {{ focus: 'adjacency' }},
        lineStyle: {{ color: 'gradient', curveness: 0.48, opacity: 0.48 }},
        label: {{ color: '#f8fafc', fontSize: 11.5, fontWeight: 'bold' }}
      }}]
    }});

    // 2. SUNBURST 3-RING
    const sunburstChart = initChart('sunburstChart');
    sunburstChart.setOption({{
      backgroundColor: 'transparent',
      tooltip: {{ trigger: 'item', formatter: '{{b}}: <b>{{c}}</b>' }},
      series: [{{
        type: 'sunburst',
        data: {json.dumps(sunburst_tree)},
        radius: ['12%', '92%'],
        itemStyle: {{ borderRadius: 5, borderWidth: 1.5, borderColor: '#0f172a' }},
        label: {{ rotate: 'radial', fontSize: 10, color: '#f8fafc' }},
        levels: [
          {{}},
          {{ r0: '12%', r: '38%', label: {{ rotate: 0, fontSize: 12, fontWeight: 'bold' }} }},
          {{ r0: '38%', r: '64%', label: {{ fontSize: 11, fontWeight: 'bold' }} }},
          {{ r0: '64%', r: '92%', label: {{ fontSize: 9.5 }} }}
        ]
      }}]
    }});

    // 3. RADAR 6-AXIS
    const radarChart = initChart('radarChart');
    radarChart.setOption({{
      backgroundColor: 'transparent',
      tooltip: {{ trigger: 'item' }},
      legend: {{ bottom: 0, textStyle: {{ fontSize: 11 }} }},
      radar: {{
        center: ['50%', '45%'],
        radius: '64%',
        indicator: [
          {{ name: 'PageRank Prestige', max: 100 }},
          {{ name: 'Graded Win Rate (%)', max: 100 }},
          {{ name: 'Top-3 Podium Consistency (%)', max: 100 }},
          {{ name: 'Career Earnings (Oku-Yen)', max: 100 }},
          {{ name: 'Stamina Index (Distance)', max: 100 }},
          {{ name: 'G1 Rivalry Volume (Starts)', max: 100 }}
        ],
        axisName: {{ color: '#e2e8f0', fontSize: 11, fontWeight: 'bold' }},
        splitArea: {{ areaStyle: {{ color: ['rgba(30,41,59,0.3)', 'rgba(15,23,42,0.5)'] }} }}
      }},
      series: [{{
        type: 'radar',
        data: {json.dumps(radar_series_data)}
      }}]
    }});

    // 4. PAGERANK SCATTER QUADRANT
    const quadrantChart = initChart('quadrantChart');
    function quadTooltip(params) {{
      const d = params.data;
      return `<b>#${{d.rank}} ${{d.name}}</b> (Sire: ${{d.sire}})<br/>` +
             `Scaled PageRank: <b>${{d.pr}}</b><br/>` +
             `Graded Wins: <b>${{d.wins}}</b> (G1: <b>${{d.g1}}</b>)<br/>` +
             `Top-3 Podiums: <b>${{d.podiums}}</b> / ${{d.starts}} starts<br/>` +
             `Earnings: <b>¥${{d.earn}}M</b> | Wright F_X: <b>${{d.fx}}%</b>`;
    }}
    quadrantChart.setOption({{
      backgroundColor: 'transparent',
      tooltip: {{ trigger: 'item', formatter: quadTooltip }},
      legend: {{ bottom: 0 }},
      grid: {{ top: '8%', left: '10%', right: '8%', bottom: '16%' }},
      xAxis: {{ type: 'value', name: 'Graded Wins', splitLine: {{ lineStyle: {{ type: 'dashed', color: '#1e293b' }} }} }},
      yAxis: {{ type: 'value', name: 'Sports PageRank (d=0.85)', splitLine: {{ lineStyle: {{ type: 'dashed', color: '#1e293b' }} }} }},
      dataZoom: [{{ type: 'inside' }}],
      series: [
        {{
          name: 'G1 / Graded Champions',
          type: 'scatter',
          symbolSize: val => Math.max(9, Math.min(36, Math.sqrt(val[2]) * 0.75)),
          itemStyle: {{ color: '#a855f7', opacity: 0.78 }},
          data: {json.dumps(g1_champs)}
        }},
        {{
          name: 'Silver Collectors (0 G1 Wins)',
          type: 'scatter',
          symbolSize: val => Math.max(12, Math.min(34, Math.sqrt(val[2]) * 0.85)),
          itemStyle: {{ color: '#38bdf8', opacity: 0.92, borderColor: '#fff', borderWidth: 1.2 }},
          data: {json.dumps(silver_cols)}
        }},
        {{
          name: 'Underdog Diamonds (0 Graded Wins!)',
          type: 'scatter',
          symbol: 'diamond',
          symbolSize: 20,
          itemStyle: {{ color: '#f97316', borderColor: '#fff', borderWidth: 1.5 }},
          label: {{ show: true, formatter: p => p.data.name, position: 'right', color: '#fdba74', fontSize: 10.5, fontWeight: 'bold' }},
          data: {json.dumps(underdogs)}
        }}
      ]
    }});

    // 5. TOP 15 PAGERANK BAR + PODIUM LINE
    const topPr = {json.dumps(pr_df.head(15)[["horse_name", "pagerank_scaled", "graded_podiums", "graded_wins"]].to_dict(orient="records"))};
    const prChart = initChart('prChart');
    prChart.setOption({{
      backgroundColor: 'transparent',
      tooltip: {{ trigger: 'axis' }},
      legend: {{ bottom: 0 }},
      grid: {{ top: '10%', left: '10%', right: '10%', bottom: '22%' }},
      xAxis: {{ type: 'category', data: topPr.map(x => x.horse_name), axisLabel: {{ rotate: 28, fontSize: 10.5 }} }},
      yAxis: [
        {{ type: 'value', name: 'Scaled PageRank' }},
        {{ type: 'value', name: 'Podiums / Wins' }}
      ],
      series: [
        {{ name: 'PageRank Score', type: 'bar', data: topPr.map(x => Number(x.pagerank_scaled.toFixed(2))), itemStyle: {{ color: '#8b5cf6', borderRadius: [4,4,0,0] }} }},
        {{ name: 'Graded Podiums (Top-3)', type: 'line', yAxisIndex: 1, data: topPr.map(x => x.graded_podiums), itemStyle: {{ color: '#38bdf8' }}, lineStyle: {{ width: 3 }} }},
        {{ name: 'Graded Wins', type: 'line', yAxisIndex: 1, data: topPr.map(x => x.graded_wins), itemStyle: {{ color: '#10b981' }}, lineStyle: {{ width: 2, type: 'dashed' }} }}
      ]
    }});

    // 6. TREEMAP FOUNDING ANCESTORS & WRIGHT'S INBREEDING F_X
    const treemapChart = initChart('treemapChart');
    treemapChart.setOption({{
      backgroundColor: 'transparent',
      tooltip: {{
        formatter: info => {{
          const d = info.data;
          return `<b>${{d.name.split('(')[0]}}</b><br/>` +
                 `Inbred Horses (LCA): <b>${{d.inbred_cases.toLocaleString()}}</b><br/>` +
                 `Graded Wins by Inbred Progeny: <b>${{d.graded_wins.toLocaleString()}}</b>`;
        }}
      }},
      series: [{{
        type: 'treemap',
        width: '96%', height: '90%',
        roam: false,
        nodeClick: false,
        breadcrumb: {{ show: false }},
        label: {{ show: true, formatter: '{{b}}', fontSize: 11.5, fontWeight: 'bold' }},
        itemStyle: {{ borderColor: '#0f172a', borderWidth: 2, gapWidth: 2 }},
        visualDimension: 0,
        colorSaturation: [0.45, 0.85],
        data: {json.dumps(treemap_ancestors)}
      }}]
    }});

    // 7. K-MEANS++ 2D PCA CLUSTERS
    const pcaData = {json.dumps(pca_series_map)};
    const pcaColors = {{
      'Cluster A: Dirt & Sand Power Specialists': '#f59e0b',
      'Cluster B: Speed & Mile Turf Sires': '#38bdf8',
      'Cluster C: Elite Classic & G1 Turf Dynasties': '#a855f7',
      'Cluster D: Classic Stayers & Long-Distance Sires': '#10b981'
    }};
    const pcaChart = initChart('pcaChart');
    pcaChart.setOption({{
      backgroundColor: 'transparent',
      tooltip: {{
        trigger: 'item',
        formatter: p => {{
          const v = p.data.value;
          return `<b>${{v[3]}}</b><br/>${{p.seriesName}}<br/>` +
                 `Graded Starts: <b>${{v[2]}}</b> | G1 Wins: <b>${{v[7]}}</b><br/>` +
                 `Turf Share: <b>${{v[4]}}%</b> | Mean Dist: <b>${{v[5]}}m</b><br/>` +
                 `Win Rate: <b>${{v[6]}}%</b> | Progeny Mean PageRank: <b>${{v[8]}}</b>`;
        }}
      }},
      legend: {{ bottom: 0, textStyle: {{ fontSize: 10.5 }} }},
      grid: {{ top: '8%', left: '10%', right: '6%', bottom: '18%' }},
      xAxis: {{ type: 'value', name: 'PC1 (44.1% Var — Surface & Distance)', splitLine: {{ lineStyle: {{ color: '#1e293b' }} }} }},
      yAxis: {{ type: 'value', name: 'PC2 (19.2% Var — G1 Prestige & Win Rate)', splitLine: {{ lineStyle: {{ color: '#1e293b' }} }} }},
      dataZoom: [{{ type: 'inside' }}],
      series: Object.keys(pcaData).map(arch => ({{
        name: arch,
        type: 'scatter',
        symbolSize: val => Math.max(9, Math.min(38, Math.sqrt(val[2]) * 1.05)),
        itemStyle: {{ color: pcaColors[arch] || '#94a3b8', opacity: 0.85, borderColor: '#0f172a', borderWidth: 1 }},
        data: pcaData[arch]
      }}))
    }});

    // 8. PARALLEL COORDINATES WITH LIVE BRUSH FILTER
    const parallelRaw = {json.dumps(parallel_data)};
    const parallelChart = initChart('parallelChart');
    parallelChart.setOption({{
      backgroundColor: 'transparent',
      tooltip: {{ trigger: 'item' }},
      legend: {{ bottom: 0, textStyle: {{ fontSize: 10.5 }} }},
      parallelAxis: [
        {{ dim: 0, name: 'Turf Share (%)' }},
        {{ dim: 1, name: 'Mean Dist (m)' }},
        {{ dim: 2, name: 'Win Rate (%)' }},
        {{ dim: 3, name: 'Podium Rate (%)' }},
        {{ dim: 4, name: 'G1 Share (%)' }},
        {{ dim: 5, name: 'Progeny PageRank' }}
      ],
      parallel: {{
        left: '6%', right: '8%', top: '12%', bottom: '20%',
        parallelAxisDefault: {{
          type: 'value',
          nameLocation: 'end',
          nameGap: 14,
          nameTextStyle: {{ color: '#e2e8f0', fontSize: 11, fontWeight: 'bold' }},
          axisLine: {{ lineStyle: {{ color: '#475569' }} }},
          axisLabel: {{ color: '#94a3b8', fontSize: 10 }}
        }}
      }},
      series: Object.keys(pcaColors).map(arch => ({{
        name: arch,
        type: 'parallel',
        lineStyle: {{ width: 1.8, opacity: 0.55, color: pcaColors[arch] }},
        emphasis: {{ lineStyle: {{ width: 4, opacity: 1 }} }},
        data: parallelRaw.filter(d => d.archetype === arch).map(d => d.value)
      }}))
    }});

    // 9. EVOLUTIONARY STREAM / STACKED AREA (2002-2018)
    const streamChart = initChart('streamChart');
    streamChart.setOption({{
      backgroundColor: 'transparent',
      tooltip: {{ trigger: 'axis', axisPointer: {{ type: 'cross' }} }},
      legend: {{ top: 0, textStyle: {{ fontSize: 10 }} }},
      grid: {{ top: '18%', left: '8%', right: '5%', bottom: '18%' }},
      dataZoom: [{{ type: 'slider', bottom: 4, height: 18 }}, {{ type: 'inside' }}],
      xAxis: {{ type: 'category', boundaryGap: false, data: {json.dumps(stream_years)} }},
      yAxis: {{ type: 'value', name: 'Graded Starts / Year' }},
      series: {json.dumps(stream_series)}
    }});

    // 10. GENETIC DISTANCE SPECIALIZATION HEATMAP
    const heatmapChart = initChart('heatmapChart');
    heatmapChart.setOption({{
      backgroundColor: 'transparent',
      tooltip: {{
        position: 'top',
        formatter: p => `<b>${{p.name}}</b><br/>Distance Share: <b>${{p.data[2]}}%</b>`
      }},
      grid: {{ top: '6%', left: '24%', right: '8%', bottom: '18%' }},
      xAxis: {{ type: 'category', data: {json.dumps(heatmap_dist_labels)}, axisLabel: {{ fontSize: 10, interval: 0 }} }},
      yAxis: {{ type: 'category', data: {json.dumps(heatmap_sire_labels)}, axisLabel: {{ fontSize: 10.5, fontWeight: 'bold' }} }},
      visualMap: {{
        min: 0, max: 65,
        calculable: true,
        orient: 'horizontal',
        left: 'center',
        bottom: 0,
        inRange: {{ color: ['#0f172a', '#1d4ed8', '#38bdf8', '#facc15'] }}
      }},
      series: [{{
        name: 'Distance Share (%)',
        type: 'heatmap',
        data: {json.dumps(heatmap_cells)},
        label: {{ show: true, formatter: p => p.data[2] + '%', fontSize: 10, fontWeight: 'bold' }},
        emphasis: {{ itemStyle: {{ shadowBlur: 10, shadowColor: 'rgba(0,0,0,0.5)' }} }}
      }}]
    }});

    // 11. TOP 15 JOCKEYS SYNERGY
    const jData = {json.dumps(jockey_json)};
    const jockeyChart = initChart('jockeyChart');
    jockeyChart.setOption({{
      backgroundColor: 'transparent',
      tooltip: {{ trigger: 'axis' }},
      legend: {{ bottom: 0 }},
      grid: {{ top: '10%', left: '10%', right: '10%', bottom: '22%' }},
      xAxis: {{ type: 'category', data: jData.map(x => x.jockey), axisLabel: {{ rotate: 28, fontSize: 10.5 }} }},
      yAxis: [
        {{ type: 'value', name: 'Graded / G1 Wins' }},
        {{ type: 'value', name: 'Podium Rate (%)', max: 60 }}
      ],
      series: [
        {{ name: 'Total Graded Wins', type: 'bar', data: jData.map(x => x.wins), itemStyle: {{ color: '#38bdf8', borderRadius: [4,4,0,0] }} }},
        {{ name: 'G1 Wins', type: 'bar', data: jData.map(x => x.g1_wins), itemStyle: {{ color: '#eab308', borderRadius: [4,4,0,0] }} }},
        {{ name: 'Top-3 Podium Rate (%)', type: 'line', yAxisIndex: 1, data: jData.map(x => x.podium_rate), itemStyle: {{ color: '#10b981' }}, lineStyle: {{ width: 3 }} }}
      ]
    }});

    // 12. EQUINE BIOMETRICS (BODY MASS KG & SPEED KM/H)
    const biometricsChart = initChart('biometricsChart');
    biometricsChart.setOption({{
      backgroundColor: 'transparent',
      tooltip: {{ trigger: 'axis' }},
      legend: {{ bottom: 0, textStyle: {{ fontSize: 10.5 }} }},
      grid: {{ top: '12%', left: '10%', right: '10%', bottom: '18%' }},
      xAxis: {{ type: 'category', data: {json.dumps(heatmap_dist_labels)} }},
      yAxis: [
        {{ type: 'value', name: 'Body Mass (kg)', min: 460, max: 508 }},
        {{ type: 'value', name: 'Mean Speed (km/h)', min: 57, max: 63 }}
      ],
      series: [
        {{ name: 'Body Mass — Turf (kg)', type: 'bar', data: {json.dumps(bio_turf_kg)}, itemStyle: {{ color: '#10b981', borderRadius: [4,4,0,0] }} }},
        {{ name: 'Body Mass — Dirt (kg)', type: 'bar', data: {json.dumps(bio_dirt_kg)}, itemStyle: {{ color: '#f59e0b', borderRadius: [4,4,0,0] }} }},
        {{ name: 'Mean Speed — Turf (km/h)', type: 'line', yAxisIndex: 1, data: {json.dumps(bio_turf_spd)}, itemStyle: {{ color: '#38bdf8' }}, lineStyle: {{ width: 3 }} }},
        {{ name: 'Mean Speed — Dirt (km/h)', type: 'line', yAxisIndex: 1, data: {json.dumps(bio_dirt_spd)}, itemStyle: {{ color: '#fb7185' }}, lineStyle: {{ width: 3, type: 'dashed' }} }}
      ]
    }});

    // 13. RANDOM FOREST FEATURE IMPORTANCE
    const mlChart = initChart('mlChart');
    mlChart.setOption({{
      backgroundColor: 'transparent',
      tooltip: {{ trigger: 'axis', formatter: p => `<b>${{p[0].name}}</b><br/>Relative Gini Importance: <b>${{p[0].value}}%</b>` }},
      grid: {{ top: '6%', left: '18%', right: '8%', bottom: '10%' }},
      xAxis: {{ type: 'value', name: 'Relative Gini Importance (%)' }},
      yAxis: {{ type: 'category', data: {json.dumps(rf_features)}, axisLabel: {{ fontSize: 11.5, fontWeight: 'bold', color: '#e2e8f0' }} }},
      series: [{{
        type: 'bar',
        data: {json.dumps(rf_importances)},
        itemStyle: {{
          borderRadius: [0, 6, 6, 0],
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            {{ offset: 0, color: '#6366f1' }},
            {{ offset: 0.5, color: '#38bdf8' }},
            {{ offset: 1, color: '#10b981' }}
          ])
        }},
        label: {{ show: true, position: 'right', formatter: '{{c}}%', color: '#f8fafc', fontWeight: 'bold' }}
      }}]
    }});
    }}
    renderAllCharts();
  </script>
</body>
</html>
"""
        html_path = os.path.join(BASE_DIR, "docs", t["filename"])
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"[5/5] Mega Dashboard ({lang_key.upper()}) salvo em: {html_path}")


def main():
    print("=" * 76)
    print("  GERANDO VISUALIZAÇÕES AVANÇADAS (ESTILO APACHE SUPERSET 6.1 & DATAVIZ)")
    print("=" * 76)
    df, races, horses, pr_df, clusters_df = load_merged_data()
    plot_alluvial_sankey(df)
    plot_radar_and_sunburst(df, races, pr_df)
    plot_streamgraph_dynasties(df)
    plot_raincloud_and_parallel(df, clusters_df)
    generate_superset_html_dashboard(df, races, pr_df, clusters_df)
    print("\n[Concluído com sucesso!]")


if __name__ == "__main__":
    main()
