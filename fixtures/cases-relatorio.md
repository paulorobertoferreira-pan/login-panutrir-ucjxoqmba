# Relatório de casos — T2.1 / SPEC-1-002 (revisão T2.1b)

**Versão do catálogo:** 1.1.0 (revisão T2.1b — EMENDA 01/2026)  
**Status:** fixtures sintéticas da Fase 1  
**Fonte:** contratos versionados em `contracts/`  
**Metodologia oficial:** `06_notas/2026-09-23-metodologia-oficial-ago-2026.md` (rastreabilidade bloco a bloco em `contracts/catalogo-schemas.json`)  
**Bloqueio de dados reais:** os CSVs reais permanecem fora do projeto até revalidação no Gate G1.

## Casos válidos

| Caso  | Arquivo                                                          | Resultado esperado          | Observação                                                                 |
| ----- | ---------------------------------------------------------------- | --------------------------- | -------------------------------------------------------------------------- |
| V-001 | `fixtures/synthetic/valid/vendas.csv`                            | Aceitar                     | 3 linhas, vírgula, UTF-8, cabeçalho completo; inclui venda líquida e canal |
| V-002 | `fixtures/synthetic/valid/vendas_reenvio_identico.csv`           | Aceitar como mesmo conteúdo | Fixture byte a byte igual a V-001; a idempotência será comprovada em T2.2  |
| V-003 | `fixtures/synthetic/valid/metas_atingimentos.csv`                | Aceitar                     | 3 linhas, ciclo `2026-01`                                                  |
| V-004 | `fixtures/synthetic/valid/produtos.csv`                          | Aceitar                     | 3 produtos, vigência aberta e encerrada; inclui `linha_tipo`               |
| V-005 | `fixtures/synthetic/valid/estrutura_comercial.csv`               | Aceitar                     | 3 atribuições, vírgula                                                     |
| V-006 | `fixtures/synthetic/valid/estrutura_comercial_ponto_virgula.csv` | Aceitar                     | Mesmo contrato, ponto e vírgula                                            |
| V-007 | `fixtures/synthetic/valid/parametros_calculo.csv`                | Aceitar                     | 8 parâmetros da metodologia oficial, valores sintéticos, origem SINTETICO  |

## Casos inválidos

| Caso  | Arquivo/entrada                           | Motivo da rejeição                                           | Resultado esperado                 |
| ----- | ----------------------------------------- | ------------------------------------------------------------ | ---------------------------------- |
| I-001 | `vendas_coluna_obrigatoria_ausente.csv`   | Falta `produto_codigo`                                       | Rejeitar antes do staging          |
| I-002 | `vendas_formula_perigosa.csv`             | Campo textual começa por `=`                                 | Rejeitar e registrar motivo        |
| I-003 | `vendas_vazia.csv`                        | Conteúdo vazio                                               | Rejeitar sem inferência silenciosa |
| I-004 | `vendas_quantidade_negativa.csv`          | `quantidade` abaixo do mínimo                                | Rejeitar e manter estado anterior  |
| I-005 | `metas_tipo_invalido.csv`                 | `meta_valor` não é decimal                                   | Rejeitar por tipo                  |
| I-006 | `produtos_formula_perigosa.csv`           | `produto_nome` começa por `=`                                | Rejeitar e registrar motivo        |
| I-007 | `produtos_vigencia_invertida.csv`         | Fim da vigência anterior ao início                           | Rejeitar por regra entre campos    |
| I-008 | `estrutura_chave_duplicada.csv`           | `estrutura_id` repetido                                      | Rejeitar duplicidade crítica       |
| I-009 | `estrutura_delimitador_nao_suportado.csv` | Usa o caractere barra vertical, que não é delimitador aceito | Rejeitar por delimitador           |
| I-010 | Nome `../vendas.csv`                      | Tentativa de path traversal                                  | Rejeitar pelo nome, antes de ler   |
| I-011 | Nome `vendas.txt`                         | Extensão diferente de `.csv`                                 | Rejeitar pelo nome                 |
| I-012 | Conteúdo com bytes fora de UTF-8          | Encoding inválido                                            | Rejeitar antes do schema           |
| I-013 | Arquivo maior que 1 MiB                   | Limite de tamanho excedido                                   | Rejeitar sem alterar staging       |
| I-014 | Interrupção durante gravação              | Falha transacional simulada                                  | Fazer rollback e preservar staging |
| I-015 | `vendas_valor_liquido_inconsistente.csv`  | `valor_liquido` ≠ bruto − devoluções − tributos              | Rejeitar por regra entre campos    |
| I-016 | `vendas_canal_invalido.csv`               | `canal_venda` fora do conjunto DIRETO/INDIRETO               | Rejeitar por enum                  |
| I-017 | `produtos_linha_tipo_invalido.csv`        | `linha_tipo` fora do conjunto BRANCO/ESPECIAL/OUTRA          | Rejeitar por enum                  |
| I-018 | `parametros_chave_duplicada.csv`          | `parametro_id` repetido                                      | Rejeitar duplicidade crítica       |
| I-019 | `parametros_versao_invalida.csv`          | `versao_parametro` zero (mínimo é 1)                         | Rejeitar por regra de campo        |
| I-020 | `parametros_origem_oficial_bloqueada.csv` | `origem` OFICIAL antes dos Gates G1–G3                       | Rejeitar por política de dados     |

## Mapa contrato → cobertura

| Contrato              | Válidos | Inválidos | Campos-chave cobertos                                                                              |
| --------------------- | ------: | --------: | -------------------------------------------------------------------------------------------------- |
| `vendas`              |       2 |         6 | período, cliente, produto, quantidade, valor bruto/líquido, devoluções, tributos, canal, estrutura |
| `metas_atingimentos`  |       1 |         1 | ciclo, dimensões comerciais, meta e atingimento                                                    |
| `produtos`            |       1 |         3 | código, linha, tipo de linha (Branco/Especial), unidade, ativo e vigência                          |
| `estrutura_comercial` |       2 |         2 | supervisor, promotor, região e vigência                                                            |
| `parametros_calculo`  |       1 |         3 | parâmetro, valor, unidade, versão, origem e vigência                                               |

## Cobertura da metodologia oficial (T2.1b)

| Bloco da metodologia                  | Insumo garantido nos contratos                                                         |
| ------------------------------------- | -------------------------------------------------------------------------------------- |
| 1. Venda líquida                      | `vendas` v1.1.0: `valor_venda`, `devolucoes`, `tributos`, `valor_liquido`              |
| 2. IS sazonal por mediana             | histórico mensal por região/supervisor/promotor (vendas + estrutura)                   |
| 3. Baseline 24 meses (35/30/35)       | histórico 24 meses + `parametros_calculo` (pesos)                                      |
| 4. G 40/60                            | `parametros_calculo`: `peso_g1`, `peso_g2`                                             |
| 5. GAP Diretoria                      | `parametros_calculo`: `gap_diretoria`                                                  |
| 6. Mix 5,5% indireto                  | `vendas` v1.1.0: `canal_venda` + `parametros_calculo`: `mix_indireto`                  |
| 7. Branco/Especial (convergência 50%) | `produtos` v1.1.0: `linha_tipo` + `parametros_calculo`: `convergencia_branco_especial` |
| 8. Reconciliação bloqueante           | exigência de T6.2 (CA-1-07a); insumos garantidos pelos contratos acima                 |

## Baseline RED e resultado da T2.1b

- **RED antes da revisão:** os contratos v1.0.0 não garantiam venda líquida (só `valor_venda` bruto), não identificavam canal direto × indireto, não classificavam linha Branco/Especial e não tinham estrutura versionada de parâmetros do cálculo — o cálculo oficial da meta não teria todos os insumos.
- **Resultado após a revisão:** vendas e produtos em v1.1.0 com os novos campos, contrato `parametros_calculo` v1.0.0 criado, catálogo v1.1.0 com rastreabilidade bloco a bloco, 7 fixtures válidas e 20 casos inválidos/limítrofes.
- **Limite:** o parser, cálculo de SHA-256, upload, staging transacional, idempotência e rollback continuam sendo executados nas tasks T2.2 e T2.3. A T2.1b não grava nenhum CSV no banco. Os valores oficiais dos parâmetros só entram versionados na T6.2, após os Gates G1–G3.
