-- F2-T2.4 / SPEC-2-002 (CA-2-08, CA-2-10) — bloqueios auditados.
--
-- CA-2-08: ciclo aprovado ou publicado recusa a criação de versão nova de
--          parâmetros, e a recusa fica auditada.
-- CA-2-10: oficializar versão com parâmetro PENDENTE é recusado e auditado,
--          e a versão oficial anterior segue vigente.
--
-- As negativas vão para authorization_audit_log em transação AUTÔNOMA (dblink)
-- — sobrevivem ao rollback da operação que as originou.

begin;

create extension if not exists dblink;

-- Negativa auditada em transação autônoma (mesma técnica da T4.2)
create or replace function public.registrar_negativa_parametros(
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
           v_id, 'editar_parametros', 'parametros_versao', p_alvo, 'denied', p_operacao || ': ' || p_razao::text, gen_random_uuid()));
  return v_id;
end;
$$;

comment on function public.registrar_negativa_parametros(text, text, text) is
  'CA-2-08/CA-2-10: negativa auditada em transação autônoma (sobrevive ao rollback).';

-- CA-2-08: criar versão a partir de versão de ciclo aprovado/publicado é recusado.
-- A versão de parâmetros está amarrada ao ciclo por ciclo_meta.parametros_versao_id;
-- se a versão de ORIGEM pertence a um ciclo aprovado/publicado, não pode derivar.
create or replace function public.criar_versao_parametros_ciclo(
  p_ciclo uuid, p_versao_origem uuid, p_novo_codigo text,
  p_autor text, p_motivo text, p_alteracoes jsonb default '{}'::jsonb
) returns uuid
language plpgsql
security invoker
set search_path to 'pg_catalog', 'public'
as $$
declare
  v_status text;
begin
  select status into v_status from public.ciclo_meta where ciclo_id = p_ciclo;
  if not found then
    raise exception 'ciclo inexistente' using errcode = 'no_data_found';
  end if;
  if v_status in ('aprovado', 'publicado') then
    perform public.registrar_negativa_parametros('criar_versao',
      p_novo_codigo, 'ciclo ' || v_status || ' recusa versão nova (CA-2-08)');
    raise exception 'ciclo % recusa versao nova de parametros (CA-2-08) — recusa auditada', v_status
      using errcode = 'check_violation';
  end if;
  return public.criar_versao_parametros(p_versao_origem, p_novo_codigo, p_autor, p_motivo, p_alteracoes);
end;
$$;

comment on function public.criar_versao_parametros_ciclo(uuid, uuid, text, text, text, jsonb) is
  'CA-2-08: cria versão de parâmetros para o ciclo, recusando (e auditando) ciclo aprovado/publicado.';

-- CA-2-10: oficializar versão com parâmetro PENDENTE é recusado e auditado.
create or replace function public.oficializar_versao_parametros(
  p_versao uuid, p_motivo text
) returns void
language plpgsql
security invoker
set search_path to 'pg_catalog', 'public'
as $$
declare
  v_pend int;
  v_mes text;
  v_pend_cod text;
begin
  if coalesce(btrim(p_motivo), '') = '' then
    raise exception 'motivo da oficializacao e obrigatorio' using errcode = 'check_violation';
  end if;
  -- PENDENTE = sem valor de verdade (valor nulo ou o literal 'PENDENTE').
  -- A coluna pendente_de é a trilha da pergunta de origem (Q-08, Q-22...) e
  -- NÃO significa que o parâmetro esteja sem valor.
  select count(*), coalesce(min(parametro_codigo), '') into v_pend, v_pend_cod
    from public.parametros_valor
   where versao_id = p_versao
     and (valor_numero is null and valor_json is null
          and (valor_texto is null or valor_texto = 'PENDENTE'));
  if v_pend > 0 then
    perform public.registrar_negativa_parametros('oficializar',
      p_versao::text, 'versão tem ' || v_pend || ' parâmetro(s) PENDENTE(s) (' || v_pend_cod || ') — CA-2-10');
    raise exception 'versao tem % parametro(s) PENDENTE(s) — oficializacao recusada e auditada (CA-2-10)', v_pend
      using errcode = 'check_violation';
  end if;
  select mes_referencia into v_mes from public.parametros_versao where versao_id = p_versao;
  if not found then
    raise exception 'versao inexistente' using errcode = 'no_data_found';
  end if;
  -- uma oficial por mês: a atual vira substituida
  update public.parametros_versao set status = 'substituida'
   where mes_referencia = v_mes and status = 'oficial';
  update public.parametros_versao set status = 'oficial'
   where versao_id = p_versao;
end;
$$;

comment on function public.oficializar_versao_parametros(uuid, text) is
  'CA-2-10: oficializa versão sem parâmetro PENDENTE; recusa (e audita) com pendência; a oficial anterior vira substituída e segue consultável.';

end;
