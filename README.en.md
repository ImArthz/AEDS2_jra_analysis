<div align="center">

# 🏇 JRA Graded Races & JBIS 5-Gen Pedigree Analytics
### *Data Engineering, Hybrid AI Semantic Translation & Graph Theory in Japanese Horse Racing (2002–2025)*

<p align="center">
  <a href="README.md"><img src="https://img.shields.io/badge/🇧🇷_Idioma-Português-2ea44f?style=for-the-badge" alt="Português"></a>
  <a href="README.en.md"><img src="https://img.shields.io/badge/🇺🇸_Language-English-0969da?style=for-the-badge" alt="English"></a>
  <a href="README.ja.md"><img src="https://img.shields.io/badge/🇯🇵_言語-日本語-d73a49?style=for-the-badge" alt="日本語"></a>
</p>

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.13%2B-3776AB?style=flat-square&logo=python&logoColor=white">
  <img alt="SQLite" src="https://img.shields.io/badge/SQLite3-3NF_%2B_WAL-003B57?style=flat-square&logo=sqlite&logoColor=white">
  <img alt="Gemini AI" src="https://img.shields.io/badge/Gemini_AI-Hybrid_Translator_(29.1k_Terms)-8E75B2?style=flat-square&logo=googlegemini&logoColor=white">
  <img alt="NetworkX" src="https://img.shields.io/badge/NetworkX-DAG_%26_PageRank-1082C3?style=flat-square">
  <img alt="QA Status" src="https://img.shields.io/badge/QA_Validation-100%25_Passed_(0_Errors)-success?style=flat-square">
  <a href="https://github.com/ImArthz/AEDS2_jra_analysis/actions/workflows/compile_latex.yml">
    <img src="https://img.shields.io/badge/LaTeX_Build-Passing-brightgreen?style=flat-square" alt="LaTeX PDF Build">
  </a>
</p>

</div>

---

## 📌 Overview

This repository consolidates the **Data Engineering, Data Science, and Graph Algorithms** ecosystem developed at **CEFET-MG (Divinópolis Campus)** for the integrated courses of **Advanced Data Structures 2 (AEDS 2)** and **Data Science**.

The system extracts, sanitizes, translates, and models **24 years of official historical data (2002–2025)** from elite **Graded Races (G1, G2, and G3)** organized by the **Japan Racing Association (JRA)**, cross-referencing every competitor with its biological profile and its **5-Generation Pedigree Tree** mined from the **Japan Bloodhorse Information System (JBIS)**. The entire dataset is mirrored in both **original Japanese (`data/csv/`)** and **100% translated, standardized English (`data/csv_en/`)**.

---

## 📊 Consolidated Dataset Metrics (Post-Sanitization)

| Dimension / Metric | Consolidated Volume | Quality Assurance (QA) Status |
| :--- | :---: | :--- |
| **Graded Races (`races` — G1, G2, G3)** | **3,216** races (2002–2025) | `100%` populated (Grade, Surface & Distance) |
| **Race Participations (`race_entries`)** | **33,409** entries | `100%` aligned (Jockey, Trainer, Age & Weight) |
| **Unique Elite Horses (`horses`)** | **8,209** athletes | Full JBIS profile, coat color & earnings in Yen (¥) |
| **Direct Pedigrees (`pedigree`)** | **8,202** records (`99.3%`) | *Sire*, *Dam*, *Grandsire* & *Dam Sire* |
| **5-Gen Pedigree Tree (`pedigree_tree`)** | **504,074** ancestor nodes | Up to $2^1 + \dots + 2^5 = 62$ ancestors per horse |
| **AI Semantic Dictionary (`gemini_cache.json`)** | **29,159** proper nouns | `0` residual Japanese characters in EN dataset |
| **Relational Integrity Validation** | **5 Tables in 3NF** | **0 Errors, 0 Warnings (`✅ PASSED`)** |

---

## 🏗 6-Stage Autonomous Pipeline Architecture

```
[1. JRA Scraper] ──► [2. JBIS 5-Gen Scraper] ──► [3. Data Cleaning & Realignment]
      (HTML4/5)          (DFS 62 Ancestors)          (25k rows realigned)
                                                               │
[6. Graphs & ML] ◄── [5. QA Validator (0 Errors)] ◄── [4. Hybrid AI Translator]
 (DAG/PageRank)         (Referential Integrity)       (Gemini Pool + JRA Lexicon)
```

1. **[`src/scraper_jra.py`](src/scraper_jra.py) — JRA Historical Graded Scraper (G1, G2, G3):**
   Extracts official race results from 2002 to 2025, handling multi-decade HTML layout shifts with $O(1)$ *Skip Logic* and *Exponential Backoff*.
2. **[`src/scraper_pedigree.py`](src/scraper_pedigree.py) — JBIS Biological Profile & 5-Gen Pedigree Scraper:**
   Parses JBIS `<dt>/<dd>` definition lists to capture lifetime earnings (converted from *Man-Yen* $\times 10,000$), coat color, breeder, and owner, building the 5-generation ascending tree via **Depth-First Search (DFS)** and automatically merging orthographic aliases under a single 10-digit biological ID (`ON UPDATE CASCADE`).
3. **[`src/clean_data.py`](src/clean_data.py) — Structural Sanitization & Vector Realignment:**
   Fixes historical column shifts in JRA result tables (2004–2018) caused by merged Sex+Age (`性齢`) cells; purges spurious betting-table rows and imputes 100% of `grade`, `surface` (*Turf*, *Dirt*, *Obstacle*), and `distance` via Unicode NFKC normalization.
4. **[`hybrid_translator.py`](hybrid_translator.py) & [`src/translate_db.py`](src/translate_db.py) — 3-Tier Hybrid AI Translation Engine (JP $\to$ EN):**
   Combines $O(1)$ domain dictionaries with a multi-model **Google Gemini API** pool (`gemini-3.5-flash-lite`, `gemini-3.5-flash`, `gemini-3.7-flash`), parallel batch processing, and traditional *Kanmei* crown-prefix rules, resolving *Nanori* human name readings (`武豊` $\to$ *Yutaka Take*) and official international horse spellings (`ディープインパクト` $\to$ *Deep Impact*, `オルフェーヴル` $\to$ *Orfevre*).
5. **[`src/validate_data.py`](src/validate_data.py) — Automated Quality Assurance (QA):**
   Verifies foreign keys, field coverage, Year $\times$ Grade distributions, and zero orphan/duplicate records.
6. **[`src/graph_analysis.py`](src/graph_analysis.py) — Graph Theory Analytics Engine (AEDS 2):**
   - **`PedigreeDAG` (Directed Acyclic Graph):** Generational BFS and DFS traversals, **Lowest Common Ancestor (LCA)**, and **Inbreeding Coefficient** calculation.
   - **`CompetitionGraph` (Weighted Rivalry Network):** Edges weighted by race grade ($\text{G1}=1.0, \text{G2}=0.7, \text{G3}=0.5$), featuring **Sports PageRank**, **Degree Centrality**, **Dijkstra Shortest Path**, and **Connected Components**.
   - **`JockeyHorseGraph` & `JockeyTrainerGraph`:** Bipartite synergy networks connecting jockeys, horses, and trainers.

---

## 📄 Technical Reports in LaTeX (Automated CI/CD PDF Releases)

Complete architectural and mathematical documentation (including the in-depth breakdown of the **7 Semantic Translation & Structural Sanitization Challenges**) automatically compiled to PDF via **GitHub Actions** on every push:

<div align="center">
<table>
  <tr>
    <td align="center">
      <a href="https://github.com/ImArthz/AEDS2_jra_analysis/releases/latest/download/relatorio_extracao.pdf">
        <img src="https://img.shields.io/badge/📄_Relatório_Técnico-Português_(PDF)-d9381e?style=for-the-badge&logo=latex&logoColor=white" alt="Download PDF PT-BR">
      </a>
    </td>
    <td align="center">
      <a href="https://github.com/ImArthz/AEDS2_jra_analysis/releases/latest/download/relatorio_extracao_en.pdf">
        <img src="https://img.shields.io/badge/📄_Technical_Report-English_(PDF)-0969da?style=for-the-badge&logo=latex&logoColor=white" alt="Download PDF EN">
      </a>
    </td>
    <td align="center">
      <a href="https://github.com/ImArthz/AEDS2_jra_analysis/releases/latest/download/relatorio_extracao_ja.pdf">
        <img src="https://img.shields.io/badge/📄_技術レポート-日本語_(PDF)-2ea44f?style=for-the-badge&logo=latex&logoColor=white" alt="Download PDF JA">
      </a>
    </td>
  </tr>
</table>
</div>

- LaTeX source files: [`docs/relatorio_extracao.tex`](docs/relatorio_extracao.tex) | [`docs/relatorio_extracao_en.tex`](docs/relatorio_extracao_en.tex) | [`docs/relatorio_extracao_ja.tex`](docs/relatorio_extracao_ja.tex) | [`docs/proposta_ciencia_dos_dados.tex`](docs/proposta_ciencia_dos_dados.tex)

---

## 📈 Visual Data Insights (2002–2025)

### 🏆 Top 10 Sires (Fathers) by Graded Offspring
The most dominant paternal bloodlines in modern Japanese turf history, led by **Deep Impact** (287 Graded runners) and his sire **Sunday Silence (USA)** (281):

<p align="center">
  <img src="docs/assets/top_sires.png" alt="Top 10 Sires" width="85%">
</p>

### 💰 Top 10 Racehorses by Lifetime Earnings
The highest-earning thoroughbreds recorded in the database (in 100 Million JPY — *Oku-Yen*):

<p align="center">
  <img src="docs/assets/top_earners.png" alt="Top 10 Earners" width="85%">
</p>

---

## 🚀 Quickstart

```bash
# 1. Validate database integrity (QA)
python src/validate_data.py

# 2. Run structural cleaning and rebuild the English DB & CSVs
python src/clean_data.py
python src/translate_db.py

# 3. Run Graph Theory analytics (5-Gen DAG, Competition PageRank & Partnerships)
python src/graph_analysis.py

# 4. Run full end-to-end pipeline via CLI
python src/run_pipeline.py --start-year 2002 --end-year 2025 --analyze
```

---

<div align="center">
  <sub>Developed by <b>Arthur De Oliveira Mendonça</b> — CEFET-MG (Divinópolis Campus) • AEDS 2 & Data Science</sub>
</div>
