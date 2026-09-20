"""
Módulo de Banco de Dados e Persistência (SQLite + CSV)
Projeto: Análise de Corridas Graded JRA e Pedigree 5 Gerações JBIS (AEDS 2)

Expansão v2: Suporta G1+G2+G3, todos os participantes, pedigree 5 gerações.
"""

import sqlite3
import os
import pandas as pd

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "sqlite", "jra_graded.db"))
CSV_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "csv"))

def get_connection(db_path=DB_PATH):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")  # Melhor performance para writes frequentes
    return conn

def init_db(db_path=DB_PATH):
    """Cria as tabelas relacionais expandidas do projeto."""
    conn = get_connection(db_path)
    cur = conn.cursor()

    # 1. Tabela de Cavalos (expandida com perfil JBIS)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS horses (
        horse_id TEXT PRIMARY KEY,
        name TEXT UNIQUE NOT NULL,
        sex TEXT,
        birth_year INTEGER,
        birth_date TEXT,
        color TEXT,
        breeder TEXT,
        owner TEXT,
        total_earnings INTEGER,
        total_starts INTEGER,
        total_wins INTEGER,
        profile_scraped INTEGER DEFAULT 0
    );
    """)

    # 2. Tabela de Corridas (G1 + G2 + G3)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS races (
        race_id TEXT PRIMARY KEY,
        year INTEGER NOT NULL,
        date TEXT,
        race_name TEXT NOT NULL,
        track TEXT,
        grade TEXT NOT NULL DEFAULT 'G1',
        grade_weight REAL NOT NULL DEFAULT 1.0,
        surface TEXT,
        distance INTEGER,
        going TEXT,
        weather TEXT,
        num_runners INTEGER,
        url TEXT UNIQUE
    );
    """)

    # 3. Tabela de Resultados (TODOS os participantes, não só Top 3)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS race_entries (
        race_id TEXT NOT NULL,
        horse_name TEXT NOT NULL,
        horse_id TEXT,
        position INTEGER,
        finish_time TEXT,
        jockey TEXT,
        trainer TEXT,
        weight REAL,
        odds REAL,
        horse_weight TEXT,
        age INTEGER,
        sex TEXT,
        passing_positions TEXT,
        margin TEXT,
        PRIMARY KEY (race_id, horse_name),
        FOREIGN KEY (race_id) REFERENCES races(race_id) ON DELETE CASCADE,
        FOREIGN KEY (horse_id) REFERENCES horses(horse_id) ON DELETE SET NULL ON UPDATE CASCADE
    );
    """)

    # 4. Tabela de Pedigree Legada (2 gerações — compatibilidade)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS pedigree (
        horse_id TEXT PRIMARY KEY,
        horse_name TEXT NOT NULL,
        sire_id TEXT,
        sire_name TEXT,
        dam_id TEXT,
        dam_name TEXT,
        grandsire_id TEXT,
        grandsire_name TEXT,
        dam_sire_id TEXT,
        dam_sire_name TEXT,
        FOREIGN KEY (horse_id) REFERENCES horses(horse_id) ON DELETE CASCADE
    );
    """)

    # 5. NOVA: Tabela de Pedigree Relacional (5 gerações)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS pedigree_tree (
        horse_id TEXT NOT NULL,
        horse_name TEXT NOT NULL,
        ancestor_id TEXT,
        ancestor_name TEXT NOT NULL,
        generation INTEGER NOT NULL,
        line TEXT NOT NULL,
        PRIMARY KEY (horse_id, line)
    );
    """)

    # Índices para otimização
    cur.execute("CREATE INDEX IF NOT EXISTS idx_horses_name ON horses(name);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_race_entries_horse ON race_entries(horse_name);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_race_entries_jockey ON race_entries(jockey);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_race_entries_trainer ON race_entries(trainer);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_races_year ON races(year);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_races_grade ON races(grade);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_pedigree_sire ON pedigree(sire_name);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_pedigree_dam_sire ON pedigree(dam_sire_name);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_ped_tree_horse ON pedigree_tree(horse_id);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_ped_tree_ancestor ON pedigree_tree(ancestor_name);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_ped_tree_gen ON pedigree_tree(generation);")

    conn.commit()
    conn.close()
    print(f"[DB] Banco SQLite inicializado: {db_path}")

def export_to_csv(db_path=DB_PATH, csv_dir=CSV_DIR):
    """Exporta todas as tabelas SQLite para arquivos CSV atualizados."""
    os.makedirs(csv_dir, exist_ok=True)
    conn = get_connection(db_path)
    
    tables = ['races', 'race_entries', 'horses', 'pedigree', 'pedigree_tree']
    for t in tables:
        try:
            df = pd.read_sql_query(f"SELECT * FROM {t}", conn)
            out_file = os.path.join(csv_dir, f"{t}.csv")
            df.to_csv(out_file, index=False, encoding='utf-8-sig')
            print(f"[CSV] {t}: {len(df)} registros -> {out_file}")
        except Exception as e:
            print(f"[CSV] Tabela '{t}' ainda não existe ou vazia: {e}")
    
    conn.close()

if __name__ == "__main__":
    init_db()
