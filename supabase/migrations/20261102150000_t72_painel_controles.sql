-- T7.2 (SPEC-1-007) — Painel de controles do ciclo: tabela que alimenta o painel.
-- CA-1-22: o painel mostra todos os controles listados, com o gabarito ao lado e o
-- estado bate/diverge. Fonte: teste automatizado de reconciliação (T7.1,
-- contracts/teste_gabarito.py), gravado por execução do teste.
-- RLS: leitura para authenticated; escrita negada a todos (o teste grava via service
-- role no pipeline de execução; o app só consulta).

create table if not exists public.controle_gabarito (
  controle_id        uuid primary key default gen_random_uuid(),
  modo               text not null check (modo in ('VALIDACAO_REGRA', 'EXECUCAO')),
  controle           text not null check (controle ~ '^G-\d{2}(_lojas|_valor)?$'),
  gabarito           numeric not null,
  medido             numeric,
  diferenca          numeric,
  diferenca_pct      numeric,
  tolerancia         numeric not null default 0,
  estado             text not null check (estado in ('BATE', 'DIVERGE', 'SEM MEDIDA')),
  referencia_ciclo   text not null default '2026-10',
  criado_em          timestamptz not null default now(),
  unique (modo, controle, referencia_ciclo)
);

comment on table public.controle_gabarito is
  'T7.2: resultado do teste de gabarito (T7.1) por controle G-01..G-18. Dois modos: VALIDACAO_REGRA (medidas provadas nas T6.x com o universo do gabarito) e EXECUCAO (motor no universo provisório).';

alter table public.controle_gabarito enable row level security;

-- Leitura: qualquer usuário autenticado do app vê os controles (o painel é do ciclo).
drop policy if exists controle_gabarito_select_authenticated on public.controle_gabarito;
create policy controle_gabarito_select_authenticated
  on public.controle_gabarito for select
  to authenticated
  using (true);

-- Escrita: negada por omissão (nenhuma policy insert/update/delete para authenticated
-- nem anon). A gravação é feita pelo pipeline de teste com service role.

-- Seed: resultado da T7.1 executada em 02/11/2026 (VALIDACAO_REGRA 19/19 BATE;
-- EXECUCAO 15/19 BATE, 2 DIVERGE esperados — G-03/G-07, GAP inverso à Meta Original,
-- converge com D2/D3 — e 2 SEM MEDIDA — G-09/G-10, mix por linha exige a carteira do
-- gabarito; aproximação pela carteira atual diverge e não é o número do controle).
insert into public.controle_gabarito (modo, controle, gabarito, medido, diferenca, diferenca_pct, tolerancia, estado)
values
  ('VALIDACAO_REGRA', 'G-01', 13000000.000000, 13000000.000000, 0.000000, 0.00000000, 0.0100, 'BATE'),
  ('VALIDACAO_REGRA', 'G-02', 11701803.730000, 11701803.730000, 0.000000, 0.00000000, 0.0100, 'BATE'),
  ('VALIDACAO_REGRA', 'G-03', 1298196.270000, 1298196.260000, -0.010000, 0.00000001, 0.0100, 'BATE'),
  ('VALIDACAO_REGRA', 'G-04', 715000.000000, 715000.000000, 0.000000, 0.00000000, 0.0000, 'BATE'),
  ('VALIDACAO_REGRA', 'G-05', 435375.280000, 435375.280000, 0.000000, 0.00000000, 0.0000, 'BATE'),
  ('VALIDACAO_REGRA', 'G-06', 279624.720000, 279624.720000, 0.000000, 0.00000000, 0.0000, 'BATE'),
  ('VALIDACAO_REGRA', 'G-07', 1018571.540000, 1018571.540000, 0.000000, 0.00000000, 0.0000, 'BATE'),
  ('VALIDACAO_REGRA', 'G-08', 0.294832, 0.294832, 0.000000, 0.00000000, 0.0100, 'BATE'),
  ('VALIDACAO_REGRA', 'G-09', 888938.140000, 888938.140000, 0.000000, 0.00000000, 0.0100, 'BATE'),
  ('VALIDACAO_REGRA', 'G-10', 409258.130000, 409258.130000, 0.000000, 0.00000000, 0.0100, 'BATE'),
  ('VALIDACAO_REGRA', 'G-11', 29003.000000, 29003.000000, 0.000000, 0.00000000, 0.0100, 'BATE'),
  ('VALIDACAO_REGRA', 'G-12', 2739.000000, 2739.000000, 0.000000, 0.00000000, 0.1500, 'BATE'),
  ('VALIDACAO_REGRA', 'G-13', 442.000000, 442.000000, 0.000000, 0.00000000, 0.0500, 'BATE'),
  ('VALIDACAO_REGRA', 'G-14', 246.000000, 246.000000, 0.000000, 0.00000000, 0.0500, 'BATE'),
  ('VALIDACAO_REGRA', 'G-15_lojas', 118.000000, 118.000000, 0.000000, 0.00000000, 0.0000, 'BATE'),
  ('VALIDACAO_REGRA', 'G-15_valor', 305758.740000, 305758.740000, 0.000000, 0.00000000, 0.0100, 'BATE'),
  ('VALIDACAO_REGRA', 'G-16', 749.000000, 749.000000, 0.000000, 0.00000000, 0.0500, 'BATE'),
  ('VALIDACAO_REGRA', 'G-17', 20955.000000, 20955.000000, 0.000000, 0.00000000, 0.0500, 'BATE'),
  ('VALIDACAO_REGRA', 'G-18', 27.000000, 27.000000, 0.000000, 0.00000000, 0.0500, 'BATE'),
  ('EXECUCAO', 'G-01', 13000000.000000, 13000000.000000, 0.000000, 0.00000000, 0.0100, 'BATE'),
  ('EXECUCAO', 'G-02', 11701803.730000, 11679641.680000, -22162.050000, 0.00189398, 0.0100, 'BATE'),
  ('EXECUCAO', 'G-03', 1298196.270000, 1320358.320000, 22162.050000, 0.01707308, 0.0100, 'DIVERGE'),
  ('EXECUCAO', 'G-04', 715000.000000, 715000.000000, 0.000000, 0.00000000, 0.0000, 'BATE'),
  ('EXECUCAO', 'G-05', 435375.280000, 435375.280000, 0.000000, 0.00000000, 0.0000, 'BATE'),
  ('EXECUCAO', 'G-06', 279624.720000, 279624.720000, 0.000000, 0.00000000, 0.0000, 'BATE'),
  ('EXECUCAO', 'G-07', 1018571.540000, 1040733.600000, 22162.060000, 0.02176219, 0.0000, 'DIVERGE'),
  ('EXECUCAO', 'G-08', 0.294832, 0.294832, 0.000000, 0.00000000, 0.0100, 'BATE'),
  ('EXECUCAO', 'G-09', 888938.140000, NULL, NULL, NULL, 0.0100, 'SEM MEDIDA'),
  ('EXECUCAO', 'G-10', 409258.130000, NULL, NULL, NULL, 0.0100, 'SEM MEDIDA'),
  ('EXECUCAO', 'G-11', 29003.000000, 28936.000000, -67.000000, 0.00231002, 0.0100, 'BATE'),
  ('EXECUCAO', 'G-12', 2739.000000, 2373.000000, -366.000000, 0.13362533, 0.1500, 'BATE'),
  ('EXECUCAO', 'G-13', 442.000000, 447.000000, 5.000000, 0.01131222, 0.0500, 'BATE'),
  ('EXECUCAO', 'G-14', 246.000000, 245.000000, -1.000000, 0.00406504, 0.0500, 'BATE'),
  ('EXECUCAO', 'G-15_lojas', 118.000000, 118.000000, 0.000000, 0.00000000, 0.0000, 'BATE'),
  ('EXECUCAO', 'G-15_valor', 305758.740000, 306327.350000, 568.610000, 0.00185966, 0.0100, 'BATE'),
  ('EXECUCAO', 'G-16', 749.000000, 746.000000, -3.000000, 0.00400534, 0.0500, 'BATE'),
  ('EXECUCAO', 'G-17', 20955.000000, 21393.000000, 438.000000, 0.02090432, 0.0500, 'BATE'),
  ('EXECUCAO', 'G-18', 27.000000, 26.000000, -1.000000, 0.03703704, 0.0500, 'BATE')
on conflict (modo, controle, referencia_ciclo) do update
  set gabarito = excluded.gabarito,
      medido = excluded.medido,
      diferenca = excluded.diferenca,
      diferenca_pct = excluded.diferenca_pct,
      tolerancia = excluded.tolerancia,
      estado = excluded.estado,
      criado_em = now();

-- Grants explícitos (padrão Supabase: authenticated lê; anon sem acesso à tabela).
grant select on public.controle_gabarito to authenticated;
revoke all on public.controle_gabarito from anon;
