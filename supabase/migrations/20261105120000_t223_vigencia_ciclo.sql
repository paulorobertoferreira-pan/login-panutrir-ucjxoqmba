-- F2-T2.3 / SPEC-2-002 (CA-2-07) — vigência por ciclo nas regras por rede.
--
-- Sortimento restrito, substituição e exclusões passam a ter ciclo_inicio:
-- a regra vale A PARTIR do ciclo informado e NUNCA retroage. Cadastrar regra
-- com vigência em ciclo já aprovado/publicado é recusado (CA-2-07/CA-2-08).
-- Regra sem ciclo_inicio vale desde sempre (compatível com o carregado da Fase 1).

begin;

alter table public.sortimento_restrito add column if not exists ciclo_inicio text;
alter table public.substituicao     add column if not exists ciclo_inicio text;

comment on column public.sortimento_restrito.ciclo_inicio is
  'CA-2-07: a regra vale a partir deste ciclo (YYYY-MM). Nulo = vale desde sempre.';
comment on column public.substituicao.ciclo_inicio is
  'CA-2-07: a regra vale a partir deste ciclo (YYYY-MM). Nulo = vale desde sempre.';

-- Vigência retroativa: recusada se já existir ciclo aprovado/publicado no ciclo
-- informado ou depois dele (a regra mudaria resultado de ciclo fechado).
create or replace function public.vigencia_valida(p_ciclo_inicio text)
returns boolean
language sql
stable
security invoker
set search_path to 'pg_catalog', 'public'
as $$
  select not exists (
    select 1 from public.ciclo_meta
     where status in ('aprovado', 'publicado')
       and mes_referencia >= p_ciclo_inicio);
$$;

create or replace function public.trg_vigencia_nao_retroativa()
returns trigger
language plpgsql
security invoker
set search_path to 'pg_catalog', 'public'
as $$
begin
  if new.ciclo_inicio is not null
     and not public.vigencia_valida(new.ciclo_inicio) then
    raise exception 'vigencia retroativa recusada: ciclo % ja aprovado/publicado', new.ciclo_inicio
      using errcode = 'check_violation';
  end if;
  return new;
end;
$$;

drop trigger if exists trg_sortimento_vigencia on public.sortimento_restrito;
create trigger trg_sortimento_vigencia
  before insert or update on public.sortimento_restrito
  for each row execute function public.trg_vigencia_nao_retroativa();

drop trigger if exists trg_substituicao_vigencia on public.substituicao;
create trigger trg_substituicao_vigencia
  before insert or update on public.substituicao
  for each row execute function public.trg_vigencia_nao_retroativa();

-- Regra vigente no ciclo: usada pelo motor (T2.2.3 GREEN — a regra nova muda o
-- resultado do ciclo de vigência e NÃO muda o do ciclo anterior).
create or replace function public.regras_vigentes(p_ciclo text)
returns setof public.substituicao
language sql
stable
security invoker
set search_path to 'pg_catalog', 'public'
as $$
  select s.* from public.substituicao s
   where s.ciclo_inicio is null
      or s.ciclo_inicio <= p_ciclo;
$$;

end;