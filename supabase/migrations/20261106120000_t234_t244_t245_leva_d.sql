-- F2 LEVA D — T2.3.4 (CA-2-13), T2.4.4 (CA-2-20), T2.4.5 (CA-2-22).
--
-- T2.3.4  promover cenário a CANDIDATO OFICIAL: exige autor e motivo, fica
--         auditado e NÃO publica a meta. O candidato é marcado na versão
--         (candidato_oficial=true) e o evento vai para a trilha;
-- T2.4.4  os 4 marcos do ciclo (mês fechado carregado, execução, aprovação,
--         publicação) com timestamp UTC e o prazo do K2 calculado a partir
--         deles; marco ausente produz "não medido" com motivo, nunca zero;
-- T2.4.5  nenhum número final é alterado por edição direta em qualquer nível
--         (o congelamento da T2.4.3 já recusa UPDATE/DELETE na meta publicada —
--         aqui a recusa ganha a operação própria 'ajuste_manual' na auditoria
--         e a via por parâmetro é provada).

begin;

create extension if not exists dblink;

-- ============ T2.3.4: promoção de cenário a candidato oficial ============
alter table public.parametros_versao add column if not exists candidato_oficial boolean not null default false;
alter table public.parametros_versao add column if not exists promovido_em timestamptz;
alter table public.parametros_versao add column if not exists promovido_por text;

create or replace function public.promover_cenario(
  p_versao_cenario uuid, p_autor text, p_motivo text
) returns uuid
language plpgsql
security invoker
set search_path to 'pg_catalog', 'public'
as $$
declare
  v_simulacao boolean;
  v_status text;
  v_evento uuid;
begin
  if coalesce(btrim(p_autor), '') = '' then
    raise exception 'autor da promocao e obrigatorio' using errcode = 'check_violation';
  end if;
  if coalesce(btrim(p_motivo), '') = '' then
    raise exception 'motivo da promocao e obrigatorio (CA-2-13)' using errcode = 'check_violation';
  end if;
  select simulacao, status into v_simulacao, v_status
    from public.parametros_versao where versao_id = p_versao_cenario;
  if not found then
    raise exception 'versao inexistente' using errcode = 'no_data_found';
  end if;
  if not v_simulacao then
    raise exception 'versao nao e um cenario (CA-2-13)' using errcode = 'check_violation';
  end if;
  if v_status <> 'rascunho' then
    raise exception 'cenario em status % nao pode ser promovido', v_status using errcode = 'check_violation';
  end if;
  -- marca o candidato (continua rascunho e simulacao: NÃO publica)
  update public.parametros_versao
     set candidato_oficial = true, promovido_em = now(), promovido_por = p_autor
   where versao_id = p_versao_cenario;
  -- trilha da promoção: o ciclo do cenário é o mes_referencia da versão
  insert into public.ciclo_evento (ciclo_id, operacao, ator, motivo, detalhe)
  select cm.ciclo_id, 'promover_cenario', p_autor, p_motivo,
         jsonb_build_object('versao', p_versao_cenario)
    from public.ciclo_meta cm where cm.mes_referencia = (select mes_referencia from public.parametros_versao where versao_id = p_versao_cenario)
  returning evento_id into v_evento;
  return v_evento;
end;
$$;

comment on function public.promover_cenario(uuid, text, text) is
  'CA-2-13: promove cenário a candidato oficial (autor e motivo obrigatórios, auditado); NÃO publica.';

-- ============ T2.4.4: marcos do ciclo e prazo do K2 ============
alter table public.ciclo_evento drop constraint if exists ciclo_evento_operacao_check;
alter table public.ciclo_evento
  add constraint ciclo_evento_operacao_check
  check (operacao in ('aprovar','publicar','recusa_aprovar','recusa_publicar','promover_cenario'));

create table if not exists public.ciclo_marcos (
  ciclo_id    uuid primary key references public.ciclo_meta(ciclo_id),
  mes_carregado_em   timestamptz,
  executado_em       timestamptz,
  aprovado_em        timestamptz,
  publicado_em       timestamptz
);
comment on table public.ciclo_marcos is
  'CA-2-20: os 4 marcos do ciclo com timestamp UTC. Marco ausente = NULL (não medido), nunca zero.';

alter table public.ciclo_marcos enable row level security;
drop policy if exists ciclo_marcos_read on public.ciclo_marcos;
create policy ciclo_marcos_read on public.ciclo_marcos for select to authenticated using (true);
drop policy if exists ciclo_marcos_write on public.ciclo_marcos;
create policy ciclo_marcos_write on public.ciclo_marcos for all to authenticated
  using (private.has_operation('aprovar_publicar'))
  with check (private.has_operation('aprovar_publicar'));

-- registra/atualiza um marco (idempotente: o marco fica com o 1º timestamp)
create or replace function public.registrar_marco(p_ciclo uuid, p_marco text)
returns timestamptz
language plpgsql
security invoker
set search_path to 'pg_catalog', 'public'
as $$
declare
  v_col text;
  v_ts timestamptz;
begin
  if p_marco not in ('mes_carregado_em','executado_em','aprovado_em','publicado_em') then
    raise exception 'marco invalido: %', p_marco using errcode = 'check_violation';
  end if;
  insert into public.ciclo_marcos (ciclo_id) values (p_ciclo)
    on conflict (ciclo_id) do nothing;
  execute format('update public.ciclo_marcos set %I = coalesce(%I, now()) where ciclo_id = %L returning %I',
                 p_marco, p_marco, p_ciclo, p_marco) into v_ts;
  return v_ts;
end;
$$;

comment on function public.registrar_marco(uuid, text) is
  'CA-2-20: registra o marco do ciclo (1º timestamp fica; idempotente).';

-- Prazo do K2: da publicação até o fim do mês de referência do ciclo.
-- Marco ausente → "não medido" com motivo, NUNCA zero.
create or replace function public.prazo_k2(p_ciclo uuid)
returns table (
  medido       boolean,
  motivo       text,
  dias_ate_publicacao numeric,
  prazo_limite date,
  dentro_do_prazo boolean
)
language plpgsql
stable
security invoker
set search_path to 'pg_catalog', 'public'
as $$
declare
  r record;
  v_mes text;
  v_limite date;
begin
  select * into r from public.ciclo_marcos where ciclo_id = p_ciclo;
  select mes_referencia into v_mes from public.ciclo_meta where ciclo_id = p_ciclo;
  -- prazo K2: publicar antes do 1º dia do mês de referência (meta proposta)
  v_limite := (to_date(v_mes || '-01', 'YYYY-MM-DD'));
  if r is null or r.publicado_em is null then
    return query select false,
      'publicação não registrada'::text,
      null::numeric, v_limite, null::boolean;
    return;
  end if;
  if r.mes_carregado_em is null then
    return query select false,
      'mês fechado carregado não registrado'::text,
      null::numeric, v_limite, null::boolean;
    return;
  end if;
  return query select true, null::text,
    (extract(epoch from (r.publicado_em - r.mes_carregado_em)) / 86400)::numeric,
    v_limite,
    (r.publicado_em::date < v_limite);
end;
$$;

comment on function public.prazo_k2(uuid) is
  'CA-2-20: prazo do K2 a partir dos marcos; marco ausente = não medido com motivo, nunca zero.';

-- ============ T2.4.5: recusa de ajuste manual (operação própria) ============
-- O congelamento da T2.4.3 já recusa UPDATE/DELETE na meta publicada; aqui a
-- negativa ganha a operação 'ajuste_manual' (CA-2-22) na auditoria.
create or replace function public.trg_meta_ajuste_manual()
returns trigger
language plpgsql
security invoker
set search_path to 'pg_catalog', 'public'
as $$
declare
  v_status text;
  v_conn text := format('dbname=%s user=%s', current_database(), current_user);
begin
  select status into v_status from public.ciclo_meta
   where mes_referencia = (select referencia_ciclo from meta_linha
                            where meta_linha_id = coalesce(new.meta_linha_id, old.meta_linha_id));
  if v_status = 'publicado' and tg_op = 'UPDATE' then
    perform dblink_exec(v_conn,
      format('insert into public.authorization_audit_log (event_id, actor_id, operation_key, target_type, target_id, decision, reason, correlation_id) values (%L, auth.uid(), %L, %L, %L, %L, %L, %L)',
             gen_random_uuid(), 'aprovar_publicar', 'meta_linha',
             coalesce(new.meta_linha_id::text, old.meta_linha_id::text), 'denied',
             'ajuste_manual (CA-2-22): número final não é editado direto — a via é parâmetro versionado no ciclo seguinte',
             gen_random_uuid()));
    raise exception 'ajuste manual recusado (CA-2-22): a via por parametro versionado produz o efeito no ciclo seguinte'
      using errcode = 'restrict_violation';
  end if;
  return coalesce(new, old);
end;
$$;

drop trigger if exists trg_meta_ajuste_manual on public.meta_linha;
create trigger trg_meta_ajuste_manual
  before update on public.meta_linha
  for each row execute function public.trg_meta_ajuste_manual();

comment on function public.trg_meta_ajuste_manual() is
  'CA-2-22: ajuste manual do número final recusado e auditado como ajuste_manual.';

-- registrar_marco automático na aprovação/publicação (T2.4.2 → T2.4.4)
create or replace function public.trg_ciclo_evento_marcos()
returns trigger
language plpgsql
security invoker
set search_path to 'pg_catalog', 'public'
as $$
begin
  if new.operacao = 'aprovar' then
    perform public.registrar_marco(new.ciclo_id, 'aprovado_em');
  elsif new.operacao = 'publicar' then
    perform public.registrar_marco(new.ciclo_id, 'publicado_em');
  end if;
  return new;
end;
$$;

drop trigger if exists trg_evento_marcos on public.ciclo_evento;
create trigger trg_evento_marcos
  after insert on public.ciclo_evento
  for each row execute function public.trg_ciclo_evento_marcos();

comment on function public.trg_ciclo_evento_marcos() is
  'CA-2-20: os marcos aprovado_em/publicado_em são registrados pelos eventos da trilha.';

end;
