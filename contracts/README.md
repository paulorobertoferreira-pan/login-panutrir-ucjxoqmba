# Contratos e fixtures sintéticas — Fase 1

Esta pasta contém somente contratos e dados fictícios da Fase 1. Nenhum CSV real da Panutrir é usado, copiado ou referenciado aqui.

## Regras comuns dos quatro contratos

- Extensão obrigatória: `.csv`.
- Codificação aceita: UTF-8 estrito; BOM é opcional.
- Delimitadores aceitos: vírgula (`,`) e ponto e vírgula (`;`).
- Aspas de campo: aspas duplas (`"`), quando necessárias.
- Quebra de linha: LF ou CRLF.
- Cabeçalho obrigatório na primeira linha; nomes são sensíveis a maiúsculas/minúsculas.
- Cabeçalhos duplicados, colunas desconhecidas e colunas obrigatórias ausentes são rejeitados.
- Limites abaixo são **limites das fixtures da Fase 1**, não limites produtivos: 1 MiB, 10.000 linhas de dados e 20 colunas.
- Números decimais usam ponto como separador e duas casas quando indicado; separador de milhar não é aceito.
- Campos textuais que começam por `=`, `+`, `-`, `@`, tabulação ou retorno de carro são rejeitados como conteúdo perigoso. Valores numéricos negativos também são rejeitados quando o contrato define mínimo zero.
- Caminhos, componentes `..`, barras e extensões diferentes de `.csv` não fazem parte de um nome de arquivo válido.
- Datas usam `YYYY-MM-DD`; mês de referência usa `YYYY-MM`.
- Códigos, nomes e valores presentes nas fixtures são sintéticos e não representam pessoas, clientes ou produtos reais.

## Arquivos

- `vendas.json` (v1.1.0): fatos de venda por período, cliente, produto e estrutura comercial. Revisado pela T2.1b: inclui `valor_venda` (bruto), `devolucoes`, `tributos`, `valor_liquido` (venda líquida, bloco 1 da metodologia oficial) e `canal_venda` (DIRETO/INDIRETO, bloco 6).
- `metas_atingimentos.json`: meta e atingimento sintéticos por ciclo e dimensões comerciais.
- `produtos.json` (v1.1.0): catálogo mínimo de produtos para os testes de importação. Revisado pela T2.1b: inclui `linha_tipo` (BRANCO/ESPECIAL/OUTRA, bloco 7 da metodologia oficial).
- `estrutura_comercial.json`: responsáveis, regiões e vigências sintéticas.
- `parametros_calculo.json` (novo na T2.1b): estrutura versionada dos parâmetros do cálculo oficial (pesos 35/30/35, G 40/60, GAP Diretoria, mix 5,5%, convergência 50%). Na Fase 1 somente valores sintéticos; valores oficiais só na T6.2, após os Gates G1–G3.
- `catalogo-schemas.json` (v1.1.0): índice versionado dos cinco contratos e suas fixtures, com rastreabilidade bloco a bloco da metodologia oficial.
