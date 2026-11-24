# 🎙️ Roteiro Cronometrado de Apresentação (15 a 20 Minutos) — Ciência dos Dados
**Autor:** Arthur De Oliveira Mendonça • **Docente:** Prof. Higor Alexandre Duarte Mascarenhas  
**Pasta da Entrega:** `docs/entrega_ciencia_dados/`

---

## 📁 Arquivos desta Pasta (`docs/entrega_ciencia_dados/`)
1. **[`artigo_ieee_ciencia_dados.tex`](artigo_ieee_ciencia_dados.tex)** — Artigo Científico Completo em formato oficial **IEEE Conference (`IEEEtran`, duas colunas, 9 páginas — dentro do limite de 11/12 páginas)** cobrindo 100% dos itens 1 a 11 do edital.
2. **[`slides_apresentacao_ciencia_dados.tex`](slides_apresentacao_ciencia_dados.tex)** — Slides em **LaTeX Beamer Widescreen (16:9)** compilados automaticamente para PDF pelo GitHub Actions.
3. **[`slides_interativos_apresentacao.html`](slides_interativos_apresentacao.html)** — Slides Interativos em HTML5 Widescreen (use as setas `←` `→` para passar os slides, aperte `F` para Tela Cheia e `N` para abrir/fechar as notas de fala na tela!), com botões diretos para abrir o **Superset Dashboard** e a **TCG Card Arena** ao vivo durante a apresentação!

---

## ⏱️ Cronograma Minuto a Minuto (Meta: 17 a 19 Minutos)

| Tempo | Slide | O que falar e enfatizar para o Prof. Higor |
| :---: | :--- | :--- |
| **00:00 – 01:00** | **Slide 1 (Capa)** | Apresentar o tema: 24 anos de histórico das corridas de elite do Japão (JRA, 2002–2025) integrados com 5 gerações de árvore genealógica (JBIS), com dataset publicado sob DOI oficial no Zenodo (`10.5281/zenodo.23681764`). |
| **01:00 – 02:30** | **Slide 2 (Introdução)** | Explicar por que o turfe japonês é um laboratório perfeito para Ciência dos Dados (alta precisão de tempo, peso do cavalo no dia da corrida, clima, pista e 62 ancestrais por animal), totalizando **3.216 corridas**, **33.409 participações** e **504.074 nós genealógicos**. |
| **02:30 – 04:30** | **Slide 3 (Descrição do Problema & Objetivos)** | Destacar os **4 problemas reais de dados sujos**: (1) Entre 2006 e 2018 a JRA fundiu Sexo+Idade (`性齢`), deslocando as colunas de 25.014 linhas; (2) A árvore de 5 gerações do JBIS estava em ordem BFS enquanto o parser rotulava em DFS; (3) Tradutores comuns falhavam em nomes em Katakana (*Deep Impact*), nomes humanos *Nanori* (*Yutaka Take*) e pelagens biológicas (*Bay*); e (4) A contagem simples de vitórias é cega para a força dos adversários. |
| **04:30 – 07:00** | **Slide 4 (Metodologia, Natureza dos Dados & Ferramentas)** | **Ponto crucial da rubrica (Item 7):** Mostrar a tabela com a natureza de cada dado (Quantitativo Contínuo/Discreto, Qualitativo Ordinal/Nominal). Explicar o que foi feito com as **variáveis categóricas**: *One-Hot* para baixa cardinalidade (`is_turf`), codificação ordinal ponderada para o Grau (`G1=1.0, G2=0.7, G3=0.5`) e **Target Encoding Bayesiano com Janela Temporal Estritamente Anterior** para alta cardinalidade (`jockey`, `sire`, `trainer`) evitando *Data Leakage*. Explicar a adaptação justificada de bibliotecas (Google Gemini API Híbrida + implementação vetorizada em `NumPy/Pandas` + motor **Apache ECharts do Apache Superset 6.1**). |
| **07:00 – 08:15** | **Slide 5 (Top Sires & Top Earners)** | Mostrar os gráficos em `Matplotlib/Seaborn` já 100% traduzidos: a hegemonia de *Deep Impact* (289 filhos Graded) e *Sunday Silence* (281), e os maiores ganhadores (*Almond Eye* ¥19,15B e *Kitasan Black* ¥18,77B). |
| **08:15 – 09:45** | **Slide 6 (Diagrama Sankey Aluvial 4 Estágios)** | Conectar diretamente com a aula de Visualização de Dados do Prof. Higor (*DataViz Project & Apache Superset*): mostrar como o Sankey cruza 4 dimensões simultâneas (*Sire $\to$ Superfície $\to$ Distância $\to$ Grau*), revelando visualmente *Gold Allure/Brian's Time* fluindo para a Areia, *Sakura Bakushin O* para o Sprint e *Deep Impact* para o clássico G1. |
| **09:45 – 11:15** | **Slide 7 (Radar dos Diamantes Injustiçados & Sunburst)** | Mostrar a validação do PageRank ($r = 0,88$ com pódios): explicar o caso de **Sounds of Earth**, que tem **0 vitórias Graded**, mas ficou em **#32 entre 8.135 cavalos** graças a 7 pódios contra lendas de G1! Mostrar o polígono tracejado laranja no Radar (`0%` em vitórias, mas topo em PageRank e volume G1) e o Sunburst de 3 anéis dos 10 hipódromos. |
| **11:15 – 12:45** | **Slide 8 (Streamgraph & Split-Violin Biométrico)** | Mostrar a sucessão das 3 Eras no Streamgraph e destacar a **descoberta biométrica do Split-Violin**: cavalos de Areia (*Dirt*, ~494–498 kg) são **16 a 21 kg mais pesados e musculosos** que os de Grama (*Turf*, ~473–482 kg) em todas as distâncias! |
| **12:45 – 14:00** | **Slide 9 (K-Means++ & PCA 2D)** | Explicar como o PCA 2D capturou **63,4% da variância total** e o K-Means++ dividiu os 106 garanhões em 4 arquétipos zootécnicos perfeitos (Areia, Velocistas, Clássicos G1 e Stayers). |
| **14:00 – 15:30** | **Slide 10 (Random Forest & Testes Qui-Quadrado/ANOVA)** | Mostrar os testes estatísticos ($\chi^2 = 2237,5, p < 10^{-300}$, ANOVA $F = 16,46$) e o resultado da **Random Forest no teste futuro 2016–2018 ($\text{ROC-AUC} = 0,7260$)**, onde a taxa prévia do **Jóquei (29,8%)** e do **Cavalo (22,7%)** lideram a importância de Gini. |
| **15:30 – 16:30** | **Slide 11 (Grafos no Gephi)** | Mostrar os 4 grafos vetoriais no Gephi e a convergência de 5 gerações sobre *Northern Dancer* (4.206 cavalos com inbreeding $F_X$ e 1.211 vitórias). |
| **16:30 – 18:30** | **Slide 12 (Demo Ao Vivo: Superset & TCG Arena)** | **Clicar nos 2 botões na tela:** (1) No **Superset Dashboard**, clicar numa fatia do Sunburst (drill-down) e arrastar um filtro nas Coordenadas Paralelas; (2) Na **TCG Card Arena**, mostrar o card `DIAMOND` do *Sounds of Earth*, clicar no pai dele na árvore genealógica e fazer um **Duelo VS** contra o *Deep Impact*! |
| **18:30 – 20:00** | **Slides 13 e 14 (Repositório, Zenodo & Conclusão)** | Mostrar a estrutura limpa do GitHub + CI/CD + DOI do Zenodo e fechar com as 4 conclusões científicas que respondem à pergunta central do trabalho! |
