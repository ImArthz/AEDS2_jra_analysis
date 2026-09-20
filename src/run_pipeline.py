"""
Pipeline Principal — Versão 3
Executa: Extração JRA -> Extração JBIS -> Validação -> Tradução -> CSVs -> Análise.
"""

import argparse
import sys
import os

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from scraper_jra import scrape_year
from scraper_pedigree import scrape_missing_pedigrees
from database import init_db, export_to_csv
from graph_analysis import load_graphs_from_db, analyze_lineage_performance
from validate_data import validate_all
from translate_db import create_english_db

def main():
    parser = argparse.ArgumentParser(description="Pipeline JRA Graded + JBIS Pedigree 5-Gen (AEDS 2)")
    parser.add_argument("--start-year", type=int, default=2002)
    parser.add_argument("--end-year", type=int, default=2025)
    parser.add_argument("--grades", type=str, default="g1,g2,g3")
    parser.add_argument("--jra-delay", type=float, default=1.5)
    parser.add_argument("--jbis-delay", type=float, default=2.0)
    parser.add_argument("--skip-races", action="store_true")
    parser.add_argument("--skip-pedigree", action="store_true")
    parser.add_argument("--skip-validation", action="store_true")
    parser.add_argument("--skip-translation", action="store_true")
    parser.add_argument("--analyze", action="store_true")
    parser.add_argument("--test", action="store_true", help="Modo teste: ano 2005, limite de cavalos")
    parser.add_argument("--max-horses", type=int, default=None)

    args = parser.parse_args()
    init_db()

    start_y = 2005 if args.test else args.start_year
    end_y = 2005 if args.test else args.end_year

    # 1. Scraper JRA
    if not args.skip_races:
        print(f"\n[Etapa 1] Coletando corridas {args.grades.upper()} ({start_y}–{end_y})...")
        for y in range(start_y, end_y + 1):
            scrape_year(y, source='graded')

    # 2. Scraper JBIS
    if not args.skip_pedigree:
        print("\n[Etapa 2] Coletando JBIS (Pedigree + Perfil)...")
        max_h = 20 if args.test and args.max_horses is None else args.max_horses
        scrape_missing_pedigrees(delay=args.jbis_delay, max_horses=max_h)
        export_to_csv()

    # 3. Validação
    if not args.skip_validation:
        print("\n[Etapa 3] Validando Integridade dos Dados...")
        passed, _ = validate_all(verbose=True)
        if not passed:
            print("⚠️ AVISO: Falhas na validação! Verifique o relatório acima.")

    # 4. Tradução JP -> EN
    if not args.skip_translation:
        print("\n[Etapa 4] Traduzindo Banco para Inglês...")
        create_english_db()

    # 5. Análise de Grafos
    if args.analyze or args.test:
        print("\n[Etapa 5] Análise de Grafos (AEDS 2)...")
        ped_dag, comp_graph, jh_graph, jt_graph = load_graphs_from_db()

        print(f"  Pedigree DAG:     {len(ped_dag.nodes)} nós")
        print(f"  Competição:       {len(comp_graph.nodes)} cavalos")
        print(f"  Jóquei↔Cavalo:    {len(jh_graph.jockeys)} jóqueis × {len(jh_graph.horses)} cavalos")
        
        if comp_graph.nodes:
            print("\n  Top 5 Cavalos (Centralidade):")
            for horse, deg in comp_graph.degree_centrality()[:5]:
                print(f"    {horse}: {deg:.1f}")

    print(f"\n{'='*60}\n  Pipeline concluído!\n{'='*60}\n")

if __name__ == "__main__":
    main()
