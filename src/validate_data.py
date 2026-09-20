"""
Módulo de Validação de Dados Extraídos
Verifica integridade, completude e consistência dos dados ANTES da tradução.
Gera relatório de validação com alertas e estatísticas.
"""

import sys
import os
import pandas as pd
from database import get_connection

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')


def validate_all(verbose=True):
    """Executa todas as validações e retorna (passed: bool, report: str)."""
    conn = get_connection()
    issues = []
    stats = []
    
    # ================================================================
    # 1. CONTAGEM DE REGISTROS
    # ================================================================
    tables = {
        'races': 'Corridas',
        'race_entries': 'Entradas (participantes)',
        'horses': 'Cavalos únicos',
        'pedigree': 'Pedigree (legado 2-gen)',
        'pedigree_tree': 'Pedigree (árvore 5-gen)',
    }
    
    counts = {}
    for table, label in tables.items():
        try:
            df = pd.read_sql_query(f"SELECT COUNT(*) as n FROM {table}", conn)
            counts[table] = df['n'].iloc[0]
            stats.append(f"  {label}: {counts[table]:,} registros")
        except Exception:
            counts[table] = 0
            stats.append(f"  {label}: TABELA NÃO EXISTE")
            issues.append(f"[ERRO] Tabela '{table}' não encontrada no banco.")
    
    # Alertas de contagem
    if counts['races'] == 0:
        issues.append("[CRÍTICO] Nenhuma corrida encontrada. Pipeline de scraping não executado?")
    if counts['race_entries'] == 0:
        issues.append("[CRÍTICO] Nenhuma entrada de participante encontrada.")
    if counts['horses'] == 0:
        issues.append("[CRÍTICO] Nenhum cavalo registrado.")
    
    # ================================================================
    # 2. INTEGRIDADE REFERENCIAL
    # ================================================================
    # race_entries deve referenciar race_ids existentes
    try:
        orphan_entries = pd.read_sql_query("""
        SELECT COUNT(*) as n FROM race_entries 
        WHERE race_id NOT IN (SELECT race_id FROM races)
        """, conn)
        n_orphans = orphan_entries['n'].iloc[0]
        if n_orphans > 0:
            issues.append(f"[ERRO] {n_orphans} entradas órfãs (race_id não existe em races).")
        else:
            stats.append("  Integridade referencial race_entries → races: ✓")
    except Exception as e:
        issues.append(f"[AVISO] Não foi possível verificar integridade referencial: {e}")
    
    # Cavalos em race_entries que não estão em horses
    try:
        missing_horses = pd.read_sql_query("""
        SELECT COUNT(DISTINCT horse_name) as n FROM race_entries 
        WHERE horse_name NOT IN (SELECT name FROM horses)
        AND horse_name != ''
        """, conn)
        n_missing = missing_horses['n'].iloc[0]
        if n_missing > 0:
            issues.append(f"[AVISO] {n_missing} cavalos em race_entries sem registro em horses.")
        else:
            stats.append("  Integridade referencial race_entries → horses: ✓")
    except Exception as e:
        pass
    
    # ================================================================
    # 3. VALORES NULOS / VAZIOS EM CAMPOS OBRIGATÓRIOS
    # ================================================================
    required_fields = {
        'races': ['race_id', 'year', 'race_name', 'surface', 'distance'],
        'race_entries': ['race_id', 'horse_name', 'position'],
    }
    
    for table, fields in required_fields.items():
        for field in fields:
            try:
                null_check = pd.read_sql_query(
                    f"SELECT COUNT(*) as n FROM {table} WHERE {field} IS NULL OR {field} = ''",
                    conn
                )
                n_null = null_check['n'].iloc[0]
                if n_null > 0:
                    issues.append(f"[AVISO] {n_null} registros com '{field}' vazio em {table}.")
            except Exception:
                pass
    
    # ================================================================
    # 4. DISTRIBUIÇÃO POR ANO E GRADE
    # ================================================================
    try:
        year_grade = pd.read_sql_query("""
        SELECT year, grade, COUNT(*) as n 
        FROM races 
        GROUP BY year, grade 
        ORDER BY year, grade
        """, conn)
        
        if not year_grade.empty:
            stats.append("\n  Distribuição por Ano × Grade:")
            pivot = year_grade.pivot_table(index='year', columns='grade', values='n', fill_value=0, aggfunc='sum')
            for year in pivot.index:
                row_vals = [f"{col}={int(pivot.loc[year, col])}" for col in pivot.columns if pivot.loc[year, col] > 0]
                stats.append(f"    {year}: {', '.join(row_vals)}")
            
            # Alerta se algum ano tem menos de 15 corridas (esperado ~24 G1/ano)
            year_totals = year_grade.groupby('year')['n'].sum()
            for year, total in year_totals.items():
                if total < 10:
                    issues.append(f"[AVISO] Ano {year} tem apenas {total} corridas (esperado ≥20).")
    except Exception as e:
        issues.append(f"[AVISO] Não foi possível analisar distribuição por ano: {e}")
    
    # ================================================================
    # 5. ESTATÍSTICAS DE PARTICIPANTES POR CORRIDA
    # ================================================================
    try:
        participants = pd.read_sql_query("""
        SELECT race_id, COUNT(*) as n FROM race_entries GROUP BY race_id
        """, conn)
        
        if not participants.empty:
            avg_p = participants['n'].mean()
            min_p = participants['n'].min()
            max_p = participants['n'].max()
            stats.append(f"\n  Participantes por corrida: min={min_p}, média={avg_p:.1f}, max={max_p}")
            
            # Corridas com poucos participantes (< 5 é suspeito)
            low_part = participants[participants['n'] < 5]
            if len(low_part) > 0:
                issues.append(f"[AVISO] {len(low_part)} corridas com menos de 5 participantes.")
            
            # Corridas com 0 participantes
            zero_part = participants[participants['n'] == 0]
            if len(zero_part) > 0:
                issues.append(f"[ERRO] {len(zero_part)} corridas com 0 participantes.")
    except Exception:
        pass
    
    # ================================================================
    # 6. COBERTURA DE CAMPOS EXTRAS
    # ================================================================
    extra_fields = {
        'jockey': 'Jóquei',
        'trainer': 'Treinador',
        'odds': 'Odds/Popularidade',
        'horse_weight': 'Peso do cavalo',
        'age': 'Idade',
        'margin': 'Margem',
    }
    
    stats.append("\n  Cobertura de campos extras (race_entries):")
    for field, label in extra_fields.items():
        try:
            coverage = pd.read_sql_query(f"""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN {field} IS NOT NULL AND {field} != '' AND {field} != 0 THEN 1 END) as filled
            FROM race_entries
            """, conn)
            total = coverage['total'].iloc[0]
            filled = coverage['filled'].iloc[0]
            pct = (filled / total * 100) if total > 0 else 0
            status = "✓" if pct > 80 else ("⚠" if pct > 50 else "✗")
            stats.append(f"    {status} {label}: {filled:,}/{total:,} ({pct:.0f}%)")
        except Exception:
            stats.append(f"    ? {label}: não disponível")
    
    # ================================================================
    # 7. PEDIGREE COVERAGE
    # ================================================================
    try:
        ped_coverage = pd.read_sql_query("""
        SELECT 
            (SELECT COUNT(DISTINCT horse_name) FROM race_entries WHERE horse_name != '') as total_horses,
            (SELECT COUNT(*) FROM pedigree WHERE sire_name IS NOT NULL AND sire_name != '') as with_pedigree
        """, conn)
        total_h = ped_coverage['total_horses'].iloc[0]
        with_p = ped_coverage['with_pedigree'].iloc[0]
        pct_p = (with_p / total_h * 100) if total_h > 0 else 0
        stats.append(f"\n  Cobertura de Pedigree: {with_p:,}/{total_h:,} cavalos ({pct_p:.0f}%)")
        if pct_p < 50 and with_p > 0:
            issues.append(f"[AVISO] Pedigree incompleto: apenas {pct_p:.0f}% dos cavalos têm genealogia.")
    except Exception:
        pass
    
    # ================================================================
    # 8. DUPLICATAS
    # ================================================================
    try:
        dup_races = pd.read_sql_query("""
        SELECT url, COUNT(*) as n FROM races GROUP BY url HAVING n > 1
        """, conn)
        if len(dup_races) > 0:
            issues.append(f"[ERRO] {len(dup_races)} URLs duplicadas na tabela races.")
        else:
            stats.append("  Duplicatas em races: nenhuma ✓")
    except Exception:
        pass
    
    conn.close()
    
    # ================================================================
    # RELATÓRIO FINAL
    # ================================================================
    report = []
    report.append("=" * 60)
    report.append("  RELATÓRIO DE VALIDAÇÃO DE DADOS")
    report.append("=" * 60)
    report.append("\n📊 Estatísticas:")
    report.extend(stats)
    
    if issues:
        report.append(f"\n⚠️  Problemas encontrados ({len(issues)}):")
        for issue in issues:
            report.append(f"  {issue}")
    else:
        report.append("\n✅ Nenhum problema encontrado!")
    
    critical = sum(1 for i in issues if '[CRÍTICO]' in i or '[ERRO]' in i)
    warnings = sum(1 for i in issues if '[AVISO]' in i)
    
    report.append(f"\n{'='*60}")
    report.append(f"  Resultado: {critical} erros, {warnings} avisos")
    passed = critical == 0
    report.append(f"  Status: {'✅ APROVADO' if passed else '❌ REPROVADO'}")
    report.append(f"{'='*60}")
    
    full_report = "\n".join(report)
    
    if verbose:
        print(full_report)
    
    return passed, full_report


if __name__ == "__main__":
    passed, _ = validate_all(verbose=True)
    sys.exit(0 if passed else 1)
