# Diagrama do modelo — catálogo canônico temporal (T4.1 / SPEC-1-004)

Todas as entidades têm vigência (`vigencia_inicio` obrigatória, `vigencia_fim` opcional — vazio significa vigente). A vigência vale pela **data da venda**, não pela data de hoje.

```mermaid
erDiagram
    CATALOG_PRODUTOS {
        uuid produto_id PK
        text produto_codigo "PROD-xxx, único por período"
        text produto_nome
        text linha_codigo "LIN-xx"
        text unidade_medida "UN | KG | CX"
        boolean ativo
        date vigencia_inicio
        date vigencia_fim "vazio = vigente"
    }

    CATALOG_CLIENTES {
        uuid cliente_id PK
        text cliente_codigo "CLI-xxx"
        text cliente_nome
        text rede_codigo "opcional"
        date vigencia_inicio
        date vigencia_fim
    }

    CATALOG_RESPONSAVEIS {
        uuid responsavel_id PK
        text responsavel_codigo "SUP-xxx | PROM-xxx"
        text responsavel_tipo "supervisor | promotor"
        text responsavel_rotulo "rótulo sintético, sem PII"
        date vigencia_inicio
        date vigencia_fim
    }

    CATALOG_TERRITORIOS {
        uuid territorio_id PK
        text territorio_codigo "REG-xx"
        text territorio_nome
        date vigencia_inicio
        date vigencia_fim
    }

    CATALOG_VINCULOS {
        uuid vinculo_id PK
        text responsavel_codigo FK
        text territorio_codigo FK
        date vigencia_inicio
        date vigencia_fim
    }

    CATALOG_PENDENCIAS_RESOLUCAO {
        uuid pendencia_id PK
        text tipo "homonimo | lacuna | sobreposicao | sem_vigencia | outro"
        text entidade_tipo "produto | cliente | responsavel | territorio | vinculo"
        text entidade_codigo
        text motivo "obrigatório"
        text status "pendente | resolvida | descartada"
        uuid correlation_id
    }

    CATALOG_RESPONSAVEIS ||--o{ CATALOG_VINCULOS : "responde por"
    CATALOG_TERRITORIOS ||--o{ CATALOG_VINCULOS : "é coberto por"
```

## Garantias do banco

| Garantia                                 | Como o banco garante                                                                                                                                                 |
| ---------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Sem sobreposição silentiosa              | Restrição de exclusão (`EXCLUDE USING gist`): duas vigências do **mesmo código** não podem se cruzar; um território não pode ter dois responsáveis no mesmo período. |
| Vigência coerente                        | `vigencia_fim` nunca anterior a `vigencia_inicio`; vazio = vigente.                                                                                                  |
| Homônimo não é associado automaticamente | Não existe unicidade por **nome** — dois registros podem ter o mesmo nome com códigos diferentes; a escolha é humana.                                                |
| Lacuna/ambiguidade viram pendência       | Tabela `catalog_pendencias_resolucao` com tipo, motivo obrigatório e `correlation_id`.                                                                               |
| Edição controlada                        | RLS: escrever exige a operação `editar_catalogo` (matriz da T1.1); leitura para autenticados.                                                                        |

## Fixtures temporais (arquivo `fixtures/temporal/seed_sintetico.sql`)

Cenários cobertos, todos sintéticos: vigência normal, vigência encerrada, tentativa de sobreposição (o banco recusa), homônimo (mesmo nome, códigos diferentes — vira pendência) e lacuna (período sem responsável — vira pendência). O seed **não é aplicado automaticamente**; será usado pela T4.2 nos testes de resolução.
