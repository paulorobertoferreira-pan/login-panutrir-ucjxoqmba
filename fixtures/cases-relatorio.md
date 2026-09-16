# Relatório de casos — T2.1 / SPEC-1-002

**Versão do catálogo:** 1.0.0  
**Status:** fixtures sintéticas da Fase 1  
**Fonte:** contratos versionados em `contracts/`  
**Bloqueio de dados reais:** os CSVs reais permanecem fora do projeto até revalidação no Gate G1.

## Casos válidos

| Caso  | Arquivo                                                          | Resultado esperado          | Observação                                                                |
| ----- | ---------------------------------------------------------------- | --------------------------- | ------------------------------------------------------------------------- |
| V-001 | `fixtures/synthetic/valid/vendas.csv`                            | Aceitar                     | 3 linhas, vírgula, UTF-8, cabeçalho completo                              |
| V-002 | `fixtures/synthetic/valid/vendas_reenvio_identico.csv`           | Aceitar como mesmo conteúdo | Fixture byte a byte igual a V-001; a idempotência será comprovada em T2.2 |
| V-003 | `fixtures/synthetic/valid/metas_atingimentos.csv`                | Aceitar                     | 3 linhas, ciclo `2026-01`                                                 |
| V-004 | `fixtures/synthetic/valid/produtos.csv`                          | Aceitar                     | 3 produtos, vigência aberta e encerrada                                   |
| V-005 | `fixtures/synthetic/valid/estrutura_comercial.csv`               | Aceitar                     | 3 atribuições, vírgula                                                    |
| V-006 | `fixtures/synthetic/valid/estrutura_comercial_ponto_virgula.csv` | Aceitar                     | Mesmo contrato, ponto e vírgula                                           |

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

## Mapa contrato → cobertura

| Contrato              | Válidos | Inválidos | Campos-chave cobertos                                                      |
| --------------------- | ------: | --------: | -------------------------------------------------------------------------- |
| `vendas`              |       2 |         4 | período, cliente, produto, quantidade, valor, supervisor, promotor, região |
| `metas_atingimentos`  |       1 |         1 | ciclo, dimensões comerciais, meta e atingimento                            |
| `produtos`            |       1 |         2 | código, linha, unidade, ativo e vigência                                   |
| `estrutura_comercial` |       2 |         2 | supervisor, promotor, região e vigência                                    |

## Baseline RED e resultado da T2.1

- **RED antes da entrega:** o projeto não possuía contratos, catálogo de schemas nem fixtures CSV versionadas; não havia como provar o formato ou os casos inválidos.
- **Resultado após a entrega:** quatro contratos, catálogo versionado, seis fixtures válidas e quatorze casos inválidos/limítrofes foram criados e ligados por relatório.
- **Limite:** o parser, cálculo de SHA-256, upload, staging transacional, idempotência e rollback serão executados nas tasks T2.2 e T2.3. A T2.1 não grava nenhum CSV no banco.
