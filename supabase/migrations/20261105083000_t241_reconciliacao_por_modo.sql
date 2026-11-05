-- F2-T4.1 / SPEC-2-004 (CA-2-16, CA-2-19) — reconciliação POR MODO.
--
-- A Fase 1 deixou a reconciliação num único controle: VALIDAÇÃO DA REGRA 19/19
-- (a REGRA reproduz o modelo do cliente) e EXECUÇÃO 15/19 (o universo provisório
-- diverge). O CA-2-16 exige os dois estados GRAVADOS SEPARADAMENTE, e o CA-2-19
-- exige que cada item fora do modo EXECUÇÃO tenha causa declarada, dono e
-- referência da pendência que a resolve — sem os três campos, a execução fica
-- NÃO reconciliada e não pode ser aprovada (T2.4.2 bloqueia na aprovação).
--
-- Desenho:
--   · reconciliacao_modo: um registro por execução × modo, com estado
--     (RECONCILIADA / NAO_RECONCILIADA) e contagem de itens fora;
--   · reconciliacao_item: um registro por item fora, com causa, dono e
--     pendencia (os três campos do CA-2-19) — entram como 'A DECLARAR' e são
--     preenchidos pela operação com a causa documentada (G-03/G-07 = D2/D3;
--     G-09/G-10 = Q-42/carteiras);
--   · derivar_reconciliacao(execucao): apura os dois modos a partir de
--     controle_gabarito e grava os registros — idempotente;
--   · execucao_aprovavel(execucao): TRUE só com todos os itens fora declarados
--     (usada pela T2.4.2 para bloquear a aprovação).

begin;

create table if not exists public.reconciliacao_modo (
  execucao_id    uuid not null references public.execucao_calculo(execucao_id),
  modo           text not null check (modo in ('VALIDACAO_REGRA', 'EXECUCAO')),
  estado         text not null check (estado in ('RECONCILIADA', 'NAO_RECONCILIADA')),
  itens_fora     int  not null default 0,
  apurado_em     timestamptz not null default now(),
  primary key (execucao_id, modo)
);
comment on table public.reconciliacao_modo is
  'CA-2-16: estado de reconciliação POR MODO (VALIDAÇÃO DA REGRA e EXECUÇÃO), separados.';

create table if not exists public.reconciliacao_item (
  execucao_id  uuid not null references public.execucao_calculo(execucao_id),
  modo         text not null check (modo in ('VALIDACAO_REGRA', 'EXECUCAO')),
  controle     text not null,
  causa        text not null,
  dono         text not null,
  pendencia    text not null,
  declarado_em timestamptz not null default now(),
  primary key (execucao_id, modo, controle)
);
comment on table public.reconciliacao_item is
  'CA-2-19: item fora do modo EXECUÇÃO com causa, dono e pendência que a resolve. Sem os três campos, a reconciliação não fecha.';

alter table public.reconciliacao_modo enable row level security;
alter table public.reconciliacao_item enable row level security;
drop policy if exists reconciliacao_read on public.reconciliacao_modo;
create policy reconciliacao_read on public.reconciliacao_modo for select to authenticated using (true);
drop policy if exists reconciliacao_item_read on public.reconciliacao_item;
create policy reconciliacao_item_read on public.reconciliacao_item for select to authenticated using (true);
drop policy if exists reconciliacao_write on public.reconciliacao_modo;
create policy reconciliacao_write on public.reconciliacao_modo for all to authenticated
  using (private.has_operation('executar_calculo'))
  with check (private.has_operation('executar_calculo'));
drop policy if exists reconciliacao_item_write on public.reconciliacao_item;
create policy reconciliacao_item_write on public.reconciliacao_item for all to authenticated
  using (private.has_operation('executar_calculo'))
  with check (private.has_operation('executar_calculo'));

-- Apuração por modo: lê controle_gabarito do ciclo da execução e grava o estado
-- de cada modo + os itens fora (a declarar).
create or replace function public.derivar_reconciliacao(p_execucao uuid)
returns void
language plpgsql
security invoker
set search_path to 'pg_catalog', 'public'
as $$
declare
  v_ciclo text;
begin
  select cm.mes_referencia into v_ciclo
    from public.execucao_calculo e join public.ciclo_meta cm using (ciclo_id)
   where e.execucao_id = p_execucao;
  if not found then
    raise exception 'execucao inexistente: %', p_execucao using errcode = 'no_data_found';
  end if;

  delete from public.reconciliacao_item  where execucao_id = p_execucao;
  delete from public.reconciliacao_modo  where execucao_id = p_execucao;

  insert into public.reconciliacao_modo (execucao_id, modo, estado, itens_fora)
  select p_execucao, modo,
         case when count(*) filter (where estado <> 'BATE') = 0 then 'RECONCILIADA'
              else 'NAO_RECONCILIADA' end,
         count(*) filter (where estado <> 'BATE')
    from public.controle_gabarito
   where referencia_ciclo = v_ciclo
   group by modo;

  insert into public.reconciliacao_item (execucao_id, modo, controle, causa, dono, pendencia)
  select p_execucao, modo, controle, 'A DECLARAR', 'A DECLARAR', 'A DECLARAR'
    from public.controle_gabarito
   where referencia_ciclo = v_ciclo and estado <> 'BATE'
   on conflict (execucao_id, modo, controle) do nothing;
end;
$$;

-- CA-2-19: a execução só é aprovável se TODOS os itens fora tiverem causa,
-- dono e pendência declarados (nada de 'A DECLARAR'); com os três campos a
-- execução PODE ser aprovada e o item aparece na publicação.
create or replace function public.execucao_aprovavel(p_execucao uuid)
returns boolean
language plpgsql
stable
security invoker
set search_path to 'pg_catalog', 'public'
as $$
declare
  v_modos    int;
  v_item_sem int;
begin
  select count(*) into v_modos from public.reconciliacao_modo where execucao_id = p_execucao;
  if v_modos = 0 then return false; end if;   -- nunca apurado
  select count(*) into v_item_sem from public.reconciliacao_item
   where execucao_id = p_execucao
     and (causa = 'A DECLARAR' or dono = 'A DECLARAR' or pendencia = 'A DECLARAR'
          or causa is null or dono is null or pendencia is null);
  return v_item_sem = 0;
end;
$$;

end;