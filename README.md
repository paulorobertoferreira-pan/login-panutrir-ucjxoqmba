# Panutrir — Sistema de Metas

App React + Supabase do programa Adapta Native (EMENDA 02/2026).

## O que tem aqui

| Pasta | Conteúdo |
|---|---|
| `src/` | App React (login e telas da intranet) |
| `supabase/migrations/` | **Todas** as migrations do banco, em ordem cronológica |
| `contracts/` | Contratos de dados (JSON) e validadores/scripts de carga (Python) |
| `fixtures/` | Fixtures sintéticas para os testes dos contratos |

## Migrations

As migrations de negócio viviam só no repositório de documentação
(`kimberlyPrest/Panutrir---Adapta-Native`) e no histórico do banco. Desde
25/10/2026 estão aqui — restauração do zero voltou a ser possível:

```
git clone https://github.com/paulorobertoferreira-pan/login-panutrir-ucjxoqmba.git
supabase db push        # ou aplique os .sql na ordem dos timestamps
```

Ordem: `20260915123000` (auth) → `20261024150000` (parâmetros T3.1) →
`20261024150100` (seed Out/26) → `20261024180000` (venda_mensal T2.2).

## Contratos e carga

O contrato `vendas` v2.0.0 define as 22 colunas das congeladas; o script
`contracts/carga_vendas.py` lê a exportação, agrega por mês × cliente × SKU
e grava em `venda_mensal` numa única transação (idempotente por mês).

```
export DATABASE_URL='postgresql://...'
python3 contracts/carga_vendas.py <arquivo.csv|.xlsx> --executado-por "Nome"
```

Suítes de teste: `testes_t21c.py` (32 verificações), `testes_t22.py` (15),
`testes_t31.py`. Rodam contra um Postgres de teste, nunca o de produção.

## Documentação e método

O método do programa (SPECs, matriz de tasks, changelog, atas) fica no
repositório de documentação: `kimberlyPrest/Panutrir---Adapta-Native`,
pasta `panutrir-cliente/`. Este repositório é só código executável.

## Segurança

- `.env` versionado contém apenas `VITE_SUPABASE_URL` e a chave `anon`
  (pública por design). Nenhuma credencial de serviço aqui.
- A conexão de carga vem de `DATABASE_URL` — nunca colocar senha em código.
- Dados reais de venda ficam só no Supabase; nunca commitar planilhas.
