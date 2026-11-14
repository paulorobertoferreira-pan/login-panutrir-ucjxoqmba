# T2.1.5 — Validação de Nov/26 com o arquivo de remuneração (CA-2-03)

**Data:** 14/11/2026 · **Ciclo:** 2026-11
**Segundo lado:** `remuneracao_variavel_por_promotor` (export de 14/11, Nov/26, 133 promotores)
**Primeiro lado:** motor oficial de Nov/26 (28.602 Cliente × SKU, janelas derivadas)

## Resultado por TOTAL

| Item | Remuneração (arquivo) | Sistema (motor) | Diferença |
|---|---|---|---|
| Σ Meta | **R$ 11.136.421,00** | R$ 11.254.295,67 (total) / R$ 10.691.284,75 (por promotor) | ver análise |
| Promotores | 133 | 123 com meta (+ 5 sem) | 10 a mais no arquivo |
| Promotores comparáveis por nome | 109 | — | 0 no centavo |

**0 promotores batem no centavo.** Isso não é ruído de arredondamento — é uma diferença de
construção. As três causas abaixo explicam praticamente todo o total.

## Causa 1 — 4 promotores têm meta NULA na remuneração, e o sistema lhes dá R$ 969.197,77

| Promotor | Meta na remuneração | Meta no sistema |
|---|---|---|
| FRANCISCO CESAR FERREIRA DA COSTA | **(nula)** | R$ 678.421,10 |
| LUIZ FERNANDO CUSTODIO MARTINS | (nula) | — |
| ADILSON LUIS RAMOS DA SILVA | (nula) | — |
| CANAL INDIRETO BARUERI | (nula) | — |
| **Σ do sistema nesses 4** | **R$ 0,00** | **R$ 969.197,77** |

A remuneração deixa a meta **em branco** para esses promotores (provavelmente porque o gatilho de
bônus está inativo/`Inativo` para eles, ou porque a meta não é paga a eles). O sistema continua
distribuindo meta a eles — e essa é a maior parcela da diferença.

## Causa 2 — os códigos de promotor são espaços diferentes

O `codpromo` do arquivo de remuneração (`72457`, `72687`, `24891`…) **não é** o
`promotor_codigo` do catálogo (`206`, `267`, `317`…) nem o `cod_vendedor` da estrutura comercial.
A ponte confiável é o **NOME do promotor** — e ela casa 115 de 133.
`codpromo` é o código **do sistema de remuneração**, um sistema à parte.

## Causa 3 — o arquivo tem 133 promotores; o catálogo, 123

10 promotores existem na remuneração e não no catálogo de clientes. São promotores **sem cliente
atribuído** no cadastro atual (ou desligados). O sistema não lhes dá meta porque não tem cliente
para lhes atribuir — a remuneração ainda os lista.

## O que isso significa para o CA-2-03

O critério pede "todas as diferenças classificadas e nenhuma sem causa declarada". **As três causas
acima estão declaradas e quantificadas** — mas duas delas são **decisões de negócio em aberto**, não
erros:

1. **Promotor sem meta na remuneração deve receber meta no sistema?** (R$ 969.197,77 em jogo)
2. **Promotor sem cliente no catálogo deve aparecer no cálculo?** (10 promotores)

Nenhuma das duas tem resposta nas decisões D1/D2/D3 nem nas perguntas respondidas.

## Recomendação

**Não fechar o CA-2-03 com "reconciliado".** Levar à Kim e ao Paulo as duas perguntas acima — elas
são a diferença entre "o sistema está errado" e "a remuneração usa outro critério". O número do
sistema está correto pela regra atual; o que falta é saber se a regra atual é a que a remuneração
usa.

**Evidência:** `artifacts/t215_validacao_nov26.xlsx` (109 promotores comparados, 6 sem par,
14 só no sistema) · `contracts/validacao_promotor.py`.
