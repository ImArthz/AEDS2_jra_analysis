"""
Módulo de Algoritmos e Estruturas de Dados 2 (AEDS 2)
Implementação de:
1. Grafo de Pedigree (DAG - Directed Acyclic Graph) com BFS, DFS e LCA (Lowest Common Ancestor)
2. Grafo de Competição (Confronto Direto) com Componentes Conexos, Dijkstra e Métricas de Centralidade
3. Análise de Hipóteses: Linhagem (Sire) vs Superfície (Turf/Dirt) e Distância
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
    Representa o Grafo Acíclico Direcionado (DAG) de Genealogia.
    Vértices: Cavalos.
    Arestas: Genitor -> Prole (ou Prole -> Genitor para busca de ancestrais).
    Implementação manual com Lista de Adjacência para fins didáticos de AEDS 2.
    """
    def __init__(self):
        # adj_ancestors[cavalo] = [pai, mae] (subir a árvore)
        self.adj_ancestors = collections.defaultdict(list)
        # adj_descendants[genitor] = [filhos] (descer a árvore)
        self.adj_descendants = collections.defaultdict(list)
        self.nodes = set()

    def add_relation(self, child, sire, dam=None):
        if not child: return
        self.nodes.add(child)
        if sire:
            self.nodes.add(sire)
            self.adj_ancestors[child].append((sire, "sire"))
            self.adj_descendants[sire].append((child, "sire"))
        if dam:
            self.nodes.add(dam)
            self.adj_ancestors[child].append((dam, "dam"))
            self.adj_descendants[dam].append((child, "dam"))

    def get_ancestors_dfs(self, start_horse):
        """Busca em Profundidade (DFS) para listar todos os ancestrais conhecidos."""
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
        """Busca em Largura (BFS) por gerações (distância em níveis)."""
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
        """
        Encontra o Menor Ancestral Comum (Lowest Common Ancestor / LCA)
        entre dois cavalos no grafo de pedigree.
        """
        # Distâncias de todos os ancestrais a partir de horse_a via BFS
        dist_a = {horse_a: 0}
        q_a = collections.deque([horse_a])
        while q_a:
            u = q_a.popleft()
            for p, _ in self.adj_ancestors.get(u, []):
                if p not in dist_a:
                    dist_a[p] = dist_a[u] + 1
                    q_a.append(p)

        # Distâncias de todos os ancestrais a partir de horse_b
        dist_b = {horse_b: 0}
        q_b = collections.deque([horse_b])
        while q_b:
            u = q_b.popleft()
            for p, _ in self.adj_ancestors.get(u, []):
                if p not in dist_b:
                    dist_b[p] = dist_b[u] + 1
                    q_b.append(p)

        # Interseção de ancestrais
        common = set(dist_a.keys()).intersection(set(dist_b.keys()))
        common.discard(horse_a)
        common.discard(horse_b)

        if not common:
            return None, float('inf')

        # O ancestral mais próximo minimiza a soma das distâncias
        lca = min(common, key=lambda anc: dist_a[anc] + dist_b[anc])
        return lca, (dist_a[lca], dist_b[lca])


class CompetitionGraph:
    """
    Grafo de Competição Esportiva (Confrontos Diretos no Top 3).
    - Não Direcionado com Pesos: número de pódios disputados juntos.
    - Direcionado: A -> B se A terminou à frente de B na corrida.
    """
    def __init__(self):
        self.adj_undirected = collections.defaultdict(lambda: collections.defaultdict(int))
        self.adj_directed = collections.defaultdict(lambda: collections.defaultdict(int))
        self.nodes = set()

    def add_race_podium(self, top_horses):
        """
        Recebe lista ordenada [(pos, horse_name), ...] do pódio de uma corrida.
        Adiciona arestas ponderadas entre todos os pares.
        """
        names = [h[1] for h in top_horses if h[1]]
        for n in names:
            self.nodes.add(n)

        # Confrontos de pares
        for i in range(len(top_horses)):
            pos_a, name_a = top_horses[i]
            for j in range(i + 1, len(top_horses)):
                pos_b, name_b = top_horses[j]
                if name_a == name_b:
                    continue

                # Grafo não direcionado (peso = corridas disputadas juntos)
                self.adj_undirected[name_a][name_b] += 1
                self.adj_undirected[name_b][name_a] += 1

                # Grafo direcionado (A venceu B)
                if pos_a < pos_b:
                    self.adj_directed[name_a][name_b] += 1
                elif pos_b < pos_a:
                    self.adj_directed[name_b][name_a] += 1

    def connected_components(self):
        """Identifica componentes conexos usando BFS manual."""
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
        """Grau de cada cavalo (total de adversários distintos enfrentados)."""
        deg = {u: len(self.adj_undirected[u]) for u in self.nodes}
        return sorted(deg.items(), key=lambda x: x[1], reverse=True)

    def dijkstra_shortest_path(self, start_node):
        """
        Algoritmo de Dijkstra para caminhos mínimos.
        Custo da aresta é inversamente proporcional ao peso (mais corridas juntos = mais perto).
        """
        dist = {n: float('inf') for n in self.nodes}
        prev = {n: None for n in self.nodes}
        dist[start_node] = 0
        heap = [(0, start_node)]

        while heap:
            d, u = heapq.heappop(heap)
            if d > dist[u]:
                continue

            for v, weight in self.adj_undirected[u].items():
                cost = 1.0 / weight
                if dist[u] + cost < dist[v]:
                    dist[v] = dist[u] + cost
                    prev[v] = u
                    heapq.heappush(heap, (dist[v], v))

        return dist, prev


def load_graphs_from_db():
    """Carrega os grafos a partir do banco SQLite gerado pelo scraper."""
    conn = get_connection()

    # 1. Carregar Pedigree
    ped_dag = PedigreeDAG()
    df_ped = pd.read_sql_query("SELECT horse_name, sire_name, dam_name FROM pedigree", conn)
    for _, row in df_ped.iterrows():
        ped_dag.add_relation(row["horse_name"], row["sire_name"], row["dam_name"])

    # 2. Carregar Competições
    comp_graph = CompetitionGraph()
    df_entries = pd.read_sql_query("""
    SELECT race_id, position, horse_name 
    FROM race_entries 
    WHERE horse_name != '' 
    ORDER BY race_id, position
    """, conn)
    
    races_grouped = df_entries.groupby("race_id")
    for race_id, group in races_grouped:
        top_list = [(row["position"], row["horse_name"]) for _, row in group.iterrows()]
        comp_graph.add_race_podium(top_list)

    conn.close()
    return ped_dag, comp_graph


def analyze_lineage_performance():
    """
    Cruza dados de Pedigree com Corridas:
    Analisa Vitórias e Pódios por Linhagem (Sire) x Superfície (Turf/Dirt) e Faixas de Distância.
    """
    conn = get_connection()
    query = """
    SELECT 
        p.sire_name AS sire,
        r.surface,
        r.distance,
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
        print("[Aviso] Dados insuficientes para análise cruzada no momento.")
        return None

    # Tabela dinâmica: Sire x Superfície
    sire_surface = pd.crosstab(
        df["sire"], df["surface"],
        margins=True, margins_name="Total"
    ).sort_values(by="Total", ascending=False)

    # Tabela dinâmica: Sire x Categoria de Distância
    sire_dist = pd.crosstab(
        df["sire"], df["distance_category"],
        margins=True, margins_name="Total"
    ).sort_values(by="Total", ascending=False)

    return sire_surface, sire_dist


if __name__ == "__main__":
    ped_dag, comp_graph = load_graphs_from_db()
    print(f"Pedigree DAG: {len(ped_dag.nodes)} nós carregados.")
    print(f"Grafo de Competição: {len(comp_graph.nodes)} cavalos carregados.")
    
    # Exibir maiores graus
    top_degrees = comp_graph.degree_centrality()[:10]
    print("\nTop 10 Cavalos por Rivais no Pódio (Grau):")
    for horse, deg in top_degrees:
        print(f"  {horse}: {deg} adversários")
