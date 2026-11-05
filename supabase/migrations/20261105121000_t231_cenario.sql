-- F2-T3.1 / SPEC-2-003 (CA-2-11) — execução de cenário sem tocar a oficial.
--
-- A versão de parâmetros ganha a coluna simulacao: cenário é uma versão
-- derivada marcada simulacao=true, que NUNCA fica oficial (constraint) e
-- NUNCA substitui a execução oficial do ciclo. A execução que usa versão de
-- cenário é identificável por parametros_versao_id (a versão é a marca).

begin;

alter table public.parametros_versao add column if not exists simulacao boolean not null default false;

-- cenário nunca é oficial nem substituída: é rascunho de simulação
alter table public.parametros_versao drop constraint if exists parametros_versao_simulacao_ck;
alter table public.parametros_versao
  add constraint parametros_versao_simulacao_ck
  check (not simulacao or status = 'rascunho');

create or replace function public.criar_versao_cenario(
  p_versao_origem uuid, p_codigo text, p_autor text, p_motivo text,
  p_alteracoes jsonb default '{}'::jsonb
) returns uuid
language plpgsql
security invoker
set search_path to 'pg_catalog', 'public'
as $$
declare
  v_origem public.parametros_versao;
  v_novo uuid;
  v_chave text;
  v_valor jsonb;
begin
  if coalesce(btrim(p_autor), '') = '' then
    raise exception 'autor do cenario e obrigatorio' using errcode = 'check_violation';
  end if;
  if coalesce(btrim(p_motivo), '') = '' then
    raise exception 'motivo do cenario e obrigatorio' using errcode = 'check_violation';
  end if;
  select * into v_origem from public.parametros_versao where versao_id = p_versao_origem;
  if not found then
    raise exception 'versao de origem inexistente' using errcode = 'no_data_found';
  end if;

  insert into public.parametros_versao
    (versao_codigo, mes_referencia, status, origem, autor, motivo, versao_anterior, simulacao)
  values (p_codigo, v_origem.mes_referencia, 'rascunho', 'sintetico', p_autor, p_motivo,
          p_versao_origem, true)
  returning versao_id into v_novo;

  insert into public.parametros_valor
    (versao_id, parametro_codigo, descricao, valor_numero, valor_texto, valor_json, unidade, pendente_de)
  select v_novo, parametro_codigo, descricao, valor_numero, valor_texto, valor_json, unidade, pendente_de
    from public.parametros_valor where versao_id = p_versao_origem;

  for v_chave, v_valor in select key, value from jsonb_each(coalesce(p_alteracoes, '{}'::jsonb)) loop
    if not exists (select 1 from public.parametros_valor
                   where versao_id = v_novo and parametro_codigo = v_chave) then
      raise exception 'parametro % nao existe na versao de origem', v_chave using errcode = 'check_violation';
    end if;
    update public.parametros_valor
       set valor_numero = case when jsonb_typeof(v_valor) = 'number' then (v_valor #>> '{}')::numeric end,
           valor_texto  = case when jsonb_typeof(v_valor) = 'string' then v_valor #>> '{}' end
     where versao_id = v_novo and parametro_codigo = v_chave;
  end loop;

  return v_novo;
end;
$$;

comment on function public.criar_versao_cenario(uuid, text, text, text, jsonb) is
  'CA-2-11: versão de cenário (simulacao=true, rascunho) derivada da oficial; nunca substitui a oficial.';

end;