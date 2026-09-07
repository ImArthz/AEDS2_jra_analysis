# Análise de Corridas G1 Japonesas (JRA) e Linhagens (JBIS) - AEDS 2

Projeto desenvolvido para a disciplina de **Algoritmos e Estruturas de Dados 2 (AEDS 2)**.
O objetivo é extrair o histórico oficial de corridas de Grupo 1 (G1) do turfe japonês (**JRA**), coletar o pódio (**Top 3**) de cada prova, mapear a genealogia de 5 gerações (**Pedigree**) no **JBIS**, e modelar essas relações por meio de **Estruturas de Dados Avançadas e Teoria dos Grafos**.

---

## 📊 Status do Projeto: Extração e Coleta 100% Concluídas

A primeira fase do projeto (Coleta, Tratamento, Resiliência e Persistência de Dados) foi **totalmente finalizada com 100% de êxito**:

- 📋 **464 Corridas G1** salvas (todos os anos de **2002 a 2020** sem lacunas).
- 🏆 **1.348 Entradas de Pódio (Top 3)** registradas.
- 🐎 **696 Cavalos Únicos** catalogados na base.
- 🧬 **696 Genealogias Completas (Pedigree)** extraídas do JBIS (100% dos cavalos mapeados).
- 🌳 **1.522 Nós** gerados no Grafo de Pedigree (DAG).

---

## 1. Estrutura do Projeto

```text
AEDS2_JRA_HorseRacing/
├── data/
│   ├── csv/                   <- Arquivos CSV finais gerados automaticamente
│   │   ├── races.csv          <- Corridas G1 (464 registros: ID, data, prova, hipódromo, superfície, distância)
│   │   ├── race_entries.csv   <- Pódio Top 3 (1.348 registros: posição, cavalo, jóquei, tempo, peso)
│   │   ├── horses.csv         <- Tabela única de cavalos (696 registros: nome, sexo, ID)
│   │   └── pedigree.csv       <- Genealogia (696 registros: Pai, Mãe, Avô Paterno, Avô Materno / Damsire)
│   └── sqlite/
│       └── jra_g1.db          <- Banco de dados relacional com índices e chaves estrangeiras
├── docs/
│   └── relatorio_extracao.tex <- Relatório técnico formal da etapa de extração em LaTeX
├── src/
│   ├── database.py            <- Gerenciamento de esquema SQLite e exportação para CSV
│   ├── scraper_jra.py         <- Scraper oficial da JRA com cp932 encoding, checkpointing e delay seguro
│   ├── scraper_pedigree.py    <- Scraper de pedigree no JBIS Search com retries e backoff exponencial
│   ├── graph_analysis.py      <- Módulo de AEDS 2: Grafos (DAG, BFS, DFS, LCA, Dijkstra, Métricas)
│   └── run_pipeline.py        <- Executável unificado do pipeline
└── README.md                  <- Documentação principal do projeto
```

---

## 2. Decisão do Escopo Temporal (2002 a 2020)

* **Por que não 1980 ou 2000?**  
  As páginas de resultados oficiais detalhados no arquivo moderno da JRA (`datafile/seiseki/replay/...`) foram disponibilizadas e padronizadas a partir de **2002**. Páginas anteriores a 2002 retornam `403 Forbidden` no replay oficial.
* **A Era de Ouro do Turfe Japones (2002 a 2020):**  
  Esse intervalo cobre 19 anos e concentra a história mais rica do turfe japonês moderno:
  * A linhagem dominante de **Sunday Silence** e seus filhos campeões (*Deep Impact*, *Neo Universe*, *Heart's Cry*, *Daiwa Major*, *Zenno Rob Roy*).
  * As grandes lendas das pistas: *Vodka*, *Daiwa Scarlet*, *Buena Vista*, *Gold Ship*, *Orfevre*, *Lord Kanaloa*, *Maurice*, *Kitasan Black*, *Almond Eye*, *Contrail*.
  * **Volume ideal para AEDS 2:** São **464 corridas G1**, **1.348 colocações de Top 3** e **696 cavalos únicos**. Um grafo com ~1.500 nós no DAG genealógico é perfeito para algoritmos de rede, visualizações sem sobrecarga de memória e cálculos didáticos de complexidade.

---

## 3. Resiliência e Politeness (Engenharia do Scraper)

* **Intervalo Educado:** Padrão de **2,0 segundos** por requisição HTTP (`time.sleep(2.0)`), evitando bloqueios e respeitando os servidores da JRA e do JBIS.
* **Sistema de Checkpoint Contínuo:**  
  O scraper salva cada corrida e cada cavalo no banco SQLite **imediatamente**. Antes de realizar qualquer requisição, ele verifica se o item já existe no banco. Se interrompido, basta rodar novamente: ele continua exatamente de onde parou.
* **Tratamento de Encoding (`cp932` / Shift-JIS):**  
  Resolveu-se problemas de detecção de encoding (ex: ano de 2016) aplicando `cp932` (superset do Shift-JIS no Windows) e adaptando filtros regex para formatos flexíveis de data (`月/日` e `2月21日`).
* **Retry com Backoff Exponencial:**  
  No scraper do JBIS, implementou-se lógica de re-tentativa automática (até 3 tentativas) em caso de instabilidades de rede e geração de registros nulos neutros para evitar loops infinitos.
* **Sincronização Incremental para CSV:** Os CSVs em `data/csv/` são sincronizados a cada lote de 5 cavalos.

---

## 4. Conexão com Algoritmos e Estruturas de Dados 2 (AEDS 2)

O módulo `src/graph_analysis.py` implementa os conceitos fundamentais da disciplina:

### A. Grafo de Pedigree (DAG - Directed Acyclic Graph)
* **Estrutura:** Grafo direcionado acíclico onde as arestas representam parentesco ($Pai \to Filho$, $M\tilde{a}e \to Filho$).
* **BFS (Busca em Largura):** Calcula os níveis geracionais de distância a partir de qualquer cavalo ($O(V + E)$).
* **DFS (Busca em Profundidade):** Explora e lista todos os ramos de ancestrais conhecidos.
* **LCA (Lowest Common Ancestor - Menor Ancestral Comum):** Algoritmo que determina o ancestral comum mais próximo entre dois cavalos campeões.

### B. Grafo de Competição (Confronto Direto)
* **Estrutura:** Grafo onde os nós são cavalos e as arestas representam pódios disputados juntos.
  * **Não Direcionado (Ponderado):** Peso da aresta = número de corridas disputadas juntos no Top 3.
  * **Direcionado:** $A \to B$ se o cavalo $A$ terminou à frente do cavalo $B$.
* **Componentes Conexos:** Identificação de subgrupos desconexos (ex.: especialistas em sprint vs longa distância).
* **Algoritmo de Dijkstra:** Determina o menor caminho entre dois competidores na rede de rivalidades.
* **Métricas de Centralidade:** Grau (*Degree*), *Betweenness Centrality* e *Closeness Centrality*.

---

## 5. Principais Resultados Obtidos

### Top 10 Sires (Garanhões) — Desempenho no Pódio G1 (2002–2020)

| # | Sire (Pai) | Presenças no Top 3 | Turf (Grama) | Dirt (Areia) | Obstacle (Obstáculos) |
| :-: | :--- | :-: | :-: | :-: | :-: |
| 🥇 | **Deep Impact** (*ディープインパクト*) | **144** | 143 | 0 | 1 |
| 🥈 | **Sunday Silence (USA)** (*サンデーサイレンス*) | **114** | 111 | 2 | 1 |
| 🥉 | **King Kamehameha** (*キングカメハメハ*) | **69** | 60 | 9 | 0 |
| 4 | **Stay Gold** (*ステイゴールド*) | **49** | 41 | 1 | 7 |
| 5 | **Fuji Kiseki** (*フジキセキ*) | **49** | 43 | 4 | 2 |
| 6 | **Hearts Cry** (*ハーツクライ*) | **44** | 44 | 0 | 0 |
| 7 | **Daiwa Major** (*ダイワメジャー*) | **39** | 39 | 0 | 0 |
| 8 | **Agnes Tachyon** (*アグネスタキオン*) | **37** | 37 | 0 | 0 |
| 9 | **Symboli Kris S (USA)** (*シンボリクリスエス*) | **34** | 30 | 4 | 0 |
| 10 | **Kurofune (USA)** (*クロフネ*) | **33** | 22 | 11 | 0 |

---

## 6. Relatório Acadêmico (Versão LaTeX e Leitura Direta)

O relatório acadêmico formal da disciplina foi gerado em LaTeX e está disponível no repositório em [`docs/relatorio_extracao.tex`](docs/relatorio_extracao.tex).

<details>
<summary>📖 <b>Clique aqui para expandir e ler o Relatório Acadêmico na íntegra</b></summary>

<br>

### Relatório Parcial: Coleta, Tratamento e Modelagem de Dados
**Análise de Corridas G1 Japonesas (JRA) e Genealogia (JBIS) em Grafos**  
*Disciplina de Algoritmos e Estruturas de Dados 2 (AEDS 2)*

#### Resumo
Este relatório documenta a primeira fase do projeto da disciplina de Algoritmos e Estruturas de Dados 2 (AEDS 2), focada na extração automatizada, estruturação e modelagem dos dados de corridas oficiais de Grupo 1 (G1) do turfe japonês (*Japan Racing Association — JRA*) e das linhagens de pedigree no *Japan Bloodhorse Information System (JBIS)*, cobrindo o período de 2002 a 2020. Detalham-se as decisões de engenharia de software para garantir a resiliência do *web scraper*, o esquema relacional em SQLite/CSV, o tratamento de particularidades técnicas (como a codificação de caracteres `cp932`/Shift-JIS) e o mapeamento dos dados para estruturas de grafos (DAG genealógico e Grafo de Competição). A etapa de extração foi concluída com 100% de êxito, resultando em 464 corridas G1, 1.348 entradas de pódio (Top 3), 696 cavalos únicos e 696 pedigrees mapeados (1.522 nós no DAG).

---

#### 1. Introdução e Escopo Temporal
O objetivo principal deste trabalho é aplicar conceitos avançados de **Estruturas de Dados e Teoria dos Grafos** em um conjunto de dados do mundo real. O turfe japonês moderno oferece um domínio rico para estudo devido à forte especialização de atletas e à transmissão genética de características físicas e esportivas através das gerações.

##### Definição do Intervalo Temporal (2002 a 2020)
1. **Disponibilidade Técnica dos Dados:** As páginas oficiais detalhadas de resultados no arquivo moderno da JRA (`datafile/seiseki/replay/`) foram padronizadas a partir do ano de 2002.
2. **Relevância Histórica e Escala Ideal:** Esse intervalo de 19 anos compreende a era de ouro do turfe japonês moderno, dominada pela linhagem lendária de *Sunday Silence* e de seus descendentes (*Deep Impact*, *Heart's Cry*, *King Kamehameha*, *Orfevre*, *Almond Eye*).
3. **Adequação para Algoritmos de AEDS 2:** O volume de 464 corridas e 696 cavalos únicos gera um grafo com aproximadamente 1.500 nós na árvore genealógica expandida, permitindo execução eficiente de algoritmos como LCA, Dijkstra e métricas de centralidade.

---

#### 2. Arquitetura e Modelagem do Banco de Dados
Para garantir a persistência dos dados e a integridade referencial, implementou-se um banco de dados relacional em **SQLite** (`jra_g1.db`), integrado a um módulo de sincronização automática com arquivos **CSV** (`database.py`).

- `races`: `race_id`, `year`, `date`, `race_name`, `track`, `surface`, `distance`, `url`.
- `race_entries`: `race_id`, `horse_name`, `position`, `finish_time`, `jockey`, `weight`.
- `horses`: `horse_id`, `name`, `sex`.
- `pedigree`: `horse_id`, `sire_name`, `dam_name`, `grandsire_name`, `dam_sire_name`.

---

#### 3. Desenvolvimento dos Web Scrapers e Resiliência
- **Tratamento de Encoding (`cp932`/Shift-JIS):** Resolução de incompatibilidades de codificação de caracteres em páginas da JRA.
- **Politeness Delay e Checkpointing:** Delay de 2,0 segundos por requisição e verificação de redundância antes de cada requisição HTTP.
- **Retry com Backoff Exponencial:** 3 tentativas automáticas no scraper do JBIS e persistência incremental a cada 5 registros.

---

#### 4. Código Fonte em LaTeX (`docs/relatorio_extracao.tex`)

```latex
\documentclass[12pt,a4paper]{article}
\usepackage[utf8]{utf8}
\usepackage[portuguese]{babel}
\usepackage[margin=2.5cm]{geometry}
\usepackage{amsmath,amssymb}
\usepackage{booktabs}
\usepackage{hyperref}

\title{\textbf{Relatório Parcial: Coleta, Tratamento e Modelagem de Dados}}
\author{\textbf{Algoritmos e Estruturas de Dados 2 (AEDS 2)}}
\date{\today}

\begin{document}
\maketitle
% Veja o código completo no arquivo docs/relatorio_extracao.tex
\end{document}
```

</details>

---

## 7. Como Executar

Abra o terminal e navegue até a pasta do projeto:

```bash
cd "src"
```

### Executar a Análise de Grafos completa (utilizando a base de dados pronta):
```bash
python run_pipeline.py --skip-races --skip-pedigree --analyze
```

### Modo Teste Rápido (Validação com o ano de 2005):
```bash
python run_pipeline.py --test
```

### Execução Completa do Pipeline (caso queira refazer ou atualizar dados):
```bash
python run_pipeline.py --start-year 2002 --end-year 2020 --delay 2.0 --analyze
```
