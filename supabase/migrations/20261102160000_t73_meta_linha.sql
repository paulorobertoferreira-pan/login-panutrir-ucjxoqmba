-- T7.3 (SPEC-1-007) — Consulta drill-down com memória de cálculo.
-- CA-1-23: a consulta navega de Empresa a Cliente × SKU e a memória de cálculo
-- explica o número sem precisar da planilha.
-- Fonte: motor oficial T5.x (meta original com memória) + GAP descido T6.1/T6.2/T6.3
-- (supervisor → promotor → cliente × linha ∝ Meta Original; Indireto pelos 2 canais).
-- RLS: leitura para authenticated; escrita negada (carga via service role no pipeline).

create table if not exists public.meta_linha (
  meta_linha_id     uuid primary key default gen_random_uuid(),
  referencia_ciclo  text not null default '2026-10',
  cliente           text not null,
  sku               text not null,
  cliente_nome      text,
  produto_nome      text,
  linha_produto     text,
  supervisor        text,
  promotor          text,
  regime            text not null,
  meta_original     numeric not null default 0,
  gap_linha         numeric not null default 0,
  meta_final        numeric not null default 0,
  memoria           jsonb,
  criado_em         timestamptz not null default now(),
  unique (referencia_ciclo, cliente, sku)
);

create index if not exists idx_meta_linha_supervisor
  on public.meta_linha (referencia_ciclo, supervisor);
create index if not exists idx_meta_linha_promotor
  on public.meta_linha (referencia_ciclo, promotor);
create index if not exists idx_meta_linha_cliente
  on public.meta_linha (referencia_ciclo, cliente);

comment on table public.meta_linha is
  'T7.3: resultado do ciclo Out/26 por Cliente × SKU com memória de cálculo (regime, blocos B1/B2/B3, Pbase, baseline, IS/DU, piso, transferência e via do GAP). Meta Original do motor T5.x + GAP descido T6.1/T6.3.';

alter table public.meta_linha enable row level security;

drop policy if exists meta_linha_select_authenticated on public.meta_linha;
create policy meta_linha_select_authenticated
  on public.meta_linha for select
  to authenticated
  using (true);

grant select on public.meta_linha to authenticated;
revoke all on public.meta_linha from anon;
