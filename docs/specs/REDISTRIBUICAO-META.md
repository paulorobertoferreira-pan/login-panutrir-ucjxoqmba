# Redistribuição de meta entre lojas, supervisores e promotores

**Status:** rascunho para implementação (decisões do Alex, 20/11/2026)
**Escopo:** feature nova do programa, fora das 27 tasks da Fase 2. Aprovada pelo Alex; sem envio à consultora (decisão do Alex).

## 1. Objetivo

O usuário pode **mover parte da meta** de uma unidade (loja, supervisor ou promotor) para outra, sem que o total mude.

## 2. Regras de negócio (decisões do Alex)

| #   | Regra                                                                                                                 | Origem                       |
| --- | --------------------------------------------------------------------------------------------------------------------- | ---------------------------- |
| R1  | A **soma das metas finais** do ciclo fica **exatamente igual** à Meta Diretoria. Não pode passar e não pode diminuir. | Alex, 20/11 (pergunta 1 e 2) |
| R2  | Uma meta inexistente ou zerada só pode ser criada para um **novo cliente**.                                           | Alex, 20/11 (pergunta 1)     |
| R3  | Para cada movimento que cria meta em um novo cliente, o valor **sai de outras unidades** (a soma não muda).           | Alex, 20/11 (pergunta 2)     |
| R4  | A redistribuição **não edita número final**. Ela entra como **versão de parâmetros versionada** (RN-07 / M-31).       | PRD RN-07; AGENTS            |
| R5  | A versão nasce como rascunho com autor e motivo; passa pela execução, reconciliação e aprovação como qualquer ciclo.  | SPEC-2-004                   |

## 3. Cliente novo (decisão do Alex)

O código do cliente existe na base do mês atual e não existe na base do mês imediatamente anterior. Comparam-se duas bases mensais fechadas e completas, pela chave de cliente. Ter venda recente, nunca ter comprado ou ter aparecido com um SKU novo não substitui o teste de presença. O núcleo recebe os dois conjuntos; a integração precisa fornecer as bases corretas. Não se interpreta falta de arquivo como base vazia.

Quem já tinha meta positiva pode receber transferências normalmente. Para partir de zero, o destino precisa ser um cliente novo. Seleções por supervisor ou promotor não criam uma meta independente: a alocação é calculada nas linhas Cliente × SKU e os totais são consolidados a partir delas.

## 4. Validações

- Cada transferência tem origem e destino distintos e valor positivo em centavos. O débito e o crédito são iguais e a origem não pode ficar negativa.
- Origem e destino podem ser loja, supervisor ou promotor, mas não podem se sobrepor nas linhas atingidas. Para criar meta em cliente novo, a nova linha precisa de cliente, SKU, supervisor e promotor validados pelo cadastro na integração. Não se credita uma linha avulsa da hierarquia.
- Os valores são calculados em centavos. O núcleo simula sem salvar, e rejeita uma base já negativa em vez de corrigi-la implicitamente.

## 5. Fechamento da base (opção B)

O resíduo é distribuído em uma **nova versão**, antes das transferências; não se edita a publicação histórica. Para Out/26, o resíduo medido foi R$ 11.742,14 antes da reconciliação das linhas negativas.

**Rateio proporcional aprovado pelo Alex:** só linhas com meta positiva participam, com peso igual à sua participação no total da base. Calcula-se a parcela em centavos inteiros (truncando a magnitude); os centavos restantes vão para a maior combinação Cliente × SKU elegível, com desempate por código do cliente e do SKU. Se for um desconto e a maior linha não tiver saldo para tudo, o desconto segue em ordem decrescente de saldo original. Linhas zeradas não participam; bases negativas precisam ser reconciliadas antes. A soma deve bater exatamente com a Meta Diretoria depois do rateio e de cada transferência.

## 6. Modelo de dados (proposta)

- `redistribuicao_movimento`: `versao_id`, `origem_tipo` (loja | supervisor | promotor), `origem_id`, `destino_tipo`, `destino_id`, `valor`, `motivo`, `autor`.
- A versão de redistribuição usa `parametros_versao` com um parâmetro novo, `P-19 (redistribuicao)`, em `valor_json`.
- Validação de soma e de elegibilidade em função de banco, para que nenhuma versão com movimento inválido seja gravada.

## 7. Critérios de aceite (propostos)

- CA-R1: versão com movimentos que mantêm a soma é aceita; qualquer outra é recusada com motivo.
- CA-R2: destino sem meta só aceito se for novo cliente (leitura escolhida).
- CA-R3: nenhuma linha de meta final é alterada diretamente (teste de RED: UPDATE em `meta_linha` é negado).
- CA-R4: a versão aparece na trilha com autor e motivo.

## 8. Fora de escopo

- Editar número final direto (proibido por RN-07).
- Criar regra nova de elegibilidade para clientes sem nenhuma relação com novos clientes.
- Alterar Out/26 publicada.

## 9. Entrega incremental

A rota `/redistribuir` oferece uma prévia local, sem escrita no banco. Lê a meta publicada sob a política de acesso existente e exige carteira `EMPRESA` no ciclo. Compara dois arquivos `.xlsx` fornecidos pelo operador (uma aba com `cliente_codigo` e `mes_referencia`, em texto AAAA-MM): o mês do ciclo e seu anterior imediato. Confere vigência de loja e produto no cadastro para a primeira meta. A completude dos arquivos é responsabilidade do operador nesta prévia; a efetivação precisa de bases oficiais versionadas e verificadas no servidor.

Para simular um valor entre unidades, a prévia rateia débitos e créditos proporcionalmente às linhas positivas elegíveis. Primeira meta exige selecionar a loja e o produto; a hierarquia vem do catálogo. É possível baixar um JSON não oficial com os movimentos e o motivo. Ainda faltam persistência como versão, revalidação no servidor e fluxo de aprovação/publicação. Nenhuma alteração em produção.
