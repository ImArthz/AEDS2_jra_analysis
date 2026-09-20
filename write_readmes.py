import os

header_html = '''<div align="center">
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

<br/>'''

pt_readme = f'''# 🏇 JRA Graded Races & JBIS Pedigree Analysis (AEDS 2)

{header_html}

Este repositório consolida o projeto final desenvolvido para a disciplina de **Algoritmos e Estruturas de Dados 2 (AEDS 2)**. Trata-se de um robusto ecossistema de engenharia de dados focado no turfe japonês moderno. O sistema extrai e estrutura resultados históricos das corridas de elite da **Japan Racing Association (JRA)** e cruza esses dados com a enciclopédia genética do **Japan Bloodhorse Information System (JBIS)**, modelando o resultado final em algoritmos complexos de **Teoria dos Grafos**.

---

## 🎯 Objetivos do Projeto

- **Escalabilidade & Web Scraping:** Processar milhares de resultados históricos contornando instabilidades e mudanças de layout ao longo de 20 anos (2002 a 2025).
- **Integridade Relacional:** Manter um banco de dados estruturado protegendo a integridade referencial via restrições rigorosas (`FOREIGN KEY`, `ON UPDATE CASCADE`).
- **Análise com Grafos:** Mapear redes biológicas (Árvores Genealógicas) e esportivas (Competidores) usando algoritmos avançados (como PageRank e Centralidade) para descobrir as linhagens mais influentes.

---

## 🏗 Arquitetura do Pipeline

O núcleo do projeto opera por meio de um Pipeline autônomo dividido em 5 etapas principais:

### 1. JRA Scraper (Extração Graded)
Vasculha o histórico de corridas japonesas do tipo G1, G2 e G3, extraindo métricas precisas (idade, tempo, margem de vitória, variação de peso na pista e condições climáticas). Para otimização, o sistema possui **Skip Logic** e ignora automaticamente provas já integradas ao banco.

### 2. JBIS Scraper (Pedigree & Perfil Biológico)
Busca dados sobre ganhos financeiros (em Ienes) na página dos perfis, além de minerar e modelar uma **Árvore Genealógica de 5 Gerações** (até 62 ancestrais por cavalo) que fundamenta as análises genéticas e de endocruzamento.

### 3. Sistema de Validação Dinâmica (QA)
Gera relatórios de integridade referencial automáticos e dispara alertas em caso de anomalias nas relações entre Tabelas de Cavalo e Resultados.

### 4. Dicionário de Tradução Dinâmica (JP -> EN)
Módulo que converte dinamicamente terminologias de pista (`良` -> `Firm`) e clima do formato codificado japonês para a taxonomia esportiva universal em Inglês. Essencial para treinar futuros algoritmos de Inteligência Artificial sem viés de idioma.

### 5. Engine Analítica de Grafos
- **Grafos Direcionados Acíclicos (DAG):** Mapeamento genético focado na árvore ascendente dos animais (útil para Lowest Common Ancestor).
- **Grafos Bipartidos e de Centralidade:** Conexão direta entre jóqueis e cavalos. Utilização do algoritmo **PageRank** da Google adaptado para o ecossistema das corridas.

---

## 📊 Estrutura de Dados & Relatórios
Todo o projeto foi espelhado dinamicamente entre arquivos `.csv` estáticos na pasta `data/csv/` e um banco SQLite `jra_graded.db`.

📄 **Relatório Técnico Completo:**
Elaborei um documento minucioso explicando minha arquitetura, os erros que contornei (como blocos de IP e restrições silenciosas do banco) no formato `LaTeX`.

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

Os arquivos renderizados acima são compilados automaticamente via **GitHub Actions** a cada push.

---

## 🚀 Como Iniciar

1. Clone o repositório na sua máquina local.
2. Dê um duplo clique no arquivo facilitador **`run_full.bat`** no Windows, ou execute:
   ```bash
   cd src
   python run_pipeline.py --start-year 2002 --end-year 2025 --analyze
   ```
'''

en_readme = f'''# 🏇 JRA Graded Races & JBIS Pedigree Analysis (AEDS 2)

{header_html}

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
'''

ja_readme = f'''# 🏇 JRA 重賞レース & JBIS 血統分析 (AEDS 2)

{header_html}

このリポジトリは、**高度なデータ構造2 (AEDS 2)** コースのために開発された最終プロジェクトを統合しています。これは、現代の日本の競馬に焦点を当てた堅牢なデータエンジニアリングエコシステムです。システムは、**日本中央競馬会 (JRA)** からエリートレースの歴史的結果を抽出し、構造化し、このデータを**ジャパン・ブラッドホース・インフォメーション・システム (JBIS)** の遺伝的百科事典と交差させ、最終的な結果を複雑な**グラフ理論**アルゴリズムでモデル化します。

---

## 🎯 プロジェクトの目標

- **スケーラビリティとウェブスクレイピング:** 20年間（2002年から2025年）にわたる不安定性やレイアウトの変更を回避し、何千もの歴史的結果を処理します。
- **リレーショナルインテグリティ:** 厳格な制約（`FOREIGN KEY`、`ON UPDATE CASCADE`）を通じて参照整合性を保護する構造化されたデータベースを維持します。
- **グラフ分析:** 高度なアルゴリズム（PageRankやCentralityなど）を使用して生物学的ネットワーク（血統図）やスポーツネットワーク（競技者）をマッピングし、最も影響力のある血統を発見します。

---

## 🏗 パイプラインアーキテクチャ

プロジェクトのコアは、5つの主要な段階に分かれた自律型パイプラインを通じて動作します。

### 1. JRA スクレイパー (重賞抽出)
G1、G2、G3の日本のレースの歴史を探求し、正確な指標（年齢、タイム、着差、トラックでの馬体重の変動、気象条件）を抽出します。最適化のため、システムには**スキップロジック**があり、すでにデータベースに統合されているレースを自動的に無視します。

### 2. JBIS スクレイパー (血統と生物学的プロフィール)
プロフィールのページで金銭的な収入（円）に関するデータを取得するだけでなく、遺伝的および近親交配分析の基礎となる**5代血統図**（分析された馬1頭あたり最大62の祖先）をマイニングおよびモデル化します。

### 3. 動的検証システム (QA)
自動的な参照整合性レポートを生成し、馬と結果テーブル間の関係に異常がある場合にアラートをトリガーします。

### 4. 動的翻訳辞書 (JP -> EN)
日本のエンコード形式の馬場状態（`良` -> `Firm`）や天候を英語の普遍的なスポーツタクソノミーに動的に変換するモジュール。言語の偏りなしに将来の人工知能アルゴリズムを訓練するために不可欠です。

### 5. グラフ分析エンジン
- **有向非巡回グラフ (DAG):** 動物の上昇ツリーに焦点を当てた遺伝的マッピング（最小共通祖先 - LCAに有用）。
- **二部グラフと中心性グラフ:** 騎手と馬の直接的なつながり。競馬エコシステムに適応したGoogleの**PageRank**アルゴリズムの利用。

---

## 📊 データ構造とレポート
プロジェクト全体は、`data/csv/` フォルダ内の静的 `.csv` ファイルと SQLite データベース `jra_graded.db` の間で動的にミラーリングされました。

📄 **完全なテクニカルレポート:**
アーキテクチャ、回避したエラー（IPブロックやサイレントなデータベースの制約など）を `LaTeX` 形式で説明する詳細なドキュメントを作成しました。

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

上記のレンダリングされたファイルは、プッシュのたびに **GitHub Actions** を介して自動的にコンパイルされます。

---

## 🚀 始め方

1. ローカルマシンにリポジトリをクローンします。
2. Windows ではヘルパーファイル **`run_full.bat`** をダブルクリックするか、次を実行します。
   ```bash
   cd src
   python run_pipeline.py --start-year 2002 --end-year 2025 --analyze
   ```
'''

with open('README.md', 'w', encoding='utf-8') as f: f.write(pt_readme)
with open('README.en.md', 'w', encoding='utf-8') as f: f.write(en_readme)
with open('README.ja.md', 'w', encoding='utf-8') as f: f.write(ja_readme)
