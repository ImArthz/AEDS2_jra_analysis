# 🏇 JRA Graded Races & JBIS Pedigree Analysis (AEDS 2)

<div align="center">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.13-blue.svg">
  <img alt="SQLite" src="https://img.shields.io/badge/SQLite-Database-lightgrey.svg">
  <img alt="NetworkX" src="https://img.shields.io/badge/NetworkX-Graph_Theory-green.svg">
  <img alt="Status" src="https://img.shields.io/badge/Status-Stable%20(2002--2025)-brightgreen">
</div>

<br/>

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
Gera relatórios de integridade referencial automáticos e dispara alertas em caso de anomalias (e.g., valores ausentes devido a raspagens falhas) nas relações entre Tabelas de Cavalo e Resultados.

### 4. Dicionário de Tradução Dinâmica (JP -> EN)
Módulo que converte dinamicamente terminologias de pista (`良` -> `Firm`) e clima do formato codificado japonês para a taxonomia esportiva universal em Inglês. Essencial para treinar futuros algoritmos de Inteligência Artificial sem viés de idioma.

### 5. Engine Analítica de Grafos
- **Grafos Direcionados Acíclicos (DAG):** Mapeamento genético focado na árvore ascendente dos animais (útil para Lowest Common Ancestor).
- **Grafos Bipartidos e de Centralidade:** Conexão direta entre jóqueis e cavalos. Utilização do algoritmo **PageRank** da Google adaptado para o ecossistema das corridas, onde enfrentar vencedores históricos também confere peso e autoridade a um atleta.

---

## 📊 Estrutura de Dados & Relatórios
Todo o projeto foi espelhado dinamicamente entre arquivos `.csv` estáticos na pasta `data/csv/` e um banco SQLite `jra_graded.db`.

📄 **Relatório Técnico Completo:**
Elaborei um documento minucioso explicando minha arquitetura, os erros que contornei (como blocos de IP e restrições silenciosas do banco) no formato `LaTeX`. O arquivo renderizado e o código-fonte encontram-se no diretório `docs/relatorio_extracao.tex`.

---

## 🚀 Como Iniciar

1. Clone o repositório na sua máquina local.
2. Dê um duplo clique no arquivo facilitador **`run_full.bat`** no Windows, ou execute:
   ```bash
   cd src
   python run_pipeline.py --start-year 2002 --end-year 2025 --analyze
   ```
3. O sistema reconhecerá instantaneamente de onde parou e continuará a construir seu grafo de conhecimento com segurança total.

---

<div align="center">
  <i>Desenvolvido com ☕ e focado na interseção entre Esportes, Biologia e Dados.</i>
</div>
