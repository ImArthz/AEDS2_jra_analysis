# 🏇 JRA Graded Races & JBIS Pedigree Analysis (AEDS 2)

<div align="center">
  <a href="README.md">🇧🇷 Português</a> |
  <a href="README.en.md">🇺🇸 English</a> |
  <a href="README.ja.md">🇯🇵 日本語</a>
</div>

<br/>

<div align="center">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.13-blue.svg">
  <img alt="SQLite" src="https://img.shields.io/badge/SQLite-Database-lightgrey.svg">
  <img alt="NetworkX" src="https://img.shields.io/badge/NetworkX-Graph_Theory-green.svg">
  <img alt="Status" src="https://img.shields.io/badge/Status-Stable%20(2002--2025)-brightgreen">
  <a href="https://github.com/ImArthz/AEDS2_jra_analysis/actions/workflows/compile_latex.yml">
    <img src="https://github.com/ImArthz/AEDS2_jra_analysis/actions/workflows/compile_latex.yml/badge.svg" alt="Build Status">
  </a>
</div>

<br/>

This repository consolidates the final project developed for the **Advanced Data Structures 2 (AEDS 2)** course. It is a robust data engineering ecosystem focused on modern Japanese horse racing. The system extracts and structures historical results of elite races from the **Japan Racing Association (JRA)** and crosses this data with the genetic encyclopedia of the **Japan Bloodhorse Information System (JBIS)**, modeling the final result in complex **Graph Theory** algorithms.

---

## 🎯 Project Goals

- **Scalability & Web Scraping:** Process thousands of historical results, bypassing instabilities and layout changes over 20 years (2002 to 2025).
- **Relational Integrity:** Maintain a structured database protecting referential integrity via strict constraints (`FOREIGN KEY`, `ON UPDATE CASCADE`).
- **Graph Analysis:** Map biological networks (Pedigree Trees) and sports networks (Competitors) using advanced algorithms (like PageRank and Centrality) to discover the most influential lineages.

---

## 🏗 Pipeline Architecture

The core of the project operates through an autonomous Pipeline divided into 5 main stages:

### 1. JRA Scraper (Graded Extraction)
Scours the history of G1, G2, and G3 Japanese races, extracting precise metrics (age, time, winning margin, weight variation on the track, and weather conditions). For optimization, the system has **Skip Logic** and automatically ignores races already integrated into the database.

### 2. JBIS Scraper (Pedigree & Biological Profile)
Fetches data on financial earnings (in Yen) on profile pages, in addition to mining and modeling a **5-Generation Pedigree Tree** (up to 62 ancestors per horse) that underlies genetic and inbreeding analyses.

### 3. Dynamic Validation System (QA)
Generates automatic referential integrity reports and triggers alerts in case of anomalies in the relationships between Horse and Result tables.

### 4. Dynamic Translation Dictionary (JP -> EN)
Module that dynamically converts track terminologies (`良` -> `Firm`) and weather from the Japanese encoded format to the universal sports taxonomy in English. Essential for training future Artificial Intelligence algorithms without language bias.

### 5. Graph Analytics Engine
- **Directed Acyclic Graphs (DAG):** Genetic mapping focused on the ascending tree of animals (useful for Lowest Common Ancestor).
- **Bipartite and Centrality Graphs:** Direct connection between jockeys and horses. Utilization of Google's **PageRank** algorithm adapted for the racing ecosystem.

---

## 📊 Data Structure & Reports
The entire project was dynamically mirrored between static `.csv` files in the `data/csv/` folder and a SQLite database `jra_graded.db`.

📄 **Complete Technical Report:**
I prepared a detailed document explaining my architecture, the errors I bypassed (like IP blocks and silent database constraints) in `LaTeX` format.

<table>
  <tr>
    <td align="center">
      <a href="https://github.com/ImArthz/AEDS2_jra_analysis/releases/latest/download/relatorio_extracao.pdf">
        <img src="https://img.shields.io/badge/Download_Artigo-PT--BR_PDF-red?style=for-the-badge&logo=adobeacrobatreader&logoColor=white" alt="Download PDF PT-BR">
      </a>
    </td>
    <td align="center">
      <a href="https://github.com/ImArthz/AEDS2_jra_analysis/releases/latest/download/relatorio_extracao_en.pdf">
        <img src="https://img.shields.io/badge/Download_Article-EN_PDF-blue?style=for-the-badge&logo=adobeacrobatreader&logoColor=white" alt="Download PDF EN">
      </a>
    </td>
    <td align="center">
      <a href="https://github.com/ImArthz/AEDS2_jra_analysis/releases/latest/download/relatorio_extracao_ja.pdf">
        <img src="https://img.shields.io/badge/Download_Report-JA_PDF-green?style=for-the-badge&logo=adobeacrobatreader&logoColor=white" alt="Download PDF JA">
      </a>
    </td>
  </tr>
</table>

The rendered files above are automatically compiled via **GitHub Actions** on every push.

---

## 🚀 How to Start

1. Clone the repository to your local machine.
2. Double-click the helper file **`run_full.bat`** on Windows, or execute:
   ```bash
   cd src
   python run_pipeline.py --start-year 2002 --end-year 2025 --analyze
   ```
