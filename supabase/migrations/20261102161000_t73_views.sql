-- T7.3 — Views de agregação para o drill-down (PostgREST sem aggregates: PGRST123).
-- security_invoker = true: a view herda o RLS de meta_linha (só authenticated vê).

create or replace view public.vw_meta_supervisor
with (security_invoker = true) as
select referencia_ciclo, supervisor,
       count(*) as combinacoes,
       count(distinct cliente) as clientes,
       sum(meta_original) as meta_original,
       sum(gap_linha) as gap_linha,
       sum(meta_final) as meta_final
from public.meta_linha
group by 1, 2;

create or replace view public.vw_meta_promotor
with (security_invoker = true) as
select referencia_ciclo, supervisor, promotor,
       count(*) as combinacoes,
       count(distinct cliente) as clientes,
       sum(meta_original) as meta_original,
       sum(gap_linha) as gap_linha,
       sum(meta_final) as meta_final
from public.meta_linha
group by 1, 2, 3;

create or replace view public.vw_meta_regime
with (security_invoker = true) as
select referencia_ciclo, regime,
       count(*) as combinacoes,
       sum(meta_original) as meta_original,
       sum(gap_linha) as gap_linha,
       sum(meta_final) as meta_final
from public.meta_linha
group by 1, 2;

grant select on public.vw_meta_supervisor, public.vw_meta_promotor, public.vw_meta_regime to authenticated;
revoke all on public.vw_meta_supervisor, public.vw_meta_promotor, public.vw_meta_regime from anon;
