<div align="center">

# 🏇 JRA 重賞レース & JBIS 5代血統データ分析
### *日本競馬（2002–2025年）におけるデータエンジニアリング・AIハイブリッド意味翻訳・グラフ理論*

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
    <img src="https://github.com/ImArthz/AEDS2_jra_analysis/actions/workflows/compile_latex.yml/badge.svg" alt="LaTeX PDF Build">
  </a>
</p>

</div>

---

## 📌 プロジェクト概要

本リポジトリは、**CEFET-MG（ミナス・ジェライス連邦技術教育センター）** の **高度なデータ構造 2 (AEDS 2)** および **データサイエンス** コースの統合最終プロジェクトとして開発された、現代日本競馬のデータエンジニアリングおよびグラフ理論分析エコシステムです。

**日本中央競馬会 (JRA)** が主催する過去24年間（2002〜2025年）の **重賞レース（G1・G2・G3）** の全成績を抽出し、**JBIS（ジャパン・ブラッドホース・インフォメーション・システム）** の生物学的プロフィールおよび **5代血統表（1頭あたり最大62頭の祖先）** と結合しています。全データは **日本語オリジナル版 (`data/csv/`)** と、AIハイブリッド翻訳によって完全に標準化された **英語版 (`data/csv_en/`)** の両方で提供されています。

---

## 📊 データセット統計（クレンジング完了後）

| 指標 / テーブル | レコード数 | 品質保証 (QA) ステータス |
| :--- | :---: | :--- |
| **重賞レース (`races` — G1, G2, G3)** | **3,216** レース (2002–2025) | `100%` 補完済（グレード・芝/ダート/障害・距離） |
| **出走記録 (`race_entries`)** | **33,409** エントリ | `100%` 整列済（騎手・調教師・馬齢・馬体重） |
| **ユニーク競走馬 (`horses`)** | **8,209** 頭 | JBISプロフィール・毛色・総獲得賞金（円） |
| **直接血統 (`pedigree`)** | **8,202** レコード (`99.3%`) | 父 (*Sire*)・母 (*Dam*)・父父・母父 (*Dam Sire*) |
| **5代血統ツリー (`pedigree_tree`)** | **504,074** 祖先ノード | 1頭あたり最大 $2^1 + \dots + 2^5 = 62$ 祖先 |
| **AI意味翻訳辞書 (`gemini_cache.json`)** | **29,159** 固有名詞 | 英語DB内の日本語文字残存 `0` 件 |
| **リレーショナル整合性検証** | **第3正規形 (3NF) 全5表** | **エラー 0件・警告 0件 (`✅ 承認済`)** |

---

## 🏗 6段階の自律型パイプラインアーキテクチャ

```
[1. JRA Scraper] ──► [2. JBIS 5-Gen Scraper] ──► [3. Data Cleaning & Realignment]
      (HTML4/5)          (DFS 62 祖先ノード)          (25,014行の列ズレ復元)
                                                               │
[6. Graphs & ML] ◄── [5. QA Validator (0 Errors)] ◄── [4. Hybrid AI Translator]
 (DAG/PageRank)           (参照整合性チェック)        (Gemini Pool + JRA専門辞書)
```

1. **[`src/scraper_jra.py`](src/scraper_jra.py) — JRA重賞成績スクレイパー (G1, G2, G3):**
   2002年から2025年までの公式重賞成績を抽出し、$O(1)$スキップロジックとエクスポネンシャルバックオフにより高効率に収集します。
2. **[`src/scraper_pedigree.py`](src/scraper_pedigree.py) — JBISプロフィール＆5代血統スクレイパー:**
   `<dt>/<dd>`定義リストから総獲得賞金（万円 $\times 10,000$）・毛色・生産牧場・馬主を抽出し、**深さ優先探索 (DFS)** により5代血統ツリーを構築します（`ON UPDATE CASCADE`による表記ゆれ自動統合機能付き）。
3. **[`src/clean_data.py`](src/clean_data.py) — 構造的データクレンジング＆列アライメント復元:**
   2004〜2018年のJRA成績表における「性齢」統合列に起因する列ズレ（25,014行）を数学的に完全復元し、払戻表のノイズ行を除去、さらにNFKC正規化により全3,216レースのグレード・コース種別・距離を100%補完します。
4. **[`hybrid_translator.py`](hybrid_translator.py) & [`src/translate_db.py`](src/translate_db.py) — 3層ハイブリッドAI翻訳エンジン (JP $\to$ EN):**
   $O(1)$静的辞書、**Google Gemini API** マルチモデルプール（`gemini-3.5-flash-lite`, `gemini-3.5-flash`, `gemini-3.7-flash`）、および並列バッチ処理と冠名（*Symboli*, *Mejiro*, *Daiwa*, *Meisho*等）ルールを組み合わせ、騎手の名乗り読み（`武豊` $\to$ *Yutaka Take*）や競走馬の国際公式英語表記（`ディープインパクト` $\to$ *Deep Impact*）を高精度に実現しました。
5. **[`src/validate_data.py`](src/validate_data.py) — 自動データ品質検証システム (QA):**
   外部キー参照整合性、欠損値カバー率、年度×グレード分布を自動検査します。
6. **[`src/graph_analysis.py`](src/graph_analysis.py) — グラフ理論分析エンジン (AEDS 2):**
   - **`PedigreeDAG`（有向非巡回グラフ）:** 世代別BFS/DFS探索、**最小共通祖先 (LCA)**、および **近親交配係数（インブリード）** の算出。
   - **`CompetitionGraph`（重み付き対戦ネットワーク）:** グレード重み（$\text{G1}=1.0, \text{G2}=0.7, \text{G3}=0.5$）に基づく **スポーツPageRank**、**次数中心性**、**Dijkstra最短経路**、**連結成分**。
   - **`JockeyHorseGraph` & `JockeyTrainerGraph`:** 騎手・競走馬・調教師間の二部グラフネットワーク。

---

## 📄 技術レポート（GitHub Actions による自動 LaTeX PDF ビルド）

アーキテクチャと数学的モデリング、および **「ハイブリッド意味翻訳と構造的データクレンジングにおける7つの課題」** を詳述した完全な技術レポート（PDF）は、プッシュごとに自動コンパイルされます：

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

---

## 📈 データインサイト（2002–2025年）

### 🏆 重賞出走馬の種牡馬（父）トップ10
現代日本競馬を牽引する種牡馬ランキング（1位：**ディープインパクト** 287頭、2位：**サンデーサイレンス(USA)** 281頭）：

<p align="center">
  <img src="docs/assets/top_sires_ja.png" alt="重賞出走馬の種牡馬トップ10" width="85%">
</p>

### 💰 生涯獲得賞金トップ10 競走馬
データベース内の生涯獲得賞金（億円単位）トップ10：

<p align="center">
  <img src="docs/assets/top_earners_ja.png" alt="生涯獲得賞金トップ10競走馬" width="85%">
</p>

---

## 🚀 実行方法

```bash
# 1. データベース整合性検証 (QA)
python src/validate_data.py

# 2. データクレンジングおよび英語版DB・CSVの再生成
python src/clean_data.py
python src/translate_db.py

# 3. グラフ理論分析（5代血統DAG・PageRank・騎手シナジー）の実行
python src/graph_analysis.py

# 4. フルパイプラインの実行
python src/run_pipeline.py --start-year 2002 --end-year 2025 --analyze
```

---

<div align="center">
  <sub>Developed by <b>Arthur De Oliveira Mendonça</b> — CEFET-MG (Divinópolis Campus) • AEDS 2 & Data Science</sub>
</div>
