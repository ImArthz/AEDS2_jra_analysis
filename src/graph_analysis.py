"""
Módulo de Algoritmos e Estruturas de Dados 2 (AEDS 2)
Versão 3: Grafos expandidos sobre a base 100% traduzida (Inglês) e higienizada.

Implementação:
1. Grafo de Pedigree (DAG 5 gerações real: pai/mãe -> filho por nível) com BFS, DFS, LCA e Coeficiente de Wright (Inbreeding F_X)
2. Grafo de Competição (TODOS os participantes) com PageRank (d=0.85), Dijkstra, Componentes Conexos e Centralidade
3. Grafo Bipartido Jóquei ↔ Cavalo
4. Grafo Jóquei ↔ Treinador (Colaborações)
5. Análise de Linhagem vs Superfície/Distância (ponderada por Grade)
"""

import collections
import heapq
import os
import sys
import sqlite3
import pandas as pd
import networkx as nx

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
EN_DB_PATH = os.path.join(BASE_DIR, "data", "sqlite", "jra_graded_en.db")
JA_DB_PATH = os.path.join(BASE_DIR, "data", "sqlite", "jra_graded.db")


def get_analysis_connection(prefer_english=True):
    db_path = EN_DB_PATH if (prefer_english and os.path.exists(EN_DB_PATH)) else JA_DB_PATH
    conn = sqlite3.connect(db_path)
    return conn


class PedigreeDAG:
    """
    DAG de Genealogia com suporte real a 5 gerações.
    Implementação com Lista de Adjacência (AEDS 2).
    """
    def __init__(self):
        self.adj_ancestors = collections.defaultdict(list)     # child -> [(parent, rel_type)]
        self.adj_descendants = collections.defaultdict(list)   # parent -> [(child, rel_type)]
        self.horse_trees = collections.defaultdict(dict)       # horse_name -> {line: ancestor_name}
        self.nodes = set()

    def add_relation(self, child, parent, relation_type="sire"):
        if not child or not parent or child == parent:
            return
        self.nodes.add(child)
        self.nodes.add(parent)
        edge = (parent, relation_type)
        if edge not in self.adj_ancestors[child]:
            self.adj_ancestors[child].append(edge)
        desc_edge = (child, relation_type)
        if desc_edge not in self.adj_descendants[parent]:
            self.adj_descendants[parent].append(desc_edge)

    def get_ancestors_dfs(self, start_horse, max_depth=5):
        """DFS limitado a max_depth gerações para listar todos os ancestrais conhecidos."""
        visited = set()
        order = []
        def dfs(u, depth):
            if depth >= max_depth:
                return
            visited.add(u)
            for parent, rel in self.adj_ancestors.get(u, []):
                order.append((parent, rel, depth + 1))
                if parent not in visited:
                    dfs(parent, depth + 1)
        dfs(start_horse, 0)
        return order

    def get_ancestors_bfs(self, start_horse, max_depth=5):
        """BFS por gerações (distância mínima em níveis até 5 gerações)."""
        visited = {start_horse}
        queue = collections.deque([(start_horse, 0)])
        levels = collections.defaultdict(list)
        while queue:
            curr, dist = queue.popleft()
            if dist > 0:
                levels[dist].append(curr)
            if dist >= max_depth:
                continue
            for parent, rel in self.adj_ancestors.get(curr, []):
                if parent not in visited:
                    visited.add(parent)
                    queue.append((parent, dist + 1))
        return dict(levels)

    def find_lca(self, horse_a, horse_b, max_depth=5):
        """LCA (Lowest Common Ancestor) entre dois cavalos até max_depth gerações."""
        def bfs_dists(start):
            dists = {start: 0}
            q = collections.deque([start])
            while q:
                u = q.popleft()
                if dists[u] >= max_depth:
                    continue
                for p, _ in self.adj_ancestors.get(u, []):
                    if p not in dists:
                        dists[p] = dists[u] + 1
                        q.append(p)
            return dists

        dist_a = bfs_dists(horse_a)
        dist_b = bfs_dists(horse_b)

        common = set(dist_a.keys()).intersection(set(dist_b.keys()))
        common.discard(horse_a)
        common.discard(horse_b)

        if not common:
            return None, (float('inf'), float('inf'))

        lca = min(common, key=lambda anc: (dist_a[anc] + dist_b[anc], max(dist_a[anc], dist_b[anc]), anc))
        return lca, (dist_a[lca], dist_b[lca])

    def wright_inbreeding_coefficient(self, horse):
        """
        Calcula o Coeficiente de Endogamia de Wright (F_X) exato em 5 gerações
        usando os caminhos paternos ('S...') e maternos ('D...') de pedigree_tree.
        F_X = sum((1/2)^(n_S + n_D - 1)) para cada par mínimo de caminhos (line_S, line_D)
        que convergem no mesmo ancestral comum (ex.: 3x4 -> (1/2)^6 = 1.5625%).
        """
        tree = self.horse_trees.get(horse, {})
        if not tree:
            return 0.0, []

        sire_side = {line: anc for line, anc in tree.items() if line.startswith("S") and anc}
        dam_side = {line: anc for line, anc in tree.items() if line.startswith("D") and anc}

        # Encontrar pares (line_s, line_d) com mesmo ancestral
        matching_pairs = []
        for ls, anc_s in sire_side.items():
            for ld, anc_d in dam_side.items():
                if anc_s == anc_d:
                    matching_pairs.append((ls, ld, anc_s))

        # Filtrar apenas cruzamentos minimais (não contar os pais de um ancestral já pareado no mesmo ramo)
        minimal_pairs = []
        for ls, ld, anc in matching_pairs:
            is_redundant = False
            for ls2, ld2, _ in matching_pairs:
                if (ls != ls2 or ld != ld2) and ls.startswith(ls2) and ld.startswith(ld2):
                    is_redundant = True
                    break
            if not is_redundant:
                minimal_pairs.append((ls, ld, anc))

        f_x = 0.0
        cross_details = []
        for ls, ld, anc in minimal_pairs:
            n_s = len(ls)
            n_d = len(ld)
            contrib = (0.5) ** (n_s + n_d - 1)
            f_x += contrib
            cross_details.append(f"{anc} ({n_s}x{n_d}: {contrib*100:.2f}%)")

        return f_x, cross_details


class CompetitionGraph:
    """
    Grafo de Competição Esportiva — TODOS os participantes.
    Ponderado por grade_weight (G1=1.0, G2=0.7, G3=0.5).
    No grafo direcionado de PageRank, se o cavalo A vence o cavalo B (pos_A < pos_B),
    cria-se a aresta direcionada B -> A (B transfere prestígio para A).
    """
    def __init__(self):
        self.adj_undirected = collections.defaultdict(lambda: collections.defaultdict(float))
        self.adj_wins = collections.defaultdict(lambda: collections.defaultdict(float))      # winner -> loser
        self.adj_prestige = collections.defaultdict(lambda: collections.defaultdict(float))  # loser -> winner (PageRank)
        self.nodes = set()

    def add_race_result(self, participants, grade_weight=1.0):
        """Recebe lista [(pos, horse_name), ...] de TODOS os participantes válidos."""
        valid = [(pos, name) for pos, name in participants if name and pos and pos < 90]
        for _, n in valid:
            self.nodes.add(n)

        n_runners = len(valid)
        for i in range(n_runners):
            pos_a, name_a = valid[i]
            for j in range(i + 1, n_runners):
                pos_b, name_b = valid[j]
                if name_a == name_b:
                    continue
                self.adj_undirected[name_a][name_b] += grade_weight
                self.adj_undirected[name_b][name_a] += grade_weight

                if pos_a < pos_b:
                    self.adj_wins[name_a][name_b] += grade_weight
                    self.adj_prestige[name_b][name_a] += grade_weight
                elif pos_b < pos_a:
                    self.adj_wins[name_b][name_a] += grade_weight
                    self.adj_prestige[name_a][name_b] += grade_weight

    def connected_components(self):
        """Componentes Conexos via BFS manual."""
        visited = set()
        components = []
        for node in self.nodes:
            if node not in visited:
                comp = []
                queue = collections.deque([node])
                visited.add(node)
                while queue:
                    u = queue.popleft()
                    comp.append(u)
                    for neighbor in self.adj_undirected[u]:
                        if neighbor not in visited:
                            visited.add(neighbor)
                            queue.append(neighbor)
                components.append(comp)
        return sorted(components, key=len, reverse=True)

    def degree_centrality(self):
        """Grau ponderado de cada cavalo (adversários enfrentados * peso da prova)."""
        deg = {u: sum(self.adj_undirected[u].values()) for u in self.nodes}
        return sorted(deg.items(), key=lambda x: x[1], reverse=True)

    def compute_pagerank(self, damping=0.85, max_iter=100, tol=1e-7):
        """
        Calcula o PageRank Esportivo (d=0.85) via Power Iteration sobre o grafo ponderado
        de transferência de prestígio (loser -> winner).
        """
        nodes = list(self.nodes)
        n = len(nodes)
        if n == 0:
            return []

        out_weight = {}
        for u in nodes:
            out_weight[u] = sum(self.adj_prestige[u].values())

        pr = {u: 1.0 / n for u in nodes}
        base = (1.0 - damping) / n

        for _ in range(max_iter):
            new_pr = {u: base for u in nodes}
            dangling_mass = sum(pr[u] for u in nodes if out_weight[u] == 0.0)
            dangling_contrib = damping * dangling_mass / n
            if dangling_contrib > 0:
                for u in nodes:
                    new_pr[u] += dangling_contrib

            for loser in nodes:
                w_out = out_weight[loser]
                if w_out > 0.0:
                    factor = damping * pr[loser] / w_out
                    for winner, w in self.adj_prestige[loser].items():
                        new_pr[winner] += factor * w

            diff = sum(abs(new_pr[u] - pr[u]) for u in nodes)
            pr = new_pr
            if diff < tol:
                break

        return sorted(pr.items(), key=lambda x: x[1], reverse=True)

    def dijkstra_shortest_path(self, start_node):
        """Dijkstra — custo inversamente proporcional ao peso de enfrentamento."""
        dist = {n: float('inf') for n in self.nodes}
        prev = {n: None for n in self.nodes}
        if start_node not in self.nodes:
            return dist, prev
        dist[start_node] = 0.0
        heap = [(0.0, start_node)]
        while heap:
            d, u = heapq.heappop(heap)
            if d > dist[u]:
                continue
            for v, weight in self.adj_undirected[u].items():
                cost = 1.0 / weight if weight > 0 else float('inf')
                if dist[u] + cost < dist[v]:
                    dist[v] = dist[u] + cost
                    prev[v] = u
                    heapq.heappush(heap, (dist[v], v))
        return dist, prev

    def head_to_head(self, horse_a, horse_b):
        """Confronto direto entre dois cavalos: vitórias ponderadas de A sobre B e vice-versa."""
        a_wins = self.adj_wins[horse_a].get(horse_b, 0.0)
        b_wins = self.adj_wins[horse_b].get(horse_a, 0.0)
        meetings = self.adj_undirected[horse_a].get(horse_b, 0.0)
        return {"meetings_weighted": meetings, f"{horse_a}_wins": a_wins, f"{horse_b}_wins": b_wins}


class JockeyHorseGraph:
    """Grafo Bipartido Jóquei ↔ Cavalo."""
    def __init__(self):
        self.adj = collections.defaultdict(lambda: collections.defaultdict(float))
        self.jockeys = set()
        self.horses = set()

    def add_ride(self, jockey, horse, grade_weight=1.0):
        if not jockey or not horse:
            return
        self.jockeys.add(jockey)
        self.horses.add(horse)
        self.adj[jockey][horse] += grade_weight
        self.adj[horse][jockey] += grade_weight

    def top_partnerships(self, n=10):
        pairs = []
        for jockey in self.jockeys:
            for horse, weight in self.adj[jockey].items():
                if horse in self.horses:
                    pairs.append((jockey, horse, weight))
        return sorted(pairs, key=lambda x: x[2], reverse=True)[:n]


class JockeyTrainerGraph:
    """Grafo Jóquei ↔ Treinador (colaborações ponderadas)."""
    def __init__(self):
        self.adj = collections.defaultdict(lambda: collections.defaultdict(float))
        self.jockeys = set()
        self.trainers = set()

    def add_collaboration(self, jockey, trainer, grade_weight=1.0):
        if not jockey or not trainer:
            return
        self.jockeys.add(jockey)
        self.trainers.add(trainer)
        self.adj[jockey][trainer] += grade_weight
        self.adj[trainer][jockey] += grade_weight

    def top_teams(self, n=10):
        pairs = []
        for jockey in self.jockeys:
            for trainer, weight in self.adj[jockey].items():
                if trainer in self.trainers:
                    pairs.append((jockey, trainer, weight))
        return sorted(pairs, key=lambda x: x[2], reverse=True)[:n]


def load_graphs_from_db(prefer_english=True):
    """Carrega todos os grafos a partir do banco SQLite (Inglês por padrão) em O(N) via cursores nativos."""
    conn = get_analysis_connection(prefer_english=prefer_english)
    cur = conn.cursor()

    # 1. Pedigree DAG (5 gerações conectando pai/mãe ao filho real em cada geração)
    ped_dag = PedigreeDAG()
    cur.execute("SELECT horse_name, ancestor_name, line FROM pedigree_tree")
    for h_name, anc_name, line in cur.fetchall():
        ped_dag.horse_trees[h_name][line] = anc_name

    for h_name, tree in ped_dag.horse_trees.items():
        for line, anc_name in tree.items():
            rel_type = "sire" if line.endswith("S") else "dam"
            if len(line) == 1:
                ped_dag.add_relation(h_name, anc_name, rel_type)
            else:
                child_name = tree.get(line[:-1])
                if child_name:
                    ped_dag.add_relation(child_name, anc_name, rel_type)

    # 2. Grafo de Competição + Bipartidos
    comp_graph = CompetitionGraph()
    jh_graph = JockeyHorseGraph()
    jt_graph = JockeyTrainerGraph()

    cur.execute("""
    SELECT re.race_id, re.position, re.horse_name, re.jockey, re.trainer, r.grade_weight
    FROM race_entries re
    JOIN races r ON re.race_id = r.race_id
    WHERE re.horse_name != '' AND re.position < 99
    ORDER BY re.race_id, re.position
    """)

    races_map = collections.defaultdict(list)
    race_weights = {}
    for race_id, pos, h_name, jockey, trainer, gw in cur.fetchall():
        gw_val = float(gw) if gw is not None else 1.0
        race_weights[race_id] = gw_val
        races_map[race_id].append((int(pos), h_name))
        jh_graph.add_ride(jockey, h_name, gw_val)
        jt_graph.add_collaboration(jockey, trainer, gw_val)

    for race_id, participants in races_map.items():
        comp_graph.add_race_result(participants, race_weights[race_id])

    conn.close()
    return ped_dag, comp_graph, jh_graph, jt_graph


def analyze_lineage_performance(prefer_english=True):
    """Cruza Pedigree com Corridas: Sire x Superfície x Distância (ponderado por Grade)."""
    conn = get_analysis_connection(prefer_english=prefer_english)
    query = """
    SELECT 
        p.sire_name AS sire,
        r.surface,
        r.distance,
        r.grade,
        r.grade_weight,
        CASE 
            WHEN r.distance <= 1400 THEN 'Sprint (<=1400m)'
            WHEN r.distance <= 1600 THEN 'Mile (1600m)'
            WHEN r.distance <= 2200 THEN 'Intermediate (1800-2200m)'
            ELSE 'Long (>=2400m)'
        END AS distance_category,
        re.position
    FROM race_entries re
    JOIN races r ON re.race_id = r.race_id
    JOIN pedigree p ON re.horse_name = p.horse_name
    WHERE p.sire_name IS NOT NULL AND p.sire_name != ''
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    if df.empty:
        return None

    sire_surface = pd.crosstab(df["sire"], df["surface"], margins=True, margins_name="Total").sort_values(by="Total", ascending=False)
    sire_dist = pd.crosstab(df["sire"], df["distance_category"], margins=True, margins_name="Total").sort_values(by="Total", ascending=False)
    return sire_surface, sire_dist


if __name__ == "__main__":
    ped_dag, comp_graph, jh_graph, jt_graph = load_graphs_from_db(prefer_english=True)

    print(f"Pedigree DAG (5-Gen Real): {len(ped_dag.nodes):,} nós únicos")
    print(f"Grafo de Competição:       {len(comp_graph.nodes):,} cavalos")
    comps = comp_graph.connected_components()
    print(f"Componentes Conexos:       {len(comps)} (Maior componente: {len(comps[0]):,} cavalos = {len(comps[0])/len(comp_graph.nodes)*100:.2f}%)")
    print(f"Jóquei ↔ Cavalo:           {len(jh_graph.jockeys):,} jóqueis × {len(jh_graph.horses):,} cavalos")
    print(f"Jóquei ↔ Treinador:        {len(jt_graph.jockeys):,} jóqueis × {len(jt_graph.trainers):,} treinadores")

    print("\nTop 10 Cavalos por PageRank Esportivo (d=0.85):")
    for rank, (horse, pr_score) in enumerate(comp_graph.compute_pagerank()[:10], 1):
        print(f"  {rank:2d}. {horse:<24s} | PR = {pr_score:.6f}")

    print("\nTop 10 Cavalos por Grau Ponderado de Rivalidade:")
    for rank, (horse, deg) in enumerate(comp_graph.degree_centrality()[:10], 1):
        print(f"  {rank:2d}. {horse:<24s} | Grau = {deg:.1f}")

    print("\nExemplos de LCA (Lowest Common Ancestor) e Inbreeding (Wright F_X):")
    for ha, hb in [("Almond Eye", "Gentildonna"), ("Orfevre", "Gold Ship"), ("Deep Impact", "Black Tide"), ("Kitasan Black", "Satono Diamond")]:
        lca, dists = ped_dag.find_lca(ha, hb)
        print(f"  LCA({ha}, {hb}) -> {lca} (distâncias: {dists[0]} e {dists[1]} gerações)")

    for h in ["Almond Eye", "Orfevre", "Gentildonna", "Gold Ship", "Kitasan Black", "Deep Impact"]:
        fx, details = ped_dag.wright_inbreeding_coefficient(h)
        print(f"  Inbreeding({h:<14s}) -> F_X = {fx*100:.2f}% | {', '.join(details[:3]) if details else 'Outcross (0%)'}")

    print("\nTop 5 Parcerias Jóquei-Cavalo:")
    for j, h, w in jh_graph.top_partnerships(5):
        print(f"  {j} + {h}: {w:.1f}")

    print("\nTop 5 Duplas Jóquei-Treinador:")
    for j, t, w in jt_graph.top_teams(5):
        print(f"  {j} + {t}: {w:.1f}")
