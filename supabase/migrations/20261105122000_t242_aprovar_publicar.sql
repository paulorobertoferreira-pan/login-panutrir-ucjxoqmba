-- F2-T4.2 / SPEC-2-004 (CA-2-17) — aprovar e publicar com trilha append-only.
--
-- Aprovar exige reconciliação por modo fechada (execucao_aprovavel, T2.4.1) e
-- nenhum parâmetro requerido não confirmado (T2.1.2). Publicar exige aprovado.
-- Cada evento (aprovação, publicação, RECUSA) vai para a trilha append-only
-- com ator, operação, alvo, motivo e timestamp UTC. UPDATE/DELETE na trilha
-- são recusados (append-only).

begin;

create extension if not exists dblink;

-- Recusa gravada em transação AUTÔNOMA (dblink): sobrevive ao rollback da
-- transação que a originou — a recusa é auditada mesmo quando a operação falha.
create or replace function public.registrar_recusa(
  p_ciclo uuid, p_execucao uuid, p_operacao text, p_razao text
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
    format('insert into public.ciclo_evento (evento_id, ciclo_id, execucao_id, operacao, ator, motivo, detalhe) values (%L, %L, %L, %L, %L, %L, to_jsonb(%L::text))',
           v_id, p_ciclo, p_execucao, p_operacao, coalesce(auth.uid()::text, 'sistema'),
           'recusa automática', p_razao::text));
  return v_id;
end;
$$;

create table if not exists public.ciclo_evento (
  evento_id  uuid primary key default gen_random_uuid(),
  ciclo_id   uuid not null references public.ciclo_meta(ciclo_id),
  execucao_id uuid references public.execucao_calculo(execucao_id),
  operacao   text not null check (operacao in ('aprovar','publicar','recusa_aprovar','recusa_publicar')),
  ator       text not null,
  motivo     text not null,
  detalhe    jsonb,
  criado_em  timestamptz not null default now()
);
comment on table public.ciclo_evento is
  'CA-2-17: trilha append-only de aprovação/publicação e recusas. Ator, operação, alvo, motivo, timestamp.';

alter table public.ciclo_evento enable row level security;
drop policy if exists ciclo_evento_read on public.ciclo_evento;
create policy ciclo_evento_read on public.ciclo_evento for select to authenticated using (true);
drop policy if exists ciclo_evento_write on public.ciclo_evento;
create policy ciclo_evento_write on public.ciclo_evento for insert to authenticated
  with check (private.has_operation('aprovar_publicar'));

create or replace function public.trg_ciclo_evento_append_only()
returns trigger
language plpgsql
security invoker
set search_path to 'pg_catalog', 'public'
as $$
begin
  raise exception 'ciclo_evento e append-only: % nao permitido', tg_op
    using errcode = 'restrict_violation';
end;
$$;

drop trigger if exists trg_ciclo_evento_no_update on public.ciclo_evento;
create trigger trg_ciclo_evento_no_update
  before update or delete on public.ciclo_evento
  for each row execute function public.trg_ciclo_evento_append_only();

-- Aprovar: só com reconciliação fechada e parâmetros confirmados.
create or replace function public.aprovar_execucao(
  p_ciclo uuid, p_execucao uuid, p_motivo text
) returns uuid
language plpgsql
security invoker
set search_path to 'pg_catalog', 'public'
as $$
declare
  v_evento uuid;
  v_status text;
  v_pend int;
begin
  if coalesce(btrim(p_motivo), '') = '' then
    raise exception 'motivo da aprovacao e obrigatorio' using errcode = 'check_violation';
  end if;
  select status into v_status from public.ciclo_meta where ciclo_id = p_ciclo;
  if not found then
    raise exception 'ciclo inexistente' using errcode = 'no_data_found';
  end if;
  if v_status in ('aprovado', 'publicado') then
    perform public.registrar_recusa(p_ciclo, p_execucao, 'recusa_aprovar',
                                    'ciclo ja ' || v_status);
    raise exception 'ciclo ja % — aprovacao recusada e auditada', v_status
      using errcode = 'check_violation';
  end if;
  if not public.execucao_aprovavel(p_execucao) then
    perform public.registrar_recusa(p_ciclo, p_execucao, 'recusa_aprovar',
                                    'reconciliacao nao fechada (itens fora sem causa/dono/pendencia)');
    raise exception 'execucao nao reconciliada — aprovacao recusada e auditada'
      using errcode = 'check_violation';
  end if;
  select count(*) into v_pend from public.pendencias_confirmacao(p_execucao);
  if v_pend > 0 then
    perform public.registrar_recusa(p_ciclo, p_execucao, 'recusa_aprovar',
                                    'parametros requeridos nao confirmados (' || v_pend || ')');
    raise exception '% parametro(s) requerido(s) nao confirmado(s) — aprovacao recusada e auditada', v_pend
      using errcode = 'check_violation';
  end if;
  update public.execucao_calculo set status = 'concluida'
   where execucao_id = p_execucao and status = 'em_andamento';
  update public.ciclo_meta set status = 'aprovado' where ciclo_id = p_ciclo;
  insert into public.ciclo_evento (ciclo_id, execucao_id, operacao, ator, motivo)
  values (p_ciclo, p_execucao, 'aprovar', coalesce(auth.uid()::text, 'sistema'), p_motivo)
  returning evento_id into v_evento;
  return v_evento;
end;
$$;

-- Publicar: só ciclo aprovado.
create or replace function public.publicar_ciclo(p_ciclo uuid, p_motivo text)
returns uuid
language plpgsql
security invoker
set search_path to 'pg_catalog', 'public'
as $$
declare
  v_evento uuid;
  v_status text;
begin
  if coalesce(btrim(p_motivo), '') = '' then
    raise exception 'motivo da publicacao e obrigatorio' using errcode = 'check_violation';
  end if;
  select status into v_status from public.ciclo_meta where ciclo_id = p_ciclo;
  if not found then
    raise exception 'ciclo inexistente' using errcode = 'no_data_found';
  end if;
  if v_status <> 'aprovado' then
    perform public.registrar_recusa(p_ciclo, null, 'recusa_publicar',
                                    'ciclo esta ' || coalesce(v_status, 'indefinido') || ' (publicar exige aprovado)');
    raise exception 'ciclo % nao pode ser publicado (exige aprovado) — recusa auditada', v_status
      using errcode = 'check_violation';
  end if;
  update public.ciclo_meta set status = 'publicado' where ciclo_id = p_ciclo;
  insert into public.ciclo_evento (ciclo_id, operacao, ator, motivo)
  values (p_ciclo, 'publicar', coalesce(auth.uid()::text, 'sistema'), p_motivo)
  returning evento_id into v_evento;
  return v_evento;
end;
$$;

comment on function public.aprovar_execucao(uuid, uuid, text) is
  'CA-2-17: aprova execução reconciliada; recusa (auditada) execução não reconciliada, parâmetro pendente ou ciclo já aprovado/publicado.';
comment on function public.publicar_ciclo(uuid, text) is
  'CA-2-17: publica ciclo aprovado; recusa (auditada) ciclo em outro estado.';

end;