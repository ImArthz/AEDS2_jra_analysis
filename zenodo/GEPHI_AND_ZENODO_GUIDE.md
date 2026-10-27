# 📊 Guia Passo a Passo: Como Abrir e Estilizar os Grafos no Gephi e Publicar no Zenodo

## Parte 1 — Usando os Arquivos `.gexf` no Gephi (v0.10+)

Foram gerados **4 arquivos `.gexf`** na pasta `data/gephi/`, já com todos os atributos matemáticos pré-calculados:

| Arquivo | Nós | Descrição Recomendada |
| :--- | :---: | :--- |
| `competition_network_top150.gexf` | 150 | **Ideal para visualização limpa com nomes visíveis**. Contém os 150 maiores cavalos da história moderna da JRA ranqueados por PageRank. |
| `competition_network_top500.gexf` | 500 | **Ideal para Detecção de Comunidades (Modularidade / Louvain)** e análise macro de gerações (2002–2025). |
| `lineage_dag_elite.gexf` | ~1.800 | **Grafo Acíclico Direcionado (DAG) de Genealogia**. Conecta Ancestral $\rightarrow$ Descendente para todos os campeões G1 e elites. |
| `jockey_horse_trainer_network.gexf` | ~350 | **Rede Bipartida/Tripartida** das maiores parcerias Jóquei $\leftrightarrow$ Cavalo e Jóquei $\leftrightarrow$ Treinador. |

### Passo a Passo no Gephi:
1. Abra o **Gephi** $\rightarrow$ `File` $\rightarrow$ `Open...` e selecione `data/gephi/competition_network_top150.gexf`.
2. Na janela de importação, mantenha **Graph Type: Directed** e clique em **OK**.
3. **Tamanho dos Nós (Node Size)**:
   - No painel esquerdo (**Appearance** $\rightarrow$ **Nodes** $\rightarrow$ ícone de círculos concêntricos *Size* $\rightarrow$ **Ranking**):
   - Escolha o atributo **`pagerank_score`** (ou `earnings_m_yen` / `g1_wins`).
   - Defina `Min size = 12` e `Max size = 65` $\rightarrow$ clique em **Apply**.
4. **Cor dos Nós (Node Color)**:
   - No painel **Appearance** $\rightarrow$ **Nodes** $\rightarrow$ ícone de paleta *Color* $\rightarrow$ **Partition**:
   - Escolha **`sire_group`** (para colorir pela linhagem paterna: *Deep Impact*, *Sunday Silence*, *King Kamehameha*, *Stay Gold*, etc.) ou **`era`** (para colorir por época histórica).
   - Clique em **Apply**.
5. **Algoritmo de Layout (Disposição Espacial)**:
   - No painel inferior esquerdo (**Layout**), selecione **ForceAtlas 2**:
     - Marque `Prevent Overlap` (Evitar sobreposição) e `LinLog mode`.
     - Defina `Scaling = 15.0` e `Gravity = 1.0`.
     - Clique em **Run** por 10 a 15 segundos e depois em **Stop**.
6. **Exibir os Nomes dos Cavalos**:
   - Na barra inferior da aba *Overview*, clique no ícone **`T` (Show Node Labels)** e marque **Size: Node size** para que os nomes das lendas (*Equinox*, *Almond Eye*, *Orfevre*, *Deep Impact*) fiquem proporcionais ao seu PageRank!
7. **Exportar em Alta Resolução (PDF/PNG/SVG)**:
   - Vá na aba **Preview** (no topo), selecione o Preset **Default Curved**, marque `Show Labels`, clique em **Refresh** e depois em **Export: SVG/PDF/PNG** no canto inferior esquerdo.

---

## Parte 2 — Como Publicar o Dataset no Zenodo (DOI Oficial)

Você tem duas formas super rápidas de publicar no [Zenodo](https://zenodo.org/):

### Opção A: Integração Automática GitHub $\leftrightarrow$ Zenodo (Recomendada)
1. Faça login em `https://zenodo.org` usando sua conta do **GitHub**.
2. No menu do seu perfil (canto superior direito), clique em **GitHub**.
3. Encontre o repositório `ImArthz/AEDS2_jra_analysis` e mude a chave para **ON**.
4. Como já deixamos o arquivo `zenodo/.zenodo.json` configurado, basta criar uma Release no GitHub (ou usar as tags automáticas) que o Zenodo gera automaticamente o **DOI oficial** para você citar no artigo!

### Opção B: Upload Manual Direto no Zenodo
1. Acesse `https://zenodo.org/uploads/new`.
2. Arraste os arquivos de `data/csv_en/`, `data/csv/`, `data/gephi/` e `data/sqlite/jra_graded_en.db`.
3. Copie o título, descrição e palavras-chave do arquivo `zenodo/.zenodo.json`, selecione **Dataset** e licença **CC-BY 4.0**, e clique em **Publish**.
