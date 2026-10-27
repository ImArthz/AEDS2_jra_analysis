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

fig, ax = plt.subplots(figsize=(10.5, 6))
top_sires_en = pedigree_en['sire_name'].value_counts().head(10)
sns.barplot(x=top_sires_en.values, y=top_sires_en.index, hue=top_sires_en.index, palette='viridis', legend=False, ax=ax)
for i, v in enumerate(top_sires_en.values):
    ax.text(v + 3, i, f"{v}", va='center', fontsize=10, fontweight='bold', color='#222222')
ax.set_xlim(0, max(top_sires_en.values) * 1.12)
ax.set_title('Top 10 Sires (Fathers) of Graded Racers (2002–2025)', fontsize=14, fontweight='bold', pad=12)
ax.set_xlabel('Number of Graded Offspring', fontsize=12)
ax.set_ylabel('Sire Name', fontsize=12)
plt.tight_layout()
plt.savefig('docs/assets/top_sires.png', dpi=300)
plt.close()

fig, ax = plt.subplots(figsize=(10.5, 6))
top_earners_en = horses_en.dropna(subset=['name', 'total_earnings']).sort_values('total_earnings', ascending=False).head(10).copy()
top_earners_en['earnings_100m'] = top_earners_en['total_earnings'] / 100_000_000
sns.barplot(x='earnings_100m', y='name', data=top_earners_en, hue='name', palette='magma', legend=False, ax=ax)
for i, v in enumerate(top_earners_en['earnings_100m']):
    ax.text(v + 0.2, i, f"¥{v:.2f}B", va='center', fontsize=10, fontweight='bold', color='#222222')
ax.set_xlim(0, top_earners_en['earnings_100m'].max() * 1.14)
ax.set_title('Top 10 Horses by Lifetime Earnings (2002–2025)', fontsize=14, fontweight='bold', pad=12)
ax.set_xlabel('Total Earnings (100 Million JPY / Oku-Yen)', fontsize=12)
ax.set_ylabel('Horse Name', fontsize=12)
plt.tight_layout()
plt.savefig('docs/assets/top_earners.png', dpi=300)
plt.close()

# ----------------- JAPANESE PLOTS (FROM SQLITE) -----------------
plt.rcParams['font.sans-serif'] = ['Yu Gothic', 'Meiryo', 'MS Gothic']
plt.rcParams['axes.unicode_minus'] = False

conn = sqlite3.connect('data/sqlite/jra_graded.db')
pedigree_ja = pd.read_sql_query('SELECT sire_name FROM pedigree WHERE sire_name IS NOT NULL AND sire_name != ""', conn)
horses_ja = pd.read_sql_query('SELECT name, total_earnings FROM horses WHERE name IS NOT NULL AND total_earnings IS NOT NULL', conn)
conn.close()

fig, ax = plt.subplots(figsize=(10.5, 6))
top_sires_ja = pedigree_ja['sire_name'].value_counts().head(10)
sns.barplot(x=top_sires_ja.values, y=top_sires_ja.index, hue=top_sires_ja.index, palette='viridis', legend=False, ax=ax)
for i, v in enumerate(top_sires_ja.values):
    ax.text(v + 3, i, f"{v}頭", va='center', fontsize=10, color='#222222')
ax.set_xlim(0, max(top_sires_ja.values) * 1.12)
ax.set_title('重賞出走馬の種牡馬（父）トップ10 (2002–2025年)', fontsize=14, pad=12)
ax.set_xlabel('重賞出走産駒数（頭）', fontsize=12)
ax.set_ylabel('種牡馬名', fontsize=12)
plt.tight_layout()
plt.savefig('docs/assets/top_sires_ja.png', dpi=300)
plt.close()

fig, ax = plt.subplots(figsize=(10.5, 6))
top_earners_ja = horses_ja.dropna(subset=['name', 'total_earnings']).sort_values('total_earnings', ascending=False).head(10).copy()
top_earners_ja['earnings_100m'] = top_earners_ja['total_earnings'] / 100_000_000
sns.barplot(x='earnings_100m', y='name', data=top_earners_ja, hue='name', palette='magma', legend=False, ax=ax)
for i, v in enumerate(top_earners_ja['earnings_100m']):
    ax.text(v + 0.2, i, f"{v:.2f}億円", va='center', fontsize=10, color='#222222')
ax.set_xlim(0, top_earners_ja['earnings_100m'].max() * 1.15)
ax.set_title('生涯獲得賞金トップ10 競走馬 (2002–2025年)', fontsize=14, pad=12)
ax.set_xlabel('総獲得賞金（億円）', fontsize=12)
ax.set_ylabel('馬名', fontsize=12)
plt.tight_layout()
plt.savefig('docs/assets/top_earners_ja.png', dpi=300)
plt.close()

print('All 4 plots generated successfully!')
