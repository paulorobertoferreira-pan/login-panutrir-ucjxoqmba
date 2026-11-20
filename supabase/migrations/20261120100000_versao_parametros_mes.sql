-- F2 (Alex, 20/11): versão de parâmetros de um MÊS NOVO (ex.: Dez/26).
--
-- criar_versao_parametros herda o mês da origem. Para Dez/26 isso gera uma versão
-- com mês 2026-10, que a oficialização trataria como a da Out/26 e substituiria
-- a oficial publicada (oficializar_versao_parametros só mantém UMA oficial por
-- mês). Esta função cria a versão com o mês informado, copiando os parâmetros,
-- sortimento e substituição da origem. A função original fica intacta.
--
-- Regra preservada: origem tem que ser oficial; autor e motivo obrigatórios; o
-- mês informado tem o formato AAAA-MM e NÃO pode ser igual ao de uma versão já
-- oficial (para não substituí-la por engano).
begin;

create or replace function public.criar_versao_parametros_mes(
  p_versao_origem uuid,
  p_novo_codigo   text,
  p_mes_referencia text,
  p_autor         text,
  p_motivo        text,
  p_alteracoes    jsonb default '{}'::jsonb
) returns uuid
language plpgsql
set search_path = pg_catalog, public
as $$
declare
  v_origem  public.parametros_versao;
  v_novo_id uuid;
  v_chave   text;
  v_valor   jsonb;
begin
  if coalesce(btrim(p_autor), '') = '' then
    raise exception 'autor da versao e obrigatorio' using errcode = 'check_violation';
  end if;
  if coalesce(btrim(p_motivo), '') = '' then
    raise exception 'motivo da nova versao e obrigatorio' using errcode = 'check_violation';
  end if;
  if p_mes_referencia !~ '^[0-9]{4}-(0[1-9]|1[0-2])$' then
    raise exception 'mes de referencia invalido: % (use AAAA-MM)', p_mes_referencia
      using errcode = '22023';
  end if;

  select * into v_origem from public.parametros_versao where versao_id = p_versao_origem;
  if not found then
    raise exception 'versao de origem inexistente: %', p_versao_origem using errcode = 'no_data_found';
  end if;
  if v_origem.status <> 'oficial' then
    raise exception 'a origem precisa ser oficial (esta esta %)', v_origem.status using errcode = 'check_violation';
  end if;

  -- não pode criar uma versão no mês de uma oficial já existente
  if exists (select 1 from public.parametros_versao
              where mes_referencia = p_mes_referencia and status = 'oficial') then
    raise exception 'ja existe versao oficial em %; crie a versao com outro mes ou substitua por nova versao do ciclo', p_mes_referencia
      using errcode = 'check_violation';
  end if;

  insert into public.parametros_versao
    (versao_codigo, mes_referencia, status, origem, autor, motivo, versao_anterior)
  values
    (p_novo_codigo, p_mes_referencia, 'rascunho', v_origem.origem, p_autor, p_motivo, v_origem.versao_id)
  returning versao_id into v_novo_id;

  insert into public.parametros_valor
    (versao_id, parametro_codigo, descricao, valor_numero, valor_texto, valor_json, unidade, pendente_de)
  select v_novo_id, parametro_codigo, descricao, valor_numero, valor_texto, valor_json, unidade, pendente_de
    from public.parametros_valor where versao_id = p_versao_origem;

  for v_chave, v_valor in select key, value from jsonb_each(coalesce(p_alteracoes, '{}'::jsonb)) loop
    if not exists (select 1 from public.parametros_valor
                    where versao_id = v_novo_id and parametro_codigo = v_chave) then
      raise exception 'parametro % nao existe na versao de origem', v_chave using errcode = 'check_violation';
    end if;
    update public.parametros_valor
       set valor_numero = case when jsonb_typeof(v_valor) = 'number' then (v_valor #>> '{}')::numeric end,
           valor_texto  = case when jsonb_typeof(v_valor) = 'string' then v_valor #>> '{}' end,
           valor_json   = case when jsonb_typeof(v_valor) in ('object', 'array') then v_valor end
     where versao_id = v_novo_id and parametro_codigo = v_chave;
  end loop;

  insert into public.sortimento_restrito (versao_id, rede, uf, sku_codigo)
  select v_novo_id, rede, uf, sku_codigo from public.sortimento_restrito where versao_id = p_versao_origem;

  insert into public.substituicao (versao_id, rede, uf, sku_origem, sku_destino, taxa)
  select v_novo_id, rede, uf, sku_origem, sku_destino, taxa from public.substituicao where versao_id = p_versao_origem;

  return v_novo_id;
end;
$$;

comment on function public.criar_versao_parametros_mes(uuid, text, text, text, text, jsonb) is
  'Versão de parâmetros de um mês novo (ex.: Dez/26). Recusa mês já oficial. Função original criar_versao_parametros mantida sem mudança.';

commit;
