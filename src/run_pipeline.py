"""
Pipeline Principal de Execução do Projeto
Permite rodar o scraper de corridas, o scraper de genealogia e a análise de grafos de forma unificada.
"""

import argparse
import sys

# Configura codificação UTF-8 para stdout e stderr no Windows
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from scraper_jra import scrape_jra_period
from scraper_pedigree import scrape_missing_pedigrees
from database import init_db, export_to_csv
from graph_analysis import load_graphs_from_db, analyze_lineage_performance

def main():
    parser = argparse.ArgumentParser(description="Pipeline JRA G1 + JBIS Pedigree (AEDS 2)")
    parser.add_argument("--start-year", type=int, default=2002, help="Ano inicial (JRA replay disponível a partir de 2002)")
    parser.add_argument("--end-year", type=int, default=2020, help="Ano final (recomendado 2020)")
    parser.add_argument("--delay", type=float, default=2.0, help="Intervalo de segurança entre requisições em segundos (padrão: 2.0s)")
    parser.add_argument("--skip-races", action="store_true", help="Pular extração de corridas e ir direto para o pedigree")
    parser.add_argument("--skip-pedigree", action="store_true", help="Pular extração de genealogia")
    parser.add_argument("--analyze", action="store_true", help="Executar análise de grafos e estatísticas ao final")
    parser.add_argument("--test", action="store_true", help="Modo teste rápido: roda apenas o ano de 2005 com delay de 2.0s")

    args = parser.parse_args()

    # Inicialização do banco de dados
    init_db()

    start_y = 2005 if args.test else args.start_year
    end_y = 2005 if args.test else args.end_year

    # 1. Scraper JRA
    if not args.skip_races:
        print(f"\n[Etapa 1] Coletando corridas JRA G1 ({start_y} a {end_y})...")
        scrape_jra_period(start_year=start_y, end_year=end_y, delay=args.delay)

    # 2. Scraper JBIS (Pedigree)
    if not args.skip_pedigree:
        print("\n[Etapa 2] Coletando linhagem genealógica (Pedigree) no JBIS...")
        scrape_missing_pedigrees(delay=args.delay)

    # 3. Exportação para CSV
    print("\n[Etapa 3] Atualizando arquivos CSV...")
    export_to_csv()

    # 4. Análise de Grafos (AEDS 2)
    if args.analyze or args.test:
        print("\n[Etapa 4] Executando Análise de Grafos (AEDS 2)...")
        ped_dag, comp_graph = load_graphs_from_db()
        print(f"  -> Grafo de Pedigree: {len(ped_dag.nodes)} cavalos e ancestrais mapeados.")
        print(f"  -> Grafo de Competição: {len(comp_graph.nodes)} competidores conectados.")

        components = comp_graph.connected_components()
        print(f"  -> Componentes Conexos no grafo de rivais: {len(components)}")
        if components:
            print(f"     Maior componente possui {len(components[0])} cavalos conectados.")

        # Teste de LCA se houver pelo menos 2 cavalos
        nodes_list = list(ped_dag.nodes)[:10]
        if len(nodes_list) >= 2:
            h1, h2 = nodes_list[0], nodes_list[1]
            lca, dists = ped_dag.find_lca(h1, h2)
            print(f"\n[AEDS 2 - Demonstração LCA] Menor Ancestral Comum entre '{h1}' e '{h2}':")
            if lca:
                print(f"  Ancestral comum: {lca} (distâncias geracionais: {dists})")
            else:
                print("  Nenhum ancestral comum direto no subgrafo atual.")

        res = analyze_lineage_performance()
        if res:
            sire_surface, sire_dist = res
            print("\n--- Desempenho por Linhagem (Sire) x Superfície (Top 5) ---")
            print(sire_surface.head(6))

    print("\n=======================================================")
    print("  Pipeline concluído com sucesso!")
    print("=======================================================\n")

if __name__ == "__main__":
    main()
