# Análise de Corridas G1 Japonesas (JRA) e Linhagens (JBIS) - AEDS 2

Projeto desenvolvido para a disciplina de **Algoritmos e Estruturas de Dados 2 (AEDS 2)**.
O objetivo é extrair o histórico oficial de corridas de Grupo 1 (G1) do turfe japonês (**JRA**), coletar o pódio (**Top 3**) de cada prova, mapear a genealogia de 5 gerações (**Pedigree**) no **JBIS**, e modelar essas relações por meio de **Estruturas de Dados Avançadas e Teoria dos Grafos**.

---

## 1. Estrutura do Projeto

```text
AEDS2_JRA_HorseRacing/
├── data/
│   ├── csv/                   <- Arquivos CSV finais gerados automaticamente
│   │   ├── races.csv          <- Corridas G1 (ID, data, prova, hipódromo, superfície, distância)
│   │   ├── race_entries.csv   <- Pódio Top 3 (posição, cavalo, jóquei, tempo, peso)
│   │   ├── horses.csv         <- Tabela única de cavalos (nome, sexo, ID)
│   │   └── pedigree.csv       <- Genealogia (Pai, Mãe, Avô Paterno, Avô Materno / Damsire)
│   └── sqlite/
│       └── jra_g1.db          <- Banco de dados relacional com índices e chaves estrangeiras
├── src/
│   ├── database.py            <- Gerenciamento de esquema SQLite e exportação para CSV
│   ├── scraper_jra.py         <- Scraper oficial da JRA com checkpointing e delay seguro
│   ├── scraper_pedigree.py    <- Scraper de pedigree no JBIS Search com checkpointing
│   ├── graph_analysis.py      <- Módulo de AEDS 2: Grafos (DAG, BFS, DFS, LCA, Dijkstra, Métricas)
│   └── run_pipeline.py        <- Executável unificado com suporte a argumentos CLI
└── README.md                  <- Documentação do projeto
```

---

## 2. Decisão do Escopo Temporal (2002 a 2020)

* **Por que não 1980 ou 2000?**  
  As páginas de resultados oficiais detalhados no arquivo moderno da JRA (`datafile/seiseki/replay/...`) foram disponibilizadas e padronizadas a partir de **2002**. Páginas anteriores a 2002 retornam `403 Forbidden` no replay oficial.
* **A Era de Ouro do Turfe Japonês (2002 a 2020):**  
  Esse intervalo cobre 19 anos e concentra a história mais rica do turfe japonês moderno:
  * A linhagem dominante de **Sunday Silence** e seus filhos campeões (*Deep Impact*, *Neo Universe*, *Heart's Cry*, *Daiwa Major*, *Zenno Rob Roy*).
  * As grandes lendas das pistas: *Vodka*, *Daiwa Scarlet*, *Buena Vista*, *Gold Ship*, *Orfevre*, *Lord Kanaloa*, *Maurice*, *Kitasan Black*, *Almond Eye*, *Contrail*.
  * **Volume ideal para AEDS 2:** São cerca de **440 corridas G1**, **~1.300 colocações de Top 3** e cerca de **450 cavalos únicos**. Um grafo com 450 nós é perfeito para algoritmos de rede, visualizações sem sobrecarga de memória e cálculos didáticos de complexidade.

---

## 3. Resiliência e Politeness (Segurança do Scraper)

* **Intervalo Educado:** Padrão de **2,0 segundos** por requisição HTTP (`time.sleep(2.0)`), evitando bloqueios e respeitando os servidores.
* **Sistema de Checkpoint Contínuo:**  
  O scraper salva cada corrida e cada cavalo no banco SQLite **imediatamente**. Antes de realizar qualquer requisição, ele verifica se o item já existe no banco. Se você pausar com `Ctrl+C` ou a conexão falhar, basta rodar novamente: ele continua exatamente da onde parou sem re-baixar nada!
* **Exportação CSV Instantânea:** Os CSVs em `data/csv/` são sincronizados automaticamente após cada lote.

---

## 4. Conexão com Algoritmos e Estruturas de Dados 2 (AEDS 2)

O módulo `src/graph_analysis.py` implementa os conceitos fundamentais da disciplina:

### A. Grafo de Pedigree (DAG - Directed Acyclic Graph)
* **Estrutura:** Grafo direcionado acíclico onde as arestas representam parentesco ($Pai \to Filho$, $M\tilde{a}e \to Filho$).
* **BFS (Busca em Largura):** Calcula os níveis geracionais de distância a partir de qualquer cavalo ($O(V + E)$).
* **DFS (Busca em Profundidade):** Explora e lista todos os ramos de ancestrais conhecidos.
* **LCA (Lowest Common Ancestor - Menor Ancestral Comum):** Algoritmo que determina o ancestral comum mais próximo entre dois cavalos campeões (ex.: verificar se um campeão de milha em grama e um campeão em areia compartilham o mesmo avô).

### B. Grafo de Competição (Confronto Direto)
* **Estrutura:** Grafo onde os nós são cavalos e as arestas representam pódios disputados juntos.
  * **Não Direcionado (Ponderado):** Peso da aresta = número de corridas disputadas juntos no Top 3.
  * **Direcionado:** $A \to B$ se o cavalo $A$ terminou à frente do cavalo $B$.
* **Componentes Conexos:** Identificação de subgrupos desconexos (ex.: grupos especialistas em provas de curta distância vs provas clássicas de longa distância).
* **Algoritmo de Dijkstra:** Determina o menor caminho entre dois competidores na rede de rivalidades.
* **Métricas de Centralidade:** Grau (*Degree*), *Betweenness Centrality* (cavalos pontes) e *Closeness Centrality*.

### C. Análise de Hipóteses
* **H1 (Pedigree x Especialização):** Cruzamento de Linhagem do Pai (*Sire*) com o Tipo de Pista (*Turf* vs *Dirt*) e Faixas de Distância (*Sprint*, *Mile*, *Intermediate*, *Long*).
* **H2 (Grau de Rivalidade):** Relação entre a quantidade de adversários distintos enfrentados e a longevidade esportiva.

---

## 5. Como Executar

Abra o terminal (PowerShell ou Prompt de Comando) e navegue até a pasta do projeto:

```bash
cd "C:\Users\Usuario\Desktop\AEDS2_JRA_HorseRacing\src"
```

### Modo Teste Rápido (Validação com o ano de 2005):
```bash
python run_pipeline.py --test
```

### Execução Completa (2002 a 2020 com delay de 2.0s):
```bash
python run_pipeline.py --start-year 2002 --end-year 2020 --delay 2.0 --analyze
```

### Se quiser rodar apenas 2005 a 2015:
```bash
python run_pipeline.py --start-year 2005 --end-year 2015 --delay 2.0 --analyze
```

### Se interromper e quiser continuar só de onde parou:
O comando é exatamente o mesmo! O sistema de checkpoint pula automaticamente tudo o que já foi salvo:
```bash
python run_pipeline.py --start-year 2002 --end-year 2020
```
