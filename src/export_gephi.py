"""
Etapa B — Exportação de Grafos para o Gephi (.gexf), Tabelas Analíticas de Redes (PageRank, LCA, Endogamia de Wright)
e Preparação de Metadados para Publicação Científica no Zenodo.
"""

import os
import sys
import json
import sqlite3
import collections
import pandas as pd
import networkx as nx
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "src"))

from graph_analysis import load_graphs_from_db

GEPHI_DIR = os.path.join(BASE_DIR, "data", "gephi")
ANALYSIS_DIR = os.path.join(BASE_DIR, "data", "analysis")
ASSETS_DIR = os.path.join(BASE_DIR, "docs", "assets")
ZENODO_DIR = os.path.join(BASE_DIR, "zenodo")
EN_DB_PATH = os.path.join(BASE_DIR, "data", "sqlite", "jra_graded_en.db")


MAJOR_SIRES = {
    "Deep Impact": "Deep Impact",
    "Sunday Silence(USA)": "Sunday Silence",
    "Sunday Silence": "Sunday Silence",
    "King Kamehameha": "King Kamehameha",
    "Stay Gold": "Stay Gold",
    "Heart's Cry": "Heart's Cry",
    "Lord Kanaloa": "Lord Kanaloa",
    "Kurofune(USA)": "Kurofune",
    "Kurofune": "Kurofune",
    "Daiwa Major": "Daiwa Major",
    "Manhattan Cafe": "Manhattan Cafe",
    "Symboli Kris S(USA)": "Symboli Kris S",
    "Rulership": "Rulership",
    "Harbinger(GB)": "Harbinger",
    "Epiphaneia": "Epiphaneia",
    "Duramente": "Duramente",
    "Orfevre": "Orfevre",
    "Gold Allure": "Gold Allure",
    "Kitasan Black": "Kitasan Black",
}


def get_era_label(year):
    if not year or year <= 0:
        return "Unknown"
    if year <= 2007:
        return "1. Classic Era (2002-2007)"
    if year <= 2013:
        return "2. Golden Transition (2008-2013)"
    if year <= 2019:
        return "3. Deep Impact Dynasty (2014-2019)"
    return "4. Modern Era (2020-2025)"


def build_horse_metadata(conn, ped_dag, comp_graph):
    """Consolida atributos ricos de cada cavalo para exportação Gephi e CSV."""
    df_horses = pd.read_sql_query("""
        SELECT name, sex, birth_year, color, breeder, owner,
               COALESCE(total_earnings, 0) AS total_earnings,
               COALESCE(total_starts, 0) AS total_starts,
               COALESCE(total_wins, 0) AS total_wins
        FROM horses
    """, conn)

    df_ped = pd.read_sql_query("""
        SELECT horse_name, COALESCE(sire_name, '') AS sire_name,
               COALESCE(dam_name, '') AS dam_name,
               COALESCE(dam_sire_name, '') AS dam_sire_name
        FROM pedigree
    """, conn)

    df_race_stats = pd.read_sql_query("""
        SELECT 
            re.horse_name,
            COUNT(*) AS graded_starts,
            SUM(CASE WHEN re.position = 1 THEN 1 ELSE 0 END) AS graded_wins,
            SUM(CASE WHEN re.position = 1 AND r.grade = 'G1' THEN 1 ELSE 0 END) AS g1_wins,
            SUM(CASE WHEN re.position = 2 AND r.grade = 'G1' THEN 1 ELSE 0 END) AS g1_seconds,
            SUM(CASE WHEN re.position <= 3 AND r.grade = 'G1' THEN 1 ELSE 0 END) AS g1_podiums,
            SUM(CASE WHEN re.position <= 3 THEN 1 ELSE 0 END) AS graded_podiums,
            CAST(ROUND(AVG(r.year)) AS INTEGER) AS peak_year
        FROM race_entries re
        JOIN races r ON re.race_id = r.race_id
        WHERE re.position < 90
        GROUP BY re.horse_name
    """, conn)

    pr_list = comp_graph.compute_pagerank(damping=0.85)
    pr_map = dict(pr_list)
    deg_map = dict(comp_graph.degree_centrality())

    meta = {}
    ped_map = df_ped.drop_duplicates(subset=["horse_name"]).set_index("horse_name").to_dict(orient="index")
    stats_map = df_race_stats.drop_duplicates(subset=["horse_name"]).set_index("horse_name").to_dict(orient="index")

    for _, row in df_horses.drop_duplicates(subset=["name"]).iterrows():
        h = row["name"]
        p_info = ped_map.get(h, {})
        s_info = stats_map.get(h, {})
        sire = p_info.get("sire_name", "") or "Unknown"
        sire_group = MAJOR_SIRES.get(sire, "Other Sires")
        fx, fx_details = ped_dag.wright_inbreeding_coefficient(h)
        peak_yr = int(s_info.get("peak_year", 0) or (row["birth_year"] + 4 if pd.notna(row["birth_year"]) and row["birth_year"] else 2015))
        pr_val = float(pr_map.get(h, 0.0))

        meta[h] = {
            "horse_name": h,
            "pagerank_raw": pr_val,
            "pagerank_scaled": round(pr_val * 10000.0, 4),
            "weighted_degree": round(float(deg_map.get(h, 0.0)), 2),
            "graded_starts": int(s_info.get("graded_starts", 0) or 0),
            "graded_wins": int(s_info.get("graded_wins", 0) or 0),
            "g1_wins": int(s_info.get("g1_wins", 0) or 0),
            "g1_seconds": int(s_info.get("g1_seconds", 0) or 0),
            "g1_podiums": int(s_info.get("g1_podiums", 0) or 0),
            "graded_podiums": int(s_info.get("graded_podiums", 0) or 0),
            "total_earnings_yen": int(row["total_earnings"] or 0),
            "total_earnings_m_yen": round(float(row["total_earnings"] or 0) / 1_000_000.0, 2),
            "sex": str(row["sex"] or "Unknown"),
            "birth_year": int(row["birth_year"]) if pd.notna(row["birth_year"]) and row["birth_year"] else 0,
            "peak_year": peak_yr,
            "era": get_era_label(peak_yr),
            "color": str(row["color"] or "Unknown"),
            "sire": sire,
            "dam": str(p_info.get("dam_name", "") or "Unknown"),
            "dam_sire": str(p_info.get("dam_sire_name", "") or "Unknown"),
            "sire_group": sire_group,
            "inbreeding_fx_pct": round(fx * 100.0, 3),
            "inbreeding_crosses": "; ".join(fx_details[:3]) if fx_details else "Outcross",
        }

    return meta


def export_competition_gexf(comp_graph, meta, top_n, filename, min_edge_weight=0.5):
    """Exporta subgrafo de competição direcionado (loser -> winner) para Gephi (.gexf)."""
    ranked_horses = sorted(
        [h for h in comp_graph.nodes if h in meta],
        key=lambda x: meta[x]["pagerank_raw"],
        reverse=True
    )[:top_n]
    selected = set(ranked_horses)

    G = nx.DiGraph()
    for rank, h in enumerate(ranked_horses, 1):
        m = meta[h]
        G.add_node(
            h,
            label=h,
            pagerank_rank=rank,
            pagerank_score=float(m["pagerank_scaled"]),
            weighted_degree=float(m["weighted_degree"]),
            graded_starts=int(m["graded_starts"]),
            graded_wins=int(m["graded_wins"]),
            g1_wins=int(m["g1_wins"]),
            graded_podiums=int(m["graded_podiums"]),
            earnings_m_yen=float(m["total_earnings_m_yen"]),
            sire=str(m["sire"]),
            sire_group=str(m["sire_group"]),
            dam_sire=str(m["dam_sire"]),
            sex=str(m["sex"]),
            peak_year=int(m["peak_year"]),
            era=str(m["era"]),
            inbreeding_fx_pct=float(m["inbreeding_fx_pct"]),
        )

    for loser in selected:
        for winner, w in comp_graph.adj_prestige[loser].items():
            if winner in selected and w >= min_edge_weight:
                G.add_edge(loser, winner, weight=round(float(w), 2))

    out_path = os.path.join(GEPHI_DIR, filename)
    nx.write_gexf(G, out_path, encoding="utf-8")
    print(f"[Gephi] {filename:<36s} -> {G.number_of_nodes():,d} nós, {G.number_of_edges():,d} arestas")
    return G


def export_lineage_dag_gexf(ped_dag, meta, filename="lineage_dag_elite.gexf"):
    """
    Exporta o DAG Genealógico (Ancestral -> Descendente) focado nos campeões G1,
    Top 250 PageRank e seus ancestrais diretos até 3 gerações.
    """
    elite_horses = [
        h for h, m in meta.items()
        if m["g1_wins"] >= 1 or m["pagerank_scaled"] >= 3.0
    ]

    G = nx.DiGraph()
    progeny_counter = collections.Counter()
    for parent, children in ped_dag.adj_descendants.items():
        progeny_counter[parent] = len(children)

    included_nodes = set()
    edges_to_add = set()

    for h in elite_horses:
        tree = ped_dag.horse_trees.get(h, {})
        if not tree:
            continue
        included_nodes.add(h)
        # Adicionar até 3 gerações (S, D, SS, SD, DS, DD, SSS..DDD) para manter o DAG limpo e visual no Gephi
        for line, anc in tree.items():
            if len(line) > 3 or not anc:
                continue
            rel_type = "Sire Line" if line.endswith("S") else "Dam Line"
            child = h if len(line) == 1 else tree.get(line[:-1])
            if child and anc and child != anc:
                included_nodes.add(child)
                included_nodes.add(anc)
                # Fluxo genético no DAG: Ancestral -> Descendente
                edges_to_add.add((anc, child, rel_type, len(line)))

    for node in included_nodes:
        m = meta.get(node)
        prog_cnt = int(progeny_counter.get(node, 0))
        if m:
            role = "G1 Champion" if m["g1_wins"] > 0 else "Graded Contender"
            G.add_node(
                node,
                label=node,
                node_role=role,
                g1_wins=int(m["g1_wins"]),
                graded_wins=int(m["graded_wins"]),
                earnings_m_yen=float(m["total_earnings_m_yen"]),
                pagerank_score=float(m["pagerank_scaled"]),
                progeny_in_dag=prog_cnt,
                sire_group=str(m["sire_group"]),
                inbreeding_fx_pct=float(m["inbreeding_fx_pct"]),
            )
        else:
            role = "Foundation Sire/Dam" if prog_cnt >= 10 else "Ancestor"
            G.add_node(
                node,
                label=node,
                node_role=role,
                g1_wins=0,
                graded_wins=0,
                earnings_m_yen=0.0,
                pagerank_score=1.0,
                progeny_in_dag=prog_cnt,
                sire_group=MAJOR_SIRES.get(node, "Foundation Bloodline"),
                inbreeding_fx_pct=0.0,
            )

    for anc, child, rel_type, gen_depth in edges_to_add:
        weight = 3.0 if gen_depth == 1 else (2.0 if gen_depth == 2 else 1.0)
        G.add_edge(anc, child, weight=weight, relation=rel_type, generation_step=gen_depth)

    out_path = os.path.join(GEPHI_DIR, filename)
    nx.write_gexf(G, out_path, encoding="utf-8")
    print(f"[Gephi] {filename:<36s} -> {G.number_of_nodes():,d} nós, {G.number_of_edges():,d} arestas")
    return G


def export_bipartite_gexf(jh_graph, jt_graph, meta, filename="jockey_horse_trainer_network.gexf"):
    """Exporta rede de parcerias Jóquei ↔ Cavalo e Jóquei ↔ Treinador para o Gephi."""
    G = nx.Graph()

    top_jh = jh_graph.top_partnerships(250)
    top_jt = jt_graph.top_teams(150)

    for jockey, horse, weight in top_jh:
        j_id = f"Jockey: {jockey}"
        h_id = f"Horse: {horse}"
        G.add_node(j_id, label=jockey, entity_type="Jockey", size_metric=float(sum(jh_graph.adj[jockey].values())))
        m = meta.get(horse, {})
        G.add_node(
            h_id,
            label=horse,
            entity_type="Horse",
            size_metric=float(m.get("pagerank_scaled", 2.0) * 10.0),
        )
        G.add_edge(j_id, h_id, weight=round(float(weight), 2), interaction="Jockey-Horse Ride")

    for jockey, trainer, weight in top_jt:
        j_id = f"Jockey: {jockey}"
        t_id = f"Trainer: {trainer}"
        if j_id not in G:
            G.add_node(j_id, label=jockey, entity_type="Jockey", size_metric=float(sum(jh_graph.adj[jockey].values())))
        G.add_node(t_id, label=trainer, entity_type="Trainer", size_metric=float(sum(jt_graph.adj[trainer].values())))
        G.add_edge(j_id, t_id, weight=round(float(weight), 2), interaction="Jockey-Trainer Team")

    out_path = os.path.join(GEPHI_DIR, filename)
    nx.write_gexf(G, out_path, encoding="utf-8")
    print(f"[Gephi] {filename:<36s} -> {G.number_of_nodes():,d} nós, {G.number_of_edges():,d} arestas")
    return G


def export_analytical_csvs(conn, ped_dag, meta):
    """Gera tabelas analíticas em data/analysis/ para uso direto no artigo e em Machine Learning."""
    df_meta = pd.DataFrame(list(meta.values())).sort_values(by="pagerank_raw", ascending=False)
    df_meta["pagerank_rank"] = range(1, len(df_meta) + 1)

    cols_order = [
        "pagerank_rank", "horse_name", "pagerank_scaled", "pagerank_raw", "weighted_degree",
        "graded_starts", "graded_wins", "g1_wins", "g1_seconds", "g1_podiums", "graded_podiums",
        "total_earnings_m_yen", "sire", "dam", "dam_sire", "sire_group",
        "sex", "birth_year", "peak_year", "era", "inbreeding_fx_pct", "inbreeding_crosses"
    ]
    df_meta = df_meta[cols_order]
    df_meta.to_csv(os.path.join(ANALYSIS_DIR, "pagerank_full_ranking.csv"), index=False, encoding="utf-8-sig")

    # "Diamantes Azarões" (Cavalos com 0 vitórias G1 ou 0 vitórias Graded, mas altíssimo PageRank por baterem na trave contra lendas)
    df_underdogs = df_meta[(df_meta["graded_wins"] == 0) & (df_meta["graded_podiums"] >= 2)].head(50)
    df_underdogs.to_csv(os.path.join(ANALYSIS_DIR, "underdog_diamonds_zero_wins.csv"), index=False, encoding="utf-8-sig")

    df_g1_silver = df_meta[(df_meta["g1_wins"] == 0) & (df_meta["g1_podiums"] >= 2)].head(50)
    df_g1_silver.to_csv(os.path.join(ANALYSIS_DIR, "silver_collectors_zero_g1_wins.csv"), index=False, encoding="utf-8-sig")

    # Especialização de Sires por Superfície e Distância
    df_sire_spec = pd.read_sql_query("""
        SELECT 
            p.sire_name AS sire,
            COUNT(*) AS total_entries,
            COUNT(DISTINCT re.horse_name) AS unique_progeny,
            SUM(CASE WHEN re.position = 1 THEN 1 ELSE 0 END) AS graded_wins,
            SUM(CASE WHEN re.position = 1 AND r.grade = 'G1' THEN 1 ELSE 0 END) AS g1_wins,
            SUM(CASE WHEN re.position <= 3 THEN 1 ELSE 0 END) AS podiums,
            ROUND(100.0 * SUM(CASE WHEN re.position = 1 THEN 1 ELSE 0 END) / COUNT(*), 2) AS win_rate_pct,
            ROUND(100.0 * SUM(CASE WHEN re.position <= 3 THEN 1 ELSE 0 END) / COUNT(*), 2) AS podium_rate_pct,
            SUM(CASE WHEN r.surface = 'Turf' THEN 1 ELSE 0 END) AS turf_entries,
            SUM(CASE WHEN r.surface = 'Dirt' THEN 1 ELSE 0 END) AS dirt_entries,
            SUM(CASE WHEN r.surface = 'Obstacle' THEN 1 ELSE 0 END) AS obstacle_entries,
            ROUND(100.0 * SUM(CASE WHEN r.surface = 'Turf' THEN 1 ELSE 0 END) / COUNT(*), 1) AS turf_share_pct,
            ROUND(AVG(r.distance), 1) AS avg_distance_m,
            ROUND(AVG(CASE WHEN re.position = 1 THEN r.distance ELSE NULL END), 1) AS avg_winning_distance_m
        FROM race_entries re
        JOIN races r ON re.race_id = r.race_id
        JOIN pedigree p ON re.horse_name = p.horse_name
        WHERE p.sire_name IS NOT NULL AND p.sire_name != '' AND re.position < 90
        GROUP BY p.sire_name
        HAVING total_entries >= 50
        ORDER BY graded_wins DESC, total_entries DESC
    """, conn)
    df_sire_spec.to_csv(os.path.join(ANALYSIS_DIR, "sire_lineage_specialization.csv"), index=False, encoding="utf-8-sig")

    # Resumo de Ancestrais de Inbreeding (Crosses mais frequentes em 5 gerações)
    cross_counter = collections.Counter()
    cross_wins = collections.Counter()
    for h, m in meta.items():
        _, details = ped_dag.wright_inbreeding_coefficient(h)
        for d in details:
            anc_name = d.split(" (")[0]
            cross_counter[anc_name] += 1
            if m["graded_wins"] > 0:
                cross_wins[anc_name] += m["graded_wins"]

    inbreed_rows = []
    for anc, cnt in cross_counter.most_common(30):
        inbreed_rows.append({
            "common_ancestor": anc,
            "inbred_horses_count": cnt,
            "graded_wins_by_inbred_progeny": cross_wins[anc]
        })
    pd.DataFrame(inbreed_rows).to_csv(os.path.join(ANALYSIS_DIR, "top_inbreeding_ancestors.csv"), index=False, encoding="utf-8-sig")
    print(f"[CSV Analítico] 5 tabelas salvas em {ANALYSIS_DIR}")
    return df_meta, df_underdogs, df_g1_silver, df_sire_spec


def generate_network_visualizations(G_top150, G_dag, meta):
    """Gera duas visualizações estáticas de alta resolução dos grafos para o artigo e README."""
    os.makedirs(ASSETS_DIR, exist_ok=True)

    # 1. Visualização do Grafo de Competição (Top 55 Ícones por PageRank no Componente Principal)
    top_candidates = sorted(G_top150.nodes(), key=lambda n: G_top150.nodes[n].get("pagerank_score", 0), reverse=True)[:70]
    H_sub = G_top150.subgraph(top_candidates).copy()
    largest_cc = max(nx.weakly_connected_components(H_sub), key=len)
    top55_nodes = sorted(list(largest_cc), key=lambda n: G_top150.nodes[n].get("pagerank_score", 0), reverse=True)[:55]
    H_comp = G_top150.subgraph(top55_nodes).copy()

    fig, ax = plt.subplots(figsize=(15, 10.5), dpi=300)
    fig.patch.set_facecolor("#0f172a")
    ax.set_facecolor("#0f172a")

    pos = nx.spring_layout(H_comp.to_undirected(), k=1.05, iterations=200, seed=42, weight="weight")

    palette = {
        "Deep Impact": "#38bdf8",
        "Sunday Silence": "#f59e0b",
        "King Kamehameha": "#a855f7",
        "Stay Gold": "#ef4444",
        "Heart's Cry": "#10b981",
        "Lord Kanaloa": "#ec4899",
        "Other Sires": "#94a3b8",
    }

    node_colors = [palette.get(H_comp.nodes[n].get("sire_group", "Other Sires"), "#94a3b8") for n in H_comp.nodes()]
    node_sizes = [max(180, H_comp.nodes[n].get("pagerank_score", 3.0) * 95) for n in H_comp.nodes()]

    # Desenhar arestas mais fortes
    edges = [(u, v, d["weight"]) for u, v, d in H_comp.edges(data=True) if d.get("weight", 0) >= 1.4]
    if edges:
        max_w = max(w for _, _, w in edges)
        for u, v, w in edges:
            alpha = min(0.55, 0.12 + 0.43 * (w / max_w))
            nx.draw_networkx_edges(
                H_comp, pos, edgelist=[(u, v)],
                width=0.6 + 1.8 * (w / max_w),
                edge_color="#64748b", alpha=alpha,
                arrows=True, arrowsize=8, ax=ax,
                connectionstyle="arc3,rad=0.08"
            )

    nx.draw_networkx_nodes(
        H_comp, pos,
        node_size=node_sizes,
        node_color=node_colors,
        edgecolors="#f8fafc",
        linewidths=1.2,
        alpha=0.93,
        ax=ax
    )

    for n in H_comp.nodes():
        x, y = pos[n]
        pr_s = H_comp.nodes[n].get("pagerank_score", 0)
        fsize = 8.5 if pr_s >= 7.5 else 7.0
        ax.text(
            x, y + 0.032, n,
            fontsize=fsize, fontweight="bold", color="#f8fafc",
            ha="center", va="bottom",
            bbox=dict(boxstyle="round,pad=0.18", facecolor="#1e293b", edgecolor="none", alpha=0.75)
        )

    legend_handles = [mpatches.Patch(color=col, label=lbl) for lbl, col in palette.items()]
    ax.legend(
        handles=legend_handles, title="Paternal Sire Line (Bloodline)",
        loc="lower right", frameon=True, facecolor="#1e293b", edgecolor="#475569",
        labelcolor="#f8fafc", title_fontsize=10, fontsize=9
    )

    ax.set_title(
        "JRA Elite Competition Network — Top 60 Racehorses Sized by PageRank (d = 0.85, 2002–2025)",
        fontsize=14, fontweight="bold", color="#f8fafc", pad=16
    )
    ax.axis("off")
    plt.tight_layout()
    comp_plot_path = os.path.join(ASSETS_DIR, "network_competition_pagerank.png")
    plt.savefig(comp_plot_path, dpi=300, facecolor=fig.get_facecolor())
    plt.close()

    # 2. Visualização Hierárquica Multipolo do DAG de Linhagens Reais
    fig, ax = plt.subplots(figsize=(15, 9.5), dpi=300)
    fig.patch.set_facecolor("#ffffff")
    ax.set_facecolor("#f8fafc")

    # Selecionar os pilares dinásticos do turfe japonês moderno para visualização hierárquica clara
    tiers = {
        0: ["Nearco(ITY)", "Native Dancer(USA)"],
        1: ["Northern Dancer(CAN)", "Halo(USA)", "Hail to Reason(USA)", "Mr. Prospector(USA)"],
        2: ["Sunday Silence(USA)", "Kingmambo(USA)", "Roberto(USA)", "Tony Bin(IRE)", "Brian's Time(USA)"],
        3: ["Deep Impact", "Stay Gold", "Heart's Cry", "King Kamehameha", "Black Tide", "Daiwa Major", "Manhattan Cafe"],
        4: ["Orfevre", "Gold Ship", "Gentildonna", "Buena Vista", "Lord Kanaloa", "Duramente", "Kitasan Black", "Epiphaneia", "Maurice"],
        5: ["Almond Eye", "Satono Diamond", "Rey de Oro", "Suave Richard", "Cheval Grand", "Al Ain", "Blast Onepiece"]
    }

    H_lin = nx.DiGraph()
    pos_lin = {}
    node_tier = {}
    for t_idx, names in tiers.items():
        n_cols = len(names)
        for c_idx, name in enumerate(names):
            H_lin.add_node(name)
            node_tier[name] = t_idx
            x_coord = (c_idx + 0.5) / n_cols
            y_coord = 1.0 - (t_idx / 5.0)
            pos_lin[name] = (x_coord, y_coord)

    # Conectar arestas diretas e de 2ª geração presentes no banco/conhecimento genealógico
    known_links = [
        ("Nearco(ITY)", "Northern Dancer(CAN)"), ("Nearco(ITY)", "Halo(USA)"),
        ("Native Dancer(USA)", "Mr. Prospector(USA)"), ("Native Dancer(USA)", "Northern Dancer(CAN)"),
        ("Hail to Reason(USA)", "Halo(USA)"), ("Hail to Reason(USA)", "Roberto(USA)"),
        ("Halo(USA)", "Sunday Silence(USA)"), ("Mr. Prospector(USA)", "Kingmambo(USA)"),
        ("Roberto(USA)", "Brian's Time(USA)"),
        ("Sunday Silence(USA)", "Deep Impact"), ("Sunday Silence(USA)", "Stay Gold"),
        ("Sunday Silence(USA)", "Heart's Cry"), ("Sunday Silence(USA)", "Black Tide"),
        ("Sunday Silence(USA)", "Daiwa Major"), ("Sunday Silence(USA)", "Manhattan Cafe"),
        ("Kingmambo(USA)", "King Kamehameha"), ("Tony Bin(IRE)", "Heart's Cry"),
        ("Deep Impact", "Gentildonna"), ("Deep Impact", "Satono Diamond"), ("Deep Impact", "Al Ain"),
        ("Stay Gold", "Orfevre"), ("Stay Gold", "Gold Ship"),
        ("Heart's Cry", "Suave Richard"), ("Heart's Cry", "Cheval Grand"),
        ("Black Tide", "Kitasan Black"),
        ("King Kamehameha", "Lord Kanaloa"), ("King Kamehameha", "Duramente"), ("King Kamehameha", "Rey de Oro"),
        ("Lord Kanaloa", "Almond Eye"), ("Deep Impact", "Almond Eye"),
        ("Special Week", "Buena Vista"), ("Brian's Time(USA)", "Epiphaneia"),
        ("King Kamehameha", "Blast Onepiece"),
    ]
    for u, v in known_links:
        if u in H_lin and v in H_lin:
            H_lin.add_edge(u, v)

    tier_colors = {
        0: "#334155",
        1: "#0284c7",
        2: "#d97706",
        3: "#dc2626",
        4: "#7c3aed",
        5: "#059669"
    }
    colors_lin = [tier_colors[node_tier[n]] for n in H_lin.nodes()]

    nx.draw_networkx_edges(
        H_lin, pos_lin,
        edge_color="#64748b", width=1.6, alpha=0.65,
        arrows=True, arrowsize=14, ax=ax,
        connectionstyle="arc3,rad=0.05"
    )
    nx.draw_networkx_nodes(
        H_lin, pos_lin,
        node_size=1100, node_color=colors_lin,
        edgecolors="#ffffff", linewidths=2.0, ax=ax
    )

    for n, (x, y) in pos_lin.items():
        clean_lbl = n.replace("(USA)", "").replace("(ITY)", "").replace("(CAN)", "").replace("(IRE)", "")
        ax.text(
            x, y - 0.048, clean_lbl,
            fontsize=8.8, fontweight="bold", color="#0f172a",
            ha="center", va="top",
            bbox=dict(boxstyle="round,pad=0.22", facecolor="#ffffff", edgecolor="#cbd5e1", alpha=0.92)
        )

    tier_labels = [
        mpatches.Patch(color="#334155", label="Gen 0: Mid-20th Century Patriarchs"),
        mpatches.Patch(color="#0284c7", label="Gen 1: Global Foundation Sires"),
        mpatches.Patch(color="#d97706", label="Gen 2: JRA Imported Pillars (Sunday Silence / Kingmambo)"),
        mpatches.Patch(color="#dc2626", label="Gen 3: First Japanese-Bred Sire Dynasties"),
        mpatches.Patch(color="#7c3aed", label="Gen 4: Hall of Fame Champions & Sires"),
        mpatches.Patch(color="#059669", label="Gen 5: Modern Superstars (2020–2025)"),
    ]
    ax.legend(
        handles=tier_labels, loc="upper center", bbox_to_anchor=(0.5, 1.02),
        ncol=3, frameon=True, facecolor="#ffffff", edgecolor="#cbd5e1", fontsize=8.5
    )
    ax.set_title(
        "Directed Acyclic Graph (DAG) — 5-Generation Royal Bloodline Flow in JRA Graded Races",
        fontsize=14, fontweight="bold", color="#0f172a", pad=32
    )
    ax.set_ylim(-0.12, 1.12)
    ax.axis("off")
    plt.tight_layout()
    dag_plot_path = os.path.join(ASSETS_DIR, "network_lineage_dag.png")
    plt.savefig(dag_plot_path, dpi=300)
    plt.close()
    print(f"[Plots] Grafos visuais salvos em {comp_plot_path} e {dag_plot_path}")


def create_zenodo_metadata():
    """Cria os arquivos de manifesto (.zenodo.json) e guia do Gephi/Zenodo."""
    os.makedirs(ZENODO_DIR, exist_ok=True)
    zenodo_json = {
        "title": "JRA Graded Races (2002-2025) & JBIS 5-Generation Pedigree Dataset (Bilingual JA/EN + Graph Networks)",
        "upload_type": "dataset",
        "publication_date": "2026-10-26",
        "creators": [
            {
                "name": "Mendonça, Arthur De Oliveira",
                "affiliation": "Centro Federal de Educação Tecnológica de Minas Gerais (CEFET-MG)"
            }
        ],
        "description": (
            "Comprehensive relational and graph-ready dataset of Japanese Thoroughbred horse racing covering 24 years "
            "(2002-2025) of Japan Racing Association (JRA) Graded Races (G1, G2, G3) coupled with 5-generation genealogical "
            "pedigrees extracted from the Japan Bloodhorse Information System (JBIS). Includes both original Japanese and "
            "100% hybrid-AI-translated English editions (SQLite3 + UTF-8 CSVs + Gephi GEXF networks). "
            "Contains 3,216 Graded races, 33,409 race entries, 8,209 unique racehorses, 8,202 direct pedigrees, and "
            "504,074 5-generation pedigree tree nodes validated with zero broken foreign keys."
        ),
        "access_right": "open",
        "license": "CC-BY-4.0",
        "keywords": [
            "Horse Racing",
            "Japan Racing Association (JRA)",
            "JBIS",
            "Pedigree DAG",
            "Graph Theory",
            "PageRank",
            "Sports Analytics",
            "Thoroughbred Genetics",
            "Gephi",
            "Data Science"
        ],
        "notes": "Developed as an integrated project for Data Science and Algorithms & Data Structures II (AEDS 2) at CEFET-MG."
    }

    with open(os.path.join(ZENODO_DIR, ".zenodo.json"), "w", encoding="utf-8") as f:
        json.dump(zenodo_json, f, indent=2, ensure_ascii=False)

    gephi_guide = """# 📊 Guia Passo a Passo: Como Abrir e Estilizar os Grafos no Gephi e Publicar no Zenodo

## Parte 1 — Usando os Arquivos `.gexf` no Gephi (v0.10+)

Foram gerados **4 arquivos `.gexf`** na pasta `data/gephi/`, já com todos os atributos matemáticos pré-calculados:

| Arquivo | Nós | Descrição Recomendada |
| :--- | :---: | :--- |
| `competition_network_top150.gexf` | 150 | **Ideal para visualização limpa com nomes visíveis**. Contém os 150 maiores cavalos da história moderna da JRA ranqueados por PageRank. |
| `competition_network_top500.gexf` | 500 | **Ideal para Detecção de Comunidades (Modularidade / Louvain)** e análise macro de gerações (2002–2025). |
| `lineage_dag_elite.gexf` | ~1.800 | **Grafo Acíclico Direcionado (DAG) de Genealogia**. Conecta Ancestral $\\rightarrow$ Descendente para todos os campeões G1 e elites. |
| `jockey_horse_trainer_network.gexf` | ~350 | **Rede Bipartida/Tripartida** das maiores parcerias Jóquei $\\leftrightarrow$ Cavalo e Jóquei $\\leftrightarrow$ Treinador. |

### Passo a Passo no Gephi:
1. Abra o **Gephi** $\\rightarrow$ `File` $\\rightarrow$ `Open...` e selecione `data/gephi/competition_network_top150.gexf`.
2. Na janela de importação, mantenha **Graph Type: Directed** e clique em **OK**.
3. **Tamanho dos Nós (Node Size)**:
   - No painel esquerdo (**Appearance** $\\rightarrow$ **Nodes** $\\rightarrow$ ícone de círculos concêntricos *Size* $\\rightarrow$ **Ranking**):
   - Escolha o atributo **`pagerank_score`** (ou `earnings_m_yen` / `g1_wins`).
   - Defina `Min size = 12` e `Max size = 65` $\\rightarrow$ clique em **Apply**.
4. **Cor dos Nós (Node Color)**:
   - No painel **Appearance** $\\rightarrow$ **Nodes** $\\rightarrow$ ícone de paleta *Color* $\\rightarrow$ **Partition**:
   - Escolha **`sire_group`** (para colorir pela linhagem paterna: *Deep Impact*, *Sunday Silence*, *King Kamehameha*, *Stay Gold*, etc.) ou **`era`** (para colorir por época histórica).
   - Clique em **Apply**.
5. **Algoritmo de Layout (Disposição Espacial)**:
   - No painel inferior esquerdo (**Layout**), selecione **ForceAtlas 2**:
     - Marque `Prevent Overlap` (Evitar sobreposição) e `LinLog mode`.
     - Defina `Scaling = 15.0` e `Gravity = 1.0`.
     - Clique em **Run** por 10 a 15 segundos e depois em **Stop**.
6. **Exibir os Nomes dos Cavalos**:
   - Na barra inferior da aba *Overview*, clique no ícone **`T` (Show Node Labels)** e marque **Size: Node size** para que os nomes das lendas (*Equinox*, *Almond Eye*, *Orfevre*, *Deep Impact*) fiquem proporcionais ao seu PageRank!
7. **Exportar em Alta Resolução (PDF/PNG/SVG)**:
   - Vá na aba **Preview** (no topo), selecione o Preset **Default Curved**, marque `Show Labels`, clique em **Refresh** e depois em **Export: SVG/PDF/PNG** no canto inferior esquerdo.

---

## Parte 2 — Como Publicar o Dataset no Zenodo (DOI Oficial)

Você tem duas formas super rápidas de publicar no [Zenodo](https://zenodo.org/):

### Opção A: Integração Automática GitHub $\\leftrightarrow$ Zenodo (Recomendada)
1. Faça login em `https://zenodo.org` usando sua conta do **GitHub**.
2. No menu do seu perfil (canto superior direito), clique em **GitHub**.
3. Encontre o repositório `ImArthz/AEDS2_jra_analysis` e mude a chave para **ON**.
4. Como já deixamos o arquivo `zenodo/.zenodo.json` configurado, basta criar uma Release no GitHub (ou usar as tags automáticas) que o Zenodo gera automaticamente o **DOI oficial** para você citar no artigo!

### Opção B: Upload Manual Direto no Zenodo
1. Acesse `https://zenodo.org/uploads/new`.
2. Arraste os arquivos de `data/csv_en/`, `data/csv/`, `data/gephi/` e `data/sqlite/jra_graded_en.db`.
3. Copie o título, descrição e palavras-chave do arquivo `zenodo/.zenodo.json`, selecione **Dataset** e licença **CC-BY 4.0**, e clique em **Publish**.
"""
    with open(os.path.join(ZENODO_DIR, "GEPHI_AND_ZENODO_GUIDE.md"), "w", encoding="utf-8") as f:
        f.write(gephi_guide)
    print(f"[Zenodo] Metadados e Guia salvos em {ZENODO_DIR}")


def main():
    os.makedirs(GEPHI_DIR, exist_ok=True)
    os.makedirs(ANALYSIS_DIR, exist_ok=True)

    print("=" * 72)
    print("  ETAPA B: EXPORTAÇÃO GEPHI (.GEXF), ANÁLISE DE GRAFOS E PACOTE ZENODO")
    print("=" * 72)

    ped_dag, comp_graph, jh_graph, jt_graph = load_graphs_from_db(prefer_english=True)
    conn = sqlite3.connect(EN_DB_PATH)

    meta = build_horse_metadata(conn, ped_dag, comp_graph)

    G_top150 = export_competition_gexf(comp_graph, meta, top_n=150, filename="competition_network_top150.gexf", min_edge_weight=0.7)
    G_top500 = export_competition_gexf(comp_graph, meta, top_n=500, filename="competition_network_top500.gexf", min_edge_weight=1.0)
    G_dag = export_lineage_dag_gexf(ped_dag, meta, filename="lineage_dag_elite.gexf")
    G_bip = export_bipartite_gexf(jh_graph, jt_graph, meta, filename="jockey_horse_trainer_network.gexf")

    df_meta, df_underdogs, df_g1_silver, df_sire_spec = export_analytical_csvs(conn, ped_dag, meta)
    generate_network_visualizations(G_top150, G_dag, meta)
    create_zenodo_metadata()

    print("\n--- TOP 10 PAGERANK GERAL (2002-2025) ---")
    for _, r in df_meta.head(10).iterrows():
        print(f"  #{int(r['pagerank_rank']):2d} {r['horse_name']:<22s} | PR_Scaled={r['pagerank_scaled']:6.2f} | G1 Wins={int(r['g1_wins'])} | Graded Wins={int(r['graded_wins'])} | Sire={r['sire']}")

    print("\n--- TOP 5 'DIAMANTES AZARÕES' (0 Vitórias Graded, mas Altíssimo PageRank) ---")
    for _, r in df_underdogs.head(5).iterrows():
        print(f"  #{int(r['pagerank_rank']):3d} {r['horse_name']:<22s} | PR_Scaled={r['pagerank_scaled']:6.2f} | Pódios={int(r['graded_podiums'])} (G1 Pódios={int(r['g1_podiums'])}) | Sire={r['sire']}")

    print("\n--- TOP 5 'COLECIONADORES DE PRATA EM G1' (0 Vitórias G1, múltiplos pódios G1) ---")
    for _, r in df_g1_silver.head(5).iterrows():
        print(f"  #{int(r['pagerank_rank']):3d} {r['horse_name']:<22s} | PR_Scaled={r['pagerank_scaled']:6.2f} | G1 Pódios={int(r['g1_podiums'])} | Graded Wins={int(r['graded_wins'])} | Sire={r['sire']}")

    conn.close()
    print("\n[Etapa B] Concluída com sucesso!")


if __name__ == "__main__":
    main()
