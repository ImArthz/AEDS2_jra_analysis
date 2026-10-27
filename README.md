<div align="center">

# 🏇 JRA Graded Races & JBIS 5-Gen Pedigree Analytics
### *Engenharia de Dados, Tradução Semântica Híbrida via IA e Teoria dos Grafos no Turfe Japonês (2002–2025)*

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

## 📌 Visão Geral

Este repositório consolida o ecossistema de **Engenharia de Dados, Ciência dos Dados e Algoritmos em Grafos** desenvolvido no **CEFET-MG (Campus Divinópolis)** para as disciplinas integradas de **Algoritmos e Estruturas de Dados 2 (AEDS 2)** e **Ciência dos Dados**.

O sistema extrai, higieniza, traduz e modela **24 anos de histórico oficial (2002–2025)** das corridas de elite (**G1, G2 e G3**) da **Japan Racing Association (JRA)**, cruzando cada competidor com seu perfil biológico e sua **Árvore Genealógica de 5 Gerações** extraída do **Japan Bloodhorse Information System (JBIS)**. Todo o conjunto de dados está disponível de forma espelhada em **Japonês original (`data/csv/`)** e **100% traduzido e padronizado em Inglês (`data/csv_en/`)**.

---

## 📊 Números Consolidados do Dataset (Pós-Sanitização)

| Dimensão / Métrica | Volume Consolidado | Status de Qualidade (QA) |
| :--- | :---: | :--- |
| **Corridas Graded (`races` — G1, G2, G3)** | **3.216** provas (2002–2025) | `100%` preenchidas (Grade, Pista e Distância) |
| **Participações Esportivas (`race_entries`)** | **33.409** entradas | `100%` alinhadas (Jóquei, Treinador, Idade e Peso) |
| **Cavalos de Elite Únicos (`horses`)** | **8.209** atletas | Perfil biológico, pelagem e prêmios em Ienes (¥) |
| **Pedigree Direto (`pedigree`)** | **8.202** registros (`99,3%`) | *Sire*, *Dam*, *Grandsire* e *Dam Sire* |
| **Árvore Genealógica 5-Gen (`pedigree_tree`)** | **504.074** nós ancestrais | Até $2^1 + \dots + 2^5 = 62$ ancestrais por cavalo |
| **Dicionário Semântico IA (`gemini_cache.json`)** | **29.159** nomes próprios | `0` caracteres japoneses residuais na base EN |
| **Validação de Integridade Relacional** | **5 Tabelas 3NF** | **0 Erros, 0 Avisos (`✅ APROVADO`)** |

---

## 🏗 Arquitetura do Pipeline em 6 Etapas

```
[1. JRA Scraper] ──► [2. JBIS 5-Gen Scraper] ──► [3. Data Cleaning & Realignment]
      (HTML4/5)          (DFS 62 Ancestrais)         (25k linhas realinhadas)
                                                               │
[6. Grafos & ML] ◄── [5. QA Validator (0 Erros)] ◄── [4. Hybrid AI Translator]
 (DAG/PageRank)        (Integridade Referencial)     (Gemini Pool + Léxico JRA)
```

1. **[`src/scraper_jra.py`](src/scraper_jra.py) — Extração Histórica JRA (G1, G2, G3):**
   Minera resultados oficiais de 2002 a 2025 contornando mudanças drásticas de layout HTML ao longo das décadas, com *Skip Logic* em $O(1)$ e *Exponential Backoff*.
2. **[`src/scraper_pedigree.py`](src/scraper_pedigree.py) — Extração Biológica e Genealogia 5 Gerações (JBIS):**
   Navega pelas listas semânticas `<dt>/<dd>` do JBIS para capturar ganhos vitalícios (convertidos de *Man-Yen* $\times 10.000$), pelagem, criador e proprietário, construindo a árvore ascendente de 5 gerações via **Busca em Profundidade (DFS)** e mesclando automaticamente aliases ortográficos sob o mesmo ID biológico de 10 dígitos (`ON UPDATE CASCADE`).
3. **[`src/clean_data.py`](src/clean_data.py) — Sanitização Estrutural e Realinhamento Vetorial:**
   Corrige deslocamentos históricos de colunas da JRA (2004–2018) onde a fusão de Sexo+Idade (`性齢`) deslocava Jóquei, Tempo e Treinador; expurga ruídos de tabelas de apostas e imputa 100% de `grade`, `surface` (*Turf*, *Dirt*, *Obstacle*) e `distance` via normalização Unicode NFKC.
4. **[`hybrid_translator.py`](hybrid_translator.py) & [`src/translate_db.py`](src/translate_db.py) — Motor Híbrido de Tradução IA (JP $\to$ EN):**
   Combina dicionários estáticos $O(1)$ com um pool multi-modelo da API **Google Gemini** (`gemini-3.5-flash-lite`, `gemini-3.5-flash`, `gemini-3.7-flash`), processamento paralelo em lote e regras de *Kanmei* (prefixos tradicionais da JRA), resolvendo leituras *Nanori* de jóqueis (`武豊` $\to$ *Yutaka Take*) e grafias internacionais oficiais de cavalos (`ディープインパクト` $\to$ *Deep Impact*, `オルフェーヴル` $\to$ *Orfevre*).
5. **[`src/validate_data.py`](src/validate_data.py) — Auditoria Automática de Qualidade (QA):**
   Verifica chaves estrangeiras, cobertura de atributos, distribuição temporal Ano $\times$ Grade e ausência de órfãos ou duplicatas.
6. **[`src/graph_analysis.py`](src/graph_analysis.py) — Motor de Teoria dos Grafos (AEDS 2):**
   - **`PedigreeDAG` (Grafo Direcionado Acíclico):** Travessias em largura (BFS por geração) e profundidade (DFS), **LCA (*Lowest Common Ancestor*)** e cálculo do **Coeficiente de Endocruzamento (*Inbreeding*)**.
   - **`CompetitionGraph` (Rede de Rivalidade Ponderada):** Arestas ponderadas pelo nível da prova ($\text{G1}=1.0, \text{G2}=0.7, \text{G3}=0.5$), cálculo de **PageRank Esportivo**, **Centralidade de Grau**, **Caminho Mínimo de Dijkstra** e **Componentes Conexos**.
   - **`JockeyHorseGraph` & `JockeyTrainerGraph`:** Redes bipartidas de sinergia entre jóqueis, cavalos e treinadores.

---

## 📄 Relatórios Técnicos em LaTeX (Compilação Automática via CI/CD)

Documentação arquitetural e matemática completa (incluindo o estudo detalhado dos **7 Problemas de Tradução Semântica e Sanitização Estrutural**) compilada automaticamente para PDF via **GitHub Actions** a cada push:

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

- Código-fonte dos artigos: [`docs/relatorio_extracao.tex`](docs/relatorio_extracao.tex) | [`docs/relatorio_extracao_en.tex`](docs/relatorio_extracao_en.tex) | [`docs/relatorio_extracao_ja.tex`](docs/relatorio_extracao_ja.tex) | [`docs/proposta_ciencia_dos_dados.tex`](docs/proposta_ciencia_dos_dados.tex)

---

## 📈 Insights Visuais do Dataset (2002–2025)

### 🏆 Top 10 Garanhões (*Sires*) por Prole em Corridas Graded
As linhagens paternas mais dominantes da era moderna do turfe japonês, lideradas por **Deep Impact** (287 filhos em provas Graded) e seu pai **Sunday Silence (USA)** (281):

<p align="center">
  <img src="docs/assets/top_sires.png" alt="Top 10 Sires" width="85%">
</p>

### 💰 Top 10 Cavalos por Premiação Acumulada na Carreira
Os maiores ganhadores financeiros registrados no banco de dados (em centenas de milhões de Ienes — *Oku-Yen*):

<p align="center">
  <img src="docs/assets/top_earners.png" alt="Top 10 Earners" width="85%">
</p>

---

## 🗂 Estrutura do Repositório

```text
AEDS2_jra_analysis/
├── .github/workflows/
│   └── compile_latex.yml         # CI/CD: Compila os relatórios LaTeX (XeLaTeX) e publica Releases
├── data/
│   ├── csv/                      # CSVs limpos no idioma original (Japonês)
│   ├── csv_en/                   # CSVs 100% traduzidos e padronizados em Inglês (Padrão Zenodo)
│   ├── sqlite/                   # Bancos relacionais SQLite3 (jra_graded.db & jra_graded_en.db)
│   └── gemini_cache.json         # Dicionário semântico com 29.159 termos traduzidos via IA
├── docs/
│   ├── assets/                   # Visualizações de alta resolução (EN e JA)
│   ├── proposta_ciencia_dos_dados.tex
│   ├── relatorio_extracao.tex    # Relatório Técnico Completo (PT-BR)
│   ├── relatorio_extracao_en.tex # Relatório Técnico Completo (EN)
│   └── relatorio_extracao_ja.tex # Relatório Técnico Completo (JA)
├── src/
│   ├── database.py               # Schema SQLite 3NF, índices e exportador CSV
│   ├── scraper_jra.py            # Web Scraper JRA (G1, G2, G3)
│   ├── scraper_pedigree.py       # Web Scraper JBIS (Perfil + Pedigree 5 Gerações)
│   ├── clean_data.py             # Sanitização estrutural, realinhamento e imputação
│   ├── validate_data.py          # Sistema de QA e integridade referencial
│   ├── translate_db.py           # Construtor do banco e CSVs em Inglês
│   ├── graph_analysis.py         # Grafos (DAG, LCA, Inbreeding, PageRank, Dijkstra, Bipartidos)
│   └── run_pipeline.py           # Orquestrador CLI completo
├── hybrid_translator.py          # Motor Híbrido de Tradução (Gemini Multi-Model Pool + Batch)
├── generate_plots.py             # Gerador dos gráficos analíticos (EN e JA)
└── LICENSE                       # Licença MIT
```

---

## 🚀 Como Executar

```bash
# 1. Validar a integridade do banco de dados (QA)
python src/validate_data.py

# 2. Executar limpeza estrutural e regenerar o banco/CSVs em Inglês
python src/clean_data.py
python src/translate_db.py

# 3. Executar a análise de Grafos (DAG 5-Gen, Competição, PageRank e Parcerias)
python src/graph_analysis.py

# 4. Executar o pipeline completo via CLI
python src/run_pipeline.py --start-year 2002 --end-year 2025 --analyze
```

---

<div align="center">
  <sub>Desenvolvido por <b>Arthur De Oliveira Mendonça</b> — CEFET-MG (Campus Divinópolis) • Disciplinas de AEDS 2 & Ciência dos Dados</sub>
</div>
