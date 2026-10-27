# 📊 Guia Passo a Passo: Configuração dos 4 Grafos no Gephi e Publicação no Zenodo

Foram gerados **4 arquivos `.gexf`** na pasta `data/gephi/`, cada um projetado para um tipo de análise de redes (AEDS 2):

| # | Arquivo | Nós / Arestas | Tipo no Gephi | Objetivo Visual no Artigo |
| :-: | :--- | :---: | :---: | :--- |
| **1** | `competition_network_top150.gexf` | 150 / 2.551 | **Directed** | Elite da JRA com nomes legíveis, tamanho por *PageRank* e cor por linhagem (`sire_group`). |
| **2** | `competition_network_top500.gexf` | 500 / 10.697 | **Directed** | Evolução temporal e comunidades geracionais coloridas por época (`era`). |
| **3** | `lineage_dag_elite.gexf` | 4.475 / 6.042 | **Directed** | Árvore Genealógica (DAG) mostrando os grandes patriarcas (*Sunday Silence*, *Deep Impact*, *King Kamehameha*). |
| **4** | `jockey_horse_trainer_network.gexf` | 405 / 400 | **Undirected** | Rede Tripartida (Jóqueis $\leftrightarrow$ Cavalos $\leftrightarrow$ Treinadores) em constelações. |

---

## 🏆 Grafo 1 e 2: `competition_network_top150.gexf` e `competition_network_top500.gexf`

1. **Importação**: `Graph Type: Directed`.
2. **Tamanho dos Nós (*Appearance $\rightarrow$ Nodes $\rightarrow$ Size $\rightarrow$ Ranking*)**:
   - Atributo: **`pagerank_score`** (ou `earnings_m_yen`).
   - `Min size = 12`, `Max size = 65` $\rightarrow$ **Apply**.
3. **Cor dos Nós (*Appearance $\rightarrow$ Nodes $\rightarrow$ Color $\rightarrow$ Partition*)**:
   - No **Top 150**: escolha **`sire_group`** (colore pelas dinastias paternas: *Deep Impact*, *Sunday Silence*, *King Kamehameha*, *Stay Gold*, *Heart's Cry*, etc.).
   - No **Top 500**: escolha **`era`** (colore pelas 4 épocas cronológicas de 2002 a 2025, mostrando o fluxo do tempo na rede!).
4. **Layout**: **ForceAtlas 2**:
   - Marque `LinLog mode` e `Prevent Overlap`.
   - `Scaling = 15.0`, `Gravity = 1.0`.

---

## 🧬 Grafo 3: `lineage_dag_elite.gexf` (Grafo Acíclico Direcionado de Genealogia — DAG)

Como esse grafo tem **4.475 nós** (incluindo avós e bisavós que só aparecem 1 vez), o segredo para deixá-lo cinematográfico no Gephi é usar o filtro de grau e dimensionar pelo número de filhos no grafo:

1. **Importação**: `File $\rightarrow$ Open` $\rightarrow$ `lineage_dag_elite.gexf` (**Graph Type: Directed**).
2. **DICA DE OURO — Filtrar Ancestrais Isolados (Opcional, deixa o grafo 10x mais limpo)**:
   - No painel direito (**Filters**), abra a pasta **Topology** e arraste **Degree Range** (ou **Out-Degree Range**) para a caixa *Queries* abaixo.
   - Mova a barrinha mínima de `1` para **`2`** (ou **`3`**) e clique no botão **Filter** no canto inferior direito. Isso oculta bisavós que só tiveram 1 descendente e mantém apenas os garanhões, matrizes-chave e campeões G1 conectados!
3. **Tamanho dos Nós (*Appearance $\rightarrow$ Nodes $\rightarrow$ Size $\rightarrow$ Ranking*)**:
   - Escolha o atributo **`progeny_in_dag`** (ou **Out-Degree**).
   - Defina `Min size = 8` e `Max size = 80` $\rightarrow$ **Apply**.
   - *Por quê?* Assim, os grandes patriarcas genéticos (**Sunday Silence(USA)**, **Deep Impact**, **Halo(USA)**, **Northern Dancer(CAN)**, **King Kamehameha**, **Stay Gold**, **Tony Bin(IRE)**) ficam gigantes no centro das galáxias genéticas, e os filhos orbitam ao redor deles!
4. **Cor dos Nós (*Appearance $\rightarrow$ Nodes $\rightarrow$ Color $\rightarrow$ Partition*)**:
   - **Opção A (Papel Biológico)**: Escolha **`node_role`** $\rightarrow$ **Apply**. Ele colore em 4 grupos distintos:
     - `Foundation Sire/Dam` (Patriarcas/Matriarcas com 10+ descendentes)
     - `G1 Champion` (Campeões de G1)
     - `Graded Contender` (Competidores de G2/G3/G1)
     - `Ancestor` (Ancestrais de 2ª/3ª geração)
   - **Opção B (Clãs Genéticos)**: Clique em **Statistics** (painel direito) $\rightarrow$ **Modularity** (Run com `Resolution = 1.0`) e depois em *Nodes $\rightarrow$ Color $\rightarrow$ Partition* escolha **`Modularity Class`** para colorir cada clã familiar automaticamente!
5. **Cor das Arestas (*Appearance $\rightarrow$ Edges $\rightarrow$ Color $\rightarrow$ Partition*)**:
   - Escolha **`relation`** $\rightarrow$ **Apply**.
   - Coloque **Azul** para `Sire Line` (Linha Paterna) e **Rosa/Vermelho** para `Dam Line` (Linha Materna)!
6. **Layout Recomendado**:
   - Comece com **Yifan Hu** (`Optimal Distance = 120`, `Relative Strength = 0.2`) até ele parar sozinho.
   - Depois rode o **ForceAtlas 2** por 5 segundos apenas com **`Prevent Overlap` marcado** e `Scaling = 20.0` para separar as bolinhas.

---

## 🤝 Grafo 4: `jockey_horse_trainer_network.gexf` (Rede Tripartida: Jóqueis, Cavalos e Treinadores)

Esse grafo mostra as "panelinhas" (sinergias de estábulos e montarias fiéis) entre **Jóqueis**, **Cavalos** e **Treinadores**:

1. **Importação**: `File $\rightarrow$ Open` $\rightarrow$ `jockey_horse_trainer_network.gexf` (**Graph Type: Undirected**).
2. **Cor dos Nós (*Appearance $\rightarrow$ Nodes $\rightarrow$ Color $\rightarrow$ Partition*)**:
   - Escolha o atributo **`entity_type`** $\rightarrow$ **Apply**.
   - Escolha 3 cores bem contrastantes para as 3 classes da rede tripartida:
     - **`Jockey`** (ex.: Dourado / Amarelo)
     - **`Horse`** (ex.: Azul Ciano)
     - **`Trainer`** (ex.: Roxo / Verde)
3. **Tamanho dos Nós (*Appearance $\rightarrow$ Nodes $\rightarrow$ Size $\rightarrow$ Ranking*)**:
   - Escolha o atributo **`size_metric`** (ou **`Degree`**).
   - Defina `Min size = 12` e `Max size = 55` $\rightarrow$ **Apply**.
   - Os jóqueis mais ativos (*Yutaka Take*, *Yuichi Fukunaga*, *Yutaka Yoshida*, *Masayoshi Ebina*, *Norihiro Yokoyama*) e os cavalos de elite ficam maiores.
4. **Cor das Arestas (*Appearance $\rightarrow$ Edges $\rightarrow$ Color $\rightarrow$ Partition*)**:
   - Escolha o atributo **`interaction`** $\rightarrow$ **Apply**.
   - Isso diferencia visualmente as arestas `Jockey-Horse Ride` (Montaria em corrida) das arestas `Jockey-Trainer Team` (Parceria de estábulo Jóquei-Treinador).
5. **Layout Recomendado**:
   - Escolha **ForceAtlas 2**:
     - Marque **`Dissuade Hubs`** (importantíssimo em grafos bipartidos/tripartidos! Ele empurra os grandes jóqueis para longe uns dos outros, formando constelações perfeitas ao redor de cada jóquei) e **`Prevent Overlap`**.
     - Defina `Scaling = 12.0` e `Gravity = 1.5`.
     - Clique em **Run** por 10 segundos e depois **Stop**.
6. **Rótulos (*Labels*)**:
   - Ative o botão **`T`** na barra inferior e escolha **Size: Node size**. Como o atributo `label` já está limpo (sem o prefixo `"Jockey:"` ou `"Horse:"`), os nomes aparecem prontos para exportar!

---

## 🌐 Como Publicar o Dataset no Zenodo (DOI Oficial)

### Opção A: Integração Automática GitHub $\leftrightarrow$ Zenodo (Recomendada)
1. Faça login em `https://zenodo.org` usando sua conta do **GitHub**.
2. No menu do seu perfil (canto superior direito), clique em **GitHub**.
3. Encontre o repositório `ImArthz/AEDS2_jra_analysis` e mude a chave para **ON**.
4. Como já deixamos o arquivo `zenodo/.zenodo.json` configurado, basta criar uma Release no GitHub que o Zenodo gera automaticamente o **DOI oficial** para você citar no artigo!

### Opção B: Upload Manual Direto no Zenodo
1. Acesse `https://zenodo.org/uploads/new`.
2. Arraste os arquivos de `data/csv_en/`, `data/csv/`, `data/gephi/`, `data/analysis/` e `data/sqlite/jra_graded_en.db`.
3. Copie o título, descrição e palavras-chave do arquivo `zenodo/.zenodo.json`, selecione **Dataset** e licença **CC-BY 4.0**, e clique em **Publish**.
