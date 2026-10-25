-- T2.2 / SPEC-1-002 — Carga agregada mensal de vendas e registro de carga.
-- Granularidade: mes × cod_cliente × cod_sku. Uma linha por combinação.
-- Sem isso o volume estoura o banco (1,28 M linhas de nota virariam 1,28 M registros).
--
-- Regras que a estrutura sustenta (ver SPEC-1-002):
--   CA-1-05  recarga de um mês não duplica nem toca nos outros; interrupção não deixa mês parcial
--            → a chave única impede duplicata; a carga apaga+insere o mês dentro de UMA transação
--   CA-1-06  cada carga tem registro com hash, contagens, totais e rejeições com motivo
--            → tabela carga_registro
--   M-02     venda_liquida = vlritens - vlrdesc - vlrtroca, podendo ser negativa (estorno)
--            → coluna gerada, não calculada à mão em cada consulta

-- ---------------------------------------------------------------- venda agregada
create table if not exists public.venda_mensal (
  venda_mensal_id uuid primary key default gen_random_uuid(),
  mes             date not null,
  cod_cliente     integer not null,
  cod_sku         integer not null,
  vlritens        numeric(18,2) not null default 0,
  vlrdesc         numeric(18,2) not null default 0,
  vlrtroca        numeric(18,2) not null default 0,
  qtdade          numeric(18,3) not null default 0,
  -- M-02 como coluna gerada: sempre consistente, impossível divergir na gravação
  venda_bruta     numeric(18,2) generated always as (vlritens) stored,
  venda_liquida   numeric(18,2) generated always as (vlritens - vlrdesc - vlrtroca) stored,
  carga_id        uuid,
  criado_em       timestamptz not null default now(),
  atualizado_em   timestamptz not null default now(),
  -- a chave é o que garante CA-1-05: não existe segunda linha para o mesmo mês/cliente/SKU
  constraint venda_mensal_chave unique (mes, cod_cliente, cod_sku),
  constraint venda_mensal_codigos_ck check (cod_cliente > 0 and cod_sku > 0),
  constraint venda_mensal_mes_ck check (mes = date_trunc('month', mes)::date)
);

comment on table public.venda_mensal is
  'T2.2/SPEC-1-002: venda agregada por mes x cliente x SKU. Uma linha por combinação (CA-1-05).';
comment on column public.venda_mensal.venda_liquida is
  'M-02: vlritens - vlrdesc - vlrtroca. Coluna gerada. Pode ser negativa (estorno) — nunca truncar.';
comment on column public.venda_mensal.mes is
  'Sempre o primeiro dia do mês; a constraint impede gravar dia solto.';

-- ---------------------------------------------------------------- registro de carga
create table if not exists public.carga_registro (
  carga_id          uuid primary key default gen_random_uuid(),
  arquivo_nome      text not null,
  arquivo_hash      text not null,
  arquivo_bytes     bigint,
  meses_afetados    text[] not null default '{}',
  linhas_lidas      integer not null default 0,
  linhas_agregadas  integer not null default 0,
  linhas_rejeitadas integer not null default 0,
  rejeicoes         jsonb not null default '{}'::jsonb,
  totais_por_mes    jsonb not null default '{}'::jsonb,
  executado_por     text not null,
  iniciado_em       timestamptz not null default now(),
  concluido_em      timestamptz,
  status            text not null default 'em_andamento',
  erro              text,
  constraint carga_registro_status_ck
    check (status in ('em_andamento', 'concluida', 'falhou')),
  constraint carga_registro_hash_ck
    check (arquivo_hash ~ '^[0-9a-f]{64}$')
);

comment on table public.carga_registro is
  'T2.2/SPEC-1-002 (CA-1-06): uma linha por carga executada — hash, contagens, totais e rejeições.';
comment on column public.carga_registro.status is
  'em_andamento só existe durante a transação: se a carga falhar, a transação reverte e o registro não fica.';

create index if not exists ix_venda_mensal_mes on public.venda_mensal (mes);
create index if not exists ix_venda_mensal_cliente on public.venda_mensal (cod_cliente, mes);
create index if not exists ix_venda_mensal_sku on public.venda_mensal (cod_sku, mes);
create index if not exists ix_carga_registro_data on public.carga_registro (iniciado_em desc);

-- ------------------------------------------------------------------------- RLS
alter table public.venda_mensal     enable row level security;
alter table public.carga_registro   enable row level security;

-- Leitura: dado de venda não é público, mas é insumo de quem opera a meta.
drop policy if exists venda_mensal_read on public.venda_mensal;
create policy venda_mensal_read on public.venda_mensal
  for select to authenticated using (true);

drop policy if exists carga_registro_read on public.carga_registro;
create policy carga_registro_read on public.carga_registro
  for select to authenticated using (true);

-- Escrita: a carga roda por script com service key (fora do app), então não há política de
-- escrita para `authenticated`. Isso é proposital: ninguém altera venda pelo navegador.
-- TODO(T2.2 -> T1.2): se a T1.2 criar a operação `importar_bases`, reavaliar se a carga
-- passa a ser feita por usuário autenticado em vez de script.
