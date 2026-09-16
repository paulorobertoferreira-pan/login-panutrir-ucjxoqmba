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

- `vendas.json`: fatos de venda por período, cliente, produto e estrutura comercial.
- `metas_atingimentos.json`: meta e atingimento sintéticos por ciclo e dimensões comerciais.
- `produtos.json`: catálogo mínimo de produtos para os testes de importação.
- `estrutura_comercial.json`: responsáveis, regiões e vigências sintéticas.
- `catalogo-schemas.json`: índice versionado dos quatro contratos e suas fixtures.
