-- F2 LEVA C — T2.4.3 (CA-2-18), T2.5.3 (CA-2-25), T2.5.4 (CA-2-26) e T2.6.3 (CA-2-30).
--
-- T2.4.3  publicação congela: UPDATE direto na meta publicada é recusado;
--         correção = nova execução publicada como versão 2 com motivo, v1
--         preservada consultável;
-- T2.5.3  RLS por carteira na meta_linha (deny-by-default) — a negativa nas 3
--         frentes (interface/RPC/tabela) usa a MESMA política;
-- T2.5.4  consulta com ciclo declarado e memória de cálculo disponível;
-- T2.6.3  extrato restrito ao publicado com campo de perfil (já feito na
--         T2.6.1/t252) + nota de responsabilidade do Metabase registrada.

begin;

create extension if not exists dblink;

-- ============ T2.4.3: negativa auditada em transação autônoma ============
create or replace function public.registrar_negativa(
  p_operacao text, p_alvo text, p_razao text
) returns uuid
language plpgsql
security definer
set search_path to 'pg_catalog', 'public'
as $$
declare
  v_conn text := format('dbname=%s user=%s', current_database(), current_user);
  v_id uuid;
begin
  select gen_random_uuid() into v_id;
  perform dblink_exec(v_conn,
    format('insert into public.authorization_audit_log (event_id, actor_id, operation_key, target_type, target_id, decision, reason, correlation_id) values (%L, auth.uid(), %L, %L, %L, %L, %L, %L)',
           v_id, 'aprovar_publicar', 'meta_linha', p_alvo, 'denied', p_operacao || ': ' || p_razao::text, gen_random_uuid()));
  return v_id;
end;
$$;

comment on function public.registrar_negativa(text, text, text) is
  'CA-2-08/CA-2-10/CA-2-18: negativa auditada em transação autônoma (sobrevive ao rollback).';

-- ============ T2.4.3: publicação congela a meta ============
-- A meta publicada não é editável: UPDATE direto em meta_linha de ciclo
-- publicado é recusado. A correção é nova execução publicada (versão 2).
create or replace function public.trg_meta_linha_publicada_congelada()
returns trigger
language plpgsql
security invoker
set search_path to 'pg_catalog', 'public'
as $$
declare
  v_status text;
begin
  select status into v_status from public.ciclo_meta
   where mes_referencia = (select referencia_ciclo from meta_linha
                            where meta_linha_id = coalesce(new.meta_linha_id, old.meta_linha_id));
  if v_status = 'publicado' and tg_op = 'UPDATE' then
    perform public.registrar_negativa('editar_meta_publicada',
      coalesce(new.meta_linha_id::text, old.meta_linha_id::text),
      'meta publicada é imutável (CA-2-18): corrigir por nova execução publicada como versão 2');
    raise exception 'meta publicada e imutavel (CA-2-18): corrigir por nova execucao publicada como versao 2 com motivo'
      using errcode = 'restrict_violation';
  end if;
  if v_status = 'publicado' and tg_op = 'DELETE' then
    perform public.registrar_negativa('apagar_meta_publicada',
      old.meta_linha_id::text,
      'meta publicada é imutável (CA-2-18)');
    raise exception 'meta publicada nao pode ser apagada (CA-2-18)'
      using errcode = 'restrict_violation';
  end if;
  return coalesce(new, old);
end;
$$;

drop trigger if exists trg_meta_publicada_congelada on public.meta_linha;
create trigger trg_meta_publicada_congelada
  before update or delete on public.meta_linha
  for each row execute function public.trg_meta_linha_publicada_congelada();

comment on function public.trg_meta_linha_publicada_congelada() is
  'CA-2-18: UPDATE/DELETE em meta publicada recusados e auditados; correção por versão 2.';

-- ============ T2.5.3: RLS por carteira na meta_linha ============
-- Deny-by-default: só vê a meta_linha do ciclo o usuário com vínculo que
-- alcança a linha (diretoria vê tudo; supervisor pela equipe; promotor pela
-- carteira). Sem vínculo, nada. A política da T7.3 ("authenticated lê tudo")
-- é SUBSTITUÍDA — manter as duas as OR-aria e anularia o recorte.
drop policy if exists meta_linha_select_authenticated on public.meta_linha;
drop policy if exists meta_linha_read on public.meta_linha;
create policy meta_linha_read on public.meta_linha
  for select to authenticated using (
    exists (select 1 from public.ciclo_meta cm
             where cm.mes_referencia = meta_linha.referencia_ciclo
               and cm.status = 'publicado')
    and (
      'EMPRESA' in (select carteiras_de('consulta_diretoria', meta_linha.referencia_ciclo))
      or meta_linha.supervisor::text in (select carteiras_de('consulta_supervisor', meta_linha.referencia_ciclo))
      or meta_linha.promotor::text in (select carteiras_de('consulta_promotor', meta_linha.referencia_ciclo))
    ));

comment on policy meta_linha_read on public.meta_linha is
  'CA-2-25: RLS por carteira, deny-by-default. A mesma política vale para as 3 frentes (interface, RPC e SELECT direto).';

-- ============ T2.5.4: consulta com ciclo declarado e memória ============
create or replace function public.consulta_publicada(
  p_ciclo text, p_papel text
)
returns table (
  ciclo          text,
  cliente        text,
  sku            text,
  regime         text,
  meta_final     numeric,
  memoria        jsonb
)
language sql
stable
security invoker
set search_path to 'pg_catalog', 'public'
as $$
  select p_ciclo, m.cliente, m.sku, m.regime, m.meta_final, m.memoria
    from public.meta_linha m
   where m.referencia_ciclo = p_ciclo
     and exists (select 1 from public.ciclo_meta cm
                 where cm.mes_referencia = p_ciclo and cm.status = 'publicado')
     and (
       'EMPRESA' in (select carteiras_de(p_papel, p_ciclo))
       or (p_papel = 'consulta_supervisor'
           and m.supervisor::text in (select carteiras_de(p_papel, p_ciclo)))
       or (p_papel = 'consulta_promotor'
           and m.promotor::text in (select carteiras_de(p_papel, p_ciclo)))
     );
$$;

comment on function public.consulta_publicada(text, text) is
  'CA-2-26: consulta da meta publicada com o ciclo declarado e a memória de cálculo disponível.';

end;