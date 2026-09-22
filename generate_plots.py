import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import sqlite3
import os

os.makedirs('docs/assets', exist_ok=True)
sns.set_theme(style='whitegrid')

# ----------------- ENGLISH PLOTS (FROM CSV) -----------------
plt.rcParams['font.family'] = 'sans-serif'
horses_en = pd.read_csv('data/csv_en/horses.csv', low_memory=False)
pedigree_en = pd.read_csv('data/csv_en/pedigree.csv', low_memory=False)

plt.figure(figsize=(10, 6))
top_sires_en = pedigree_en['sire_name'].value_counts().head(10)
sns.barplot(x=top_sires_en.values, y=top_sires_en.index, hue=top_sires_en.index, palette='viridis', legend=False)
plt.title('Top 10 Sires (Fathers) of Graded Racers (2002-2025)', fontsize=14, fontweight='bold')
plt.xlabel('Number of Graded Offsprings', fontsize=12)
plt.ylabel('Sire Name', fontsize=12)
plt.tight_layout()
plt.savefig('docs/assets/top_sires.png', dpi=300)
plt.close()

plt.figure(figsize=(10, 6))
top_earners_en = horses_en.dropna(subset=['name', 'total_earnings']).sort_values('total_earnings', ascending=False).head(10)
top_earners_en['earnings_100m'] = top_earners_en['total_earnings'] / 100_000_000
sns.barplot(x='earnings_100m', y='name', data=top_earners_en, hue='name', palette='magma', legend=False)
plt.title('Top 10 Horses by Total Earnings', fontsize=14, fontweight='bold')
plt.xlabel('Total Earnings (100 Million JPY)', fontsize=12)
plt.ylabel('Horse Name', fontsize=12)
plt.tight_layout()
plt.savefig('docs/assets/top_earners.png', dpi=300)
plt.close()

# ----------------- JAPANESE PLOTS (FROM SQLITE) -----------------
plt.rcParams['font.family'] = 'MS Gothic' # Windows Japanese font
conn = sqlite3.connect('data/sqlite/jra_graded.db')
pedigree_ja = pd.read_sql_query('SELECT sire_name FROM pedigree', conn)
horses_ja = pd.read_sql_query('SELECT name, total_earnings FROM horses', conn)

plt.figure(figsize=(10, 6))
top_sires_ja = pedigree_ja['sire_name'].value_counts().head(10)
sns.barplot(x=top_sires_ja.values, y=top_sires_ja.index, hue=top_sires_ja.index, palette='viridis', legend=False)
plt.title('?????????10 ???(??) (2002-2025)', fontsize=14, fontweight='bold')
plt.xlabel('?????', fontsize=12)
plt.ylabel('????', fontsize=12)
plt.tight_layout()
plt.savefig('docs/assets/top_sires_ja.png', dpi=300)
plt.close()

plt.figure(figsize=(10, 6))
top_earners_ja = horses_ja.dropna(subset=['name', 'total_earnings']).sort_values('total_earnings', ascending=False).head(10)
top_earners_ja['earnings_100m'] = top_earners_ja['total_earnings'] / 100_000_000
sns.barplot(x='earnings_100m', y='name', data=top_earners_ja, hue='name', palette='magma', legend=False)
plt.title('???10 ?????????', fontsize=14, fontweight='bold')
plt.xlabel('????? (??)', fontsize=12)
plt.ylabel('??', fontsize=12)
plt.tight_layout()
plt.savefig('docs/assets/top_earners_ja.png', dpi=300)
plt.close()

print('All 4 plots generated successfully!')
