"""
Módulo de Banco de Dados e Persistência (SQLite + CSV)
Projeto: Análise de G1 JRA e Pedigree JBIS (AEDS 2)
"""

import sqlite3
import os
import pandas as pd

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "sqlite", "jra_g1.db"))
CSV_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "csv"))

def get_connection(db_path=DB_PATH):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db(db_path=DB_PATH):
    """Cria as tabelas relacionais do projeto, conforme especificação de AEDS 2."""
    conn = get_connection(db_path)
    cur = conn.cursor()

    # 1. Tabela de Cavalos
    cur.execute("""
    CREATE TABLE IF NOT EXISTS horses (
        horse_id TEXT PRIMARY KEY,
        name TEXT UNIQUE NOT NULL,
        sex TEXT,
        birth_year INTEGER
    );
    """)

    # 2. Tabela de Corridas G1
    cur.execute("""
    CREATE TABLE IF NOT EXISTS races (
        race_id TEXT PRIMARY KEY,
        year INTEGER NOT NULL,
        date TEXT,
        race_name TEXT NOT NULL,
        track TEXT,
        grade TEXT DEFAULT 'G1',
        surface TEXT,
        distance INTEGER,
        url TEXT UNIQUE
    );
    """)

    # 3. Tabela de Resultados (Top 3 de cada corrida)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS race_entries (
        race_id TEXT,
        horse_id TEXT,
        horse_name TEXT NOT NULL,
        position INTEGER NOT NULL,
        finish_time TEXT,
        jockey TEXT,
        weight REAL,
        PRIMARY KEY (race_id, position),
        FOREIGN KEY (race_id) REFERENCES races(race_id) ON DELETE CASCADE,
        FOREIGN KEY (horse_id) REFERENCES horses(horse_id) ON DELETE SET NULL
    );
    """)

    # 4. Tabela de Pedigree (Genealogia - DAG)
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

    # Índices para otimização de consultas e joins (AEDS 2)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_horses_name ON horses(name);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_race_entries_pos ON race_entries(position);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_races_year ON races(year);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_pedigree_sire ON pedigree(sire_name);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_pedigree_dam_sire ON pedigree(dam_sire_name);")

    conn.commit()
    conn.close()
    print(f"[DB] Banco SQLite inicializado com sucesso em: {db_path}")

def export_to_csv(db_path=DB_PATH, csv_dir=CSV_DIR):
    """Exporta todas as tabelas SQLite para arquivos CSV atualizados."""
    os.makedirs(csv_dir, exist_ok=True)
    conn = get_connection(db_path)
    
    tables = ['races', 'race_entries', 'horses', 'pedigree']
    for t in tables:
        df = pd.read_sql_query(f"SELECT * FROM {t}", conn)
        out_file = os.path.join(csv_dir, f"{t}.csv")
        df.to_csv(out_file, index=False, encoding='utf-8-sig')
        print(f"[CSV] Exportado {len(df)} registros para: {out_file}")
    
    conn.close()

if __name__ == "__main__":
    init_db()
