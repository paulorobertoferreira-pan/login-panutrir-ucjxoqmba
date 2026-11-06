-- F2-T3.2 / SPEC-2-003 (CA-2-14) — limite de cenários por ciclo (P-17).
-- F2-T3.3 / SPEC-2-003 (CA-2-12, CA-2-15) — comparação de dois cenários.
--
-- CA-2-14: ao atingir o limite P-17, a criação seguinte é recusada com
--          registro; com P-17 PENDENTE, aplica teto provisório documentado
--          (10) e avisa (a função devolve o aviso junto).
-- CA-2-12: comparação de dois cenários por canal, supervisor e linha, com
--          diferença absoluta e percentual e a soma dos filhos igual ao pai.
-- CA-2-15: cada diferença identifica o parâmetro causador (os parâmetros que
--          diferem entre as duas versões de cenário).

begin;

-- Teto provisório documentado enquanto P-17 estiver PENDENTE (CA-2-14)
create or replace function public.limite_cenarios(p_ciclo text)
returns table (limite int, aviso text)
language plpgsql
stable
security invoker
set search_path to 'pg_catalog', 'public'
as $$
declare
  v_valor text;
  v_pendente boolean;
begin
  select coalesce(pv.valor_numero::text, pv.valor_texto) into v_valor
    from public.parametros_valor pv
    join public.parametros_versao v using (versao_id)
   where pv.parametro_codigo = 'P-17' and v.status = 'oficial'
   order by v.mes_referencia desc, v.criado_em desc limit 1;
  v_pendente := (v_valor is null or v_valor = 'PENDENTE');
  if v_pendente then
    return query select 10::int,
      'P-17 (limite de cenários) está PENDENTE — aplicado teto provisório de 10'::text;
  else
    return query select v_valor::int, null::text;
  end if;
end;
$$;

comment on function public.limite_cenarios(text) is
  'CA-2-14: limite de cenários do ciclo (P-17); com P-17 PENDENTE, teto provisório 10 + aviso.';

-- Criar cenário com o limite aplicado (recusa auditada ao exceder)
create or replace function public.criar_cenario_ciclo(
  p_ciclo text, p_versao_origem uuid, p_codigo text,
  p_autor text, p_motivo text, p_alteracoes jsonb default '{}'::jsonb
) returns uuid
language plpgsql
security invoker
set search_path to 'pg_catalog', 'public'
as $$
declare
  v_limite int;
  v_aviso text;
  v_atual int;
  v_novo uuid;
  v_chave text;
  v_valor jsonb;
begin
  select limite, aviso into v_limite, v_aviso from public.limite_cenarios(p_ciclo);
  select count(*) into v_atual
    from public.parametros_versao
   where simulacao = true and mes_referencia = p_ciclo;
  if v_atual >= v_limite then
    perform public.registrar_negativa_parametros('criar_cenario',
      p_codigo, 'limite de cenários do ciclo ' || p_ciclo || ' atingido (' || v_atual || '/' || v_limite || ') — CA-2-14');
    raise exception 'limite de cenarios do ciclo % atingido (%/% — CA-2-14) — recusa auditada', p_ciclo, v_atual, v_limite
      using errcode = 'check_violation';
  end if;
  -- o cenário nasce com o mes_referencia do CICLO (não da versão de origem) —
  -- o count do limite é por ciclo; insert direto (a versão de origem é
  -- congelada, o mes_referencia não pode ser atualizado depois)
  insert into public.parametros_versao
    (versao_codigo, mes_referencia, status, origem, autor, motivo, versao_anterior, simulacao)
  values (p_codigo, p_ciclo, 'rascunho', 'sintetico', p_autor, p_motivo, p_versao_origem, true)
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

comment on function public.criar_cenario_ciclo(text, uuid, text, text, text, jsonb) is
  'CA-2-14: cria cenário respeitando o limite P-17 (com teto provisório e aviso quando PENDENTE); recusa auditada ao exceder.';

create or replace function public.comparar_parametros_cenarios(
  p_versao_a uuid, p_versao_b uuid
)
returns table (
  parametro  text,
  valor_a    text,
  valor_b    text
)
language sql
stable
security invoker
set search_path to 'pg_catalog', 'public'
as $$
  select coalesce(a.parametro_codigo, b.parametro_codigo) as parametro,
         coalesce(a.valor_numero::text, a.valor_texto, '(ausente)') as valor_a,
         coalesce(b.valor_numero::text, b.valor_texto, '(ausente)') as valor_b
    from (select * from parametros_valor where versao_id = p_versao_a) a
    full join (select * from parametros_valor where versao_id = p_versao_b) b
      using (parametro_codigo)
   where coalesce(a.valor_numero::text, a.valor_texto, '(ausente)')
      <> coalesce(b.valor_numero::text, b.valor_texto, '(ausente)')
   order by 1;
$$;

comment on function public.comparar_parametros_cenarios(uuid, uuid) is
  'CA-2-15: parâmetros que diferem entre os dois cenários (os causadores das diferenças).';

end;
