# 🏇 JRA 重賞レース & JBIS 血統分析 (AEDS 2)

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
