"""
Módulo de Algoritmos e Estruturas de Dados 2 (AEDS 2)
Versão 2: Grafos expandidos para corridas Graded completas e Pedigree 5 gerações.

Implementação:
1. Grafo de Pedigree (DAG 5 gerações) com BFS, DFS e LCA
2. Grafo de Competição (TODOS os participantes) com Dijkstra, Componentes Conexos, Centralidade
3. Grafo Bipartido Jóquei ↔ Cavalo
4. Grafo Jóquei ↔ Treinador (Colaborações)
5. Análise de Linhagem vs Superfície/Distância (ponderada por Grade)
"""

import collections
import heapq
import os
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from database import get_connection


class PedigreeDAG:
    """
    DAG de Genealogia com suporte a 5 gerações.
    Implementação com Lista de Adjacência (AEDS 2).
    """
    def __init__(self):
        self.adj_ancestors = collections.defaultdict(list)
        self.adj_descendants = collections.defaultdict(list)
        self.nodes = set()

    def add_relation(self, child, parent, relation_type="sire"):
        if not child or not parent:
            return
        self.nodes.add(child)
        self.nodes.add(parent)
        self.adj_ancestors[child].append((parent, relation_type))
        self.adj_descendants[parent].append((child, relation_type))

    def get_ancestors_dfs(self, start_horse):
        """DFS para listar todos os ancestrais conhecidos."""
        visited = set()
        order = []
        def dfs(u):
            visited.add(u)
            for parent, rel in self.adj_ancestors.get(u, []):
                if parent not in visited:
                    order.append((parent, rel))
                    dfs(parent)
        dfs(start_horse)
        return order

    def get_ancestors_bfs(self, start_horse):
        """BFS por gerações (distância em níveis)."""
        visited = {start_horse}
        queue = collections.deque([(start_horse, 0)])
        levels = collections.defaultdict(list)
        while queue:
            curr, dist = queue.popleft()
            if dist > 0:
                levels[dist].append(curr)
            for parent, rel in self.adj_ancestors.get(curr, []):
                if parent not in visited:
                    visited.add(parent)
                    queue.append((parent, dist + 1))
        return dict(levels)

    def find_lca(self, horse_a, horse_b):
        """LCA (Lowest Common Ancestor) entre dois cavalos."""
        dist_a = {horse_a: 0}
        q_a = collections.deque([horse_a])
        while q_a:
            u = q_a.popleft()
            for p, _ in self.adj_ancestors.get(u, []):
                if p not in dist_a:
                    dist_a[p] = dist_a[u] + 1
                    q_a.append(p)

        dist_b = {horse_b: 0}
        q_b = collections.deque([horse_b])
        while q_b:
            u = q_b.popleft()
            for p, _ in self.adj_ancestors.get(u, []):
                if p not in dist_b:
                    dist_b[p] = dist_b[u] + 1
                    q_b.append(p)

        common = set(dist_a.keys()).intersection(set(dist_b.keys()))
        common.discard(horse_a)
        common.discard(horse_b)

        if not common:
            return None, float('inf')

        lca = min(common, key=lambda anc: dist_a[anc] + dist_b[anc])
        return lca, (dist_a[lca], dist_b[lca])

    def inbreeding_coefficient(self, horse):
        """Calcula coeficiente de inbreeding simplificado (ancestrais repetidos em 5 gerações)."""
        ancestors = self.get_ancestors_bfs(horse)
        all_names = []
        for gen, names in ancestors.items():
            all_names.extend(names)
        if not all_names:
            return 0.0
        unique = len(set(all_names))
        total = len(all_names)
        return 1.0 - (unique / total) if total > 0 else 0.0


class CompetitionGraph:
    """
    Grafo de Competição Esportiva — TODOS os participantes.
    Ponderado por grade_weight (G1=1.0, G2=0.7, G3=0.5).
    """
    def __init__(self):
        self.adj_undirected = collections.defaultdict(lambda: collections.defaultdict(float))
        self.adj_directed = collections.defaultdict(lambda: collections.defaultdict(float))
        self.nodes = set()

    def add_race_result(self, participants, grade_weight=1.0):
        """Recebe lista [(pos, horse_name), ...] de TODOS os participantes."""
        names = [h[1] for h in participants if h[1]]
        for n in names:
            self.nodes.add(n)

        for i in range(len(participants)):
            pos_a, name_a = participants[i]
            for j in range(i + 1, len(participants)):
                pos_b, name_b = participants[j]
                if name_a == name_b:
                    continue
                # Peso = grade_weight (G1 pesa mais que G3)
                self.adj_undirected[name_a][name_b] += grade_weight
                self.adj_undirected[name_b][name_a] += grade_weight

                if pos_a < pos_b:
                    self.adj_directed[name_a][name_b] += grade_weight
                elif pos_b < pos_a:
                    self.adj_directed[name_b][name_a] += grade_weight

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
        """Grau de cada cavalo (adversários distintos enfrentados, ponderado)."""
        deg = {u: sum(self.adj_undirected[u].values()) for u in self.nodes}
        return sorted(deg.items(), key=lambda x: x[1], reverse=True)

    def dijkstra_shortest_path(self, start_node):
        """Dijkstra — custo inversamente proporcional ao peso."""
        dist = {n: float('inf') for n in self.nodes}
        prev = {n: None for n in self.nodes}
        dist[start_node] = 0
        heap = [(0, start_node)]
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
        """Confronto direto entre dois cavalos: vitórias de A sobre B e vice-versa."""
        a_wins = self.adj_directed[horse_a].get(horse_b, 0)
        b_wins = self.adj_directed[horse_b].get(horse_a, 0)
        meetings = self.adj_undirected[horse_a].get(horse_b, 0)
        return {"meetings": meetings, f"{horse_a}_wins": a_wins, f"{horse_b}_wins": b_wins}


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
        """Top N parcerias jóquei-cavalo por número de corridas (ponderado)."""
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
        """Top N duplas jóquei-treinador."""
        pairs = []
        for jockey in self.jockeys:
            for trainer, weight in self.adj[jockey].items():
                if trainer in self.trainers:
                    pairs.append((jockey, trainer, weight))
        return sorted(pairs, key=lambda x: x[2], reverse=True)[:n]


def load_graphs_from_db():
    """Carrega todos os grafos a partir do banco SQLite."""
    conn = get_connection()

    # 1. Pedigree DAG (5 gerações via pedigree_tree, fallback para pedigree)
    ped_dag = PedigreeDAG()
    
    try:
        df_tree = pd.read_sql_query("SELECT horse_name, ancestor_name, line FROM pedigree_tree", conn)
        for _, row in df_tree.iterrows():
            line = row["line"]
            rel_type = "sire" if line.endswith("S") or line == "S" else "dam"
            ped_dag.add_relation(row["horse_name"], row["ancestor_name"], rel_type)
    except Exception:
        # Fallback para tabela legada
        df_ped = pd.read_sql_query("SELECT horse_name, sire_name, dam_name FROM pedigree", conn)
        for _, row in df_ped.iterrows():
            ped_dag.add_relation(row["horse_name"], row["sire_name"], "sire")
            ped_dag.add_relation(row["horse_name"], row["dam_name"], "dam")

    # 2. Grafo de Competição (todos os participantes)
    comp_graph = CompetitionGraph()
    jh_graph = JockeyHorseGraph()
    jt_graph = JockeyTrainerGraph()

    df_entries = pd.read_sql_query("""
    SELECT re.race_id, re.position, re.horse_name, re.jockey, re.trainer, r.grade_weight
    FROM race_entries re
    JOIN races r ON re.race_id = r.race_id
    WHERE re.horse_name != '' AND re.position < 99
    ORDER BY re.race_id, re.position
    """, conn)
    
    races_grouped = df_entries.groupby("race_id")
    for race_id, group in races_grouped:
        grade_weight = group["grade_weight"].iloc[0] if "grade_weight" in group.columns else 1.0
        
        participants = [(row["position"], row["horse_name"]) for _, row in group.iterrows()]
        comp_graph.add_race_result(participants, grade_weight)

        for _, row in group.iterrows():
            jh_graph.add_ride(row["jockey"], row["horse_name"], grade_weight)
            jt_graph.add_collaboration(row["jockey"], row.get("trainer", ""), grade_weight)

    conn.close()
    return ped_dag, comp_graph, jh_graph, jt_graph


def analyze_lineage_performance():
    """Cruza Pedigree com Corridas: Sire x Superfície x Distância (ponderado por Grade)."""
    conn = get_connection()
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
        print("[Aviso] Dados insuficientes para análise cruzada.")
        return None

    sire_surface = pd.crosstab(
        df["sire"], df["surface"],
        margins=True, margins_name="Total"
    ).sort_values(by="Total", ascending=False)

    sire_dist = pd.crosstab(
        df["sire"], df["distance_category"],
        margins=True, margins_name="Total"
    ).sort_values(by="Total", ascending=False)

    return sire_surface, sire_dist


if __name__ == "__main__":
    ped_dag, comp_graph, jh_graph, jt_graph = load_graphs_from_db()
    
    print(f"Pedigree DAG: {len(ped_dag.nodes)} nós")
    print(f"Competição:   {len(comp_graph.nodes)} cavalos")
    print(f"Jóquei↔Cavalo: {len(jh_graph.jockeys)} jóqueis, {len(jh_graph.horses)} cavalos")
    print(f"Jóquei↔Treinador: {len(jt_graph.jockeys)} jóqueis, {len(jt_graph.trainers)} treinadores")
    
    print("\nTop 10 Cavalos por Grau de Rivalidade:")
    for horse, deg in comp_graph.degree_centrality()[:10]:
        print(f"  {horse}: {deg:.1f}")

    print("\nTop 5 Parcerias Jóquei-Cavalo:")
    for j, h, w in jh_graph.top_partnerships(5):
        print(f"  {j} + {h}: {w:.1f}")

    print("\nTop 5 Duplas Jóquei-Treinador:")
    for j, t, w in jt_graph.top_teams(5):
        print(f"  {j} + {t}: {w:.1f}")
