-- T4.3 — DDL do catálogo versionado + tabela de auditoria (SPEC-1-004, M-27)
--
-- Por quê: o CREATE das tabelas da T4.1 nunca foi versionado em repositório
-- (do catálogo, só o ALTER da T4.2 estava no repo). Este arquivo fecha a lacuna:
-- o DDL abaixo é o espelho exato do Supabase (fonte da verdade), extraído de
-- information_schema.columns e pg_constraint do projeto ewwjwewjpbqikknjjozb
-- em 30/10/2026. Nas tabelas já existentes (Supabase) é no-op (IF NOT EXISTS);
-- no banco local de auditoria cria as tabelas para rodar a T4.3 sobre a
-- venda_mensal carregada pela T2.3.
-- Diferença deliberada: este arquivo NÃO recria RLS nas tabelas do catálogo —
-- no Supabase elas já têm RLS ativo e o IF NOT EXISTS não as toca; no banco
-- local não há schema auth. A tabela nova auditoria_estrutura tem RLS
-- deny-by-default (nenhuma policy: escrita/leitura oficiais via service role,
-- como nas demais cargas).

-- ============================================================ produtos
create table if not exists public.catalog_produtos (
  produto_id uuid primary key default gen_random_uuid(),
  produto_codigo text not null,
  produto_nome text not null,
  linha_codigo text not null,
  unidade_medida text,
  ativo boolean not null default true,
  vigencia_inicio date not null,
  vigencia_fim date,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  ean text,
  is_panettone boolean not null default false,
  constraint catalog_produtos_codigo_formato check (produto_codigo ~ '^[0-9]{1,9}$'),
  constraint catalog_produtos_linha_formato check (linha_codigo in ('Branca', 'Especiais', 'Panetones')),
  constraint catalog_produtos_nome_obrigatorio check (btrim(produto_nome) <> ''),
  constraint catalog_produtos_ean_formato check (ean is null or ean ~ '^[0-9]{8,14}$'),
  constraint catalog_produtos_vigencia_valida check (vigencia_fim is null or vigencia_fim >= vigencia_inicio),
  constraint catalog_produtos_sem_sobreposicao
    exclude using gist (produto_codigo with =, daterange(vigencia_inicio, coalesce(vigencia_fim, 'infinity'::date), '[)') with &&)
);
create index if not exists catalog_produtos_ean_idx on public.catalog_produtos (ean);

-- ============================================================ clientes
create table if not exists public.catalog_clientes (
  cliente_id uuid primary key default gen_random_uuid(),
  cliente_codigo text not null,
  cliente_nome text not null,
  rede_codigo text,
  vigencia_inicio date not null,
  vigencia_fim date,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  canal text,
  rede text,
  uf text,
  supervisor_codigo text,
  promotor_codigo text,
  constraint catalog_clientes_codigo_formato check (cliente_codigo ~ '^[0-9]{1,9}$'),
  constraint catalog_clientes_nome_obrigatorio check (btrim(cliente_nome) <> ''),
  constraint catalog_clientes_canal_formato check (canal is null or canal in ('Direto', 'Indireto')),
  constraint catalog_clientes_supervisor_formato check (supervisor_codigo is null or supervisor_codigo ~ '^[0-9]{1,9}$'),
  constraint catalog_clientes_promotor_formato check (promotor_codigo is null or promotor_codigo ~ '^[0-9]{1,9}$'),
  constraint catalog_clientes_vigencia_valida check (vigencia_fim is null or vigencia_fim >= vigencia_inicio),
  constraint catalog_clientes_sem_sobreposicao
    exclude using gist (cliente_codigo with =, daterange(vigencia_inicio, coalesce(vigencia_fim, 'infinity'::date), '[)') with &&)
);
create index if not exists catalog_clientes_supervisor_idx on public.catalog_clientes (supervisor_codigo);

-- ============================================================ responsáveis
create table if not exists public.catalog_responsaveis (
  responsavel_id uuid primary key default gen_random_uuid(),
  responsavel_codigo text not null,
  responsavel_tipo text not null,
  responsavel_rotulo text not null,
  vigencia_inicio date not null,
  vigencia_fim date,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint catalog_responsaveis_codigo_formato check (responsavel_codigo ~ '^[0-9]{1,9}$'),
  constraint catalog_responsaveis_tipo check (responsavel_tipo in ('supervisor', 'promotor')),
  constraint catalog_responsaveis_rotulo_obrigatorio check (btrim(responsavel_rotulo) <> ''),
  constraint catalog_responsaveis_vigencia_valida check (vigencia_fim is null or vigencia_fim >= vigencia_inicio),
  constraint catalog_responsaveis_sem_sobreposicao
    exclude using gist (responsavel_codigo with =, daterange(vigencia_inicio, coalesce(vigencia_fim, 'infinity'::date), '[)') with &&)
);

-- ============================================================ auditoria (T4.3, M-27)
-- Cliente ativo sem estrutura válida e SKU vendido sem produto na base.
-- Append-only na prática: cada execução grava com o próprio execucao_id e a
-- reexecução com o mesmo id substitui o conjunto (idempotente).
create table if not exists public.auditoria_estrutura (
  auditoria_id uuid primary key default gen_random_uuid(),
  execucao_id text not null,
  tipo text not null,
  codigo text not null,
  nome text,
  motivo text not null,
  detalhe jsonb,
  created_at timestamptz not null default now(),
  constraint auditoria_estrutura_tipo check (tipo in ('cliente', 'sku'))
);
create index if not exists auditoria_estrutura_execucao_idx on public.auditoria_estrutura (execucao_id);
create index if not exists auditoria_estrutura_tipo_idx on public.auditoria_estrutura (tipo);
alter table public.auditoria_estrutura enable row level security;
-- deny-by-default: nenhuma policy para anon/authenticated. Cargas e auditoria
-- oficiais rodam via service role (fora de RLS), como a carga da T2.2/T2.3.
