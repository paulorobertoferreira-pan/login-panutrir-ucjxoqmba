-- F2-T1.2 / SPEC-2-001 (CA-2-05) — herança de parâmetros com requer_confirmação.
--
-- Ao criar o ciclo novo (Nov/26 em diante), a versão de parâmetros dele nasce
-- HERDADA do ciclo anterior, com os 4 campos de negócio (P-02 Meta Diretoria,
-- P-05 IS, P-06 dias úteis, P-07 G) marcados como requer_confirmação — o valor
-- herdado é hipótese, não decisão. Execução que usar parâmetro não confirmado
-- sai NÃO reconciliada, com a lista de pendências (CA-2-05).
--
-- Desenho:
--   · criar_ciclo_com_herdanca(ciclo): cria o ciclo_meta do mês + a versão de
--     parâmetros herdada (insert direto, com autor/motivo obrigatórios e
--     mes_referencia do ciclo novo) e marca os 4 campos em requerimento;
--   · requer_confirmação é a coluna pendente_de preenchida com
--     'REQUER_CONFIRMACAO' (os valores vêm do ciclo anterior — a confirmação
--     é da operação/Paulo no ciclo novo);
--   · pendencias_confirmacao(execucao): devolve a lista de parâmetros
--     requeridos não confirmados usados pela execução — alimenta o estado
--     NAO_RECONCILIADA da T2.4.1.

begin;

-- Ciclo novo com versão herdada: os 4 campos de negócio nascem requeridos.
create or replace function public.criar_ciclo_com_herdanca(
  p_ciclo text, p_autor text, p_motivo text
) returns uuid
language plpgsql
security invoker
set search_path to 'pg_catalog', 'public'
as $$
declare
  v_ciclo_anterior text;
  v_versao_origem  uuid;
  v_versao_nova    uuid;
  v_ciclo_id       uuid;
  v_param          text;
begin
  -- o ciclo anterior é o mês imediatamente anterior ao p_ciclo
  v_ciclo_anterior := to_char((to_date(p_ciclo || '-01', 'YYYY-MM-DD') - interval '1 month'), 'YYYY-MM');

  select versao_id into v_versao_origem
    from public.parametros_versao
   where status = 'oficial' and mes_referencia <= v_ciclo_anterior
   order by mes_referencia desc, criado_em desc
   limit 1;
  if not found then
    raise exception 'nenhuma versao oficial para herdar (ciclo anterior %)', v_ciclo_anterior
      using errcode = 'no_data_found';
  end if;

  -- versão nova herda todos os valores, JÁ com mes_referencia do ciclo novo
  -- (o trigger da T3.1 protege a identidade da versão: mes_referencia não muda
  -- depois de criada, então a herança nasce certa)
  insert into public.parametros_versao
    (versao_codigo, mes_referencia, status, origem, autor, motivo, versao_anterior)
  values ('HERDADA-' || p_ciclo, p_ciclo, 'rascunho', 'sintetico', p_autor, p_motivo, v_versao_origem)
  returning versao_id into v_versao_nova;

  insert into public.parametros_valor
    (versao_id, parametro_codigo, descricao, valor_numero, valor_texto, valor_json, unidade, pendente_de)
  select v_versao_nova, parametro_codigo, descricao, valor_numero, valor_texto, valor_json, unidade, pendente_de
    from public.parametros_valor
   where versao_id = v_versao_origem;

  insert into public.sortimento_restrito (versao_id, rede, uf, sku_codigo)
  select v_versao_nova, rede, uf, sku_codigo from public.sortimento_restrito
   where versao_id = v_versao_origem;

  insert into public.substituicao (versao_id, rede, uf, sku_origem, sku_destino, taxa)
  select v_versao_nova, rede, uf, sku_origem, sku_destino, taxa from public.substituicao
   where versao_id = v_versao_origem;

  -- os 4 campos de negócio nascem requerendo confirmação
  foreach v_param in array array['P-02', 'P-05', 'P-06', 'P-07'] loop
    update public.parametros_valor
       set pendente_de = 'REQUER_CONFIRMACAO'
     where versao_id = v_versao_nova and parametro_codigo = v_param;
  end loop;

  -- o ciclo nasce com a versão herdada
  insert into public.ciclo_meta (mes_referencia, status, meta_diretoria, parametros_versao_id, criado_por)
  select p_ciclo, 'rascunho', pv.valor_numero, v_versao_nova, auth.uid()
    from public.parametros_valor pv
   where pv.versao_id = v_versao_nova and pv.parametro_codigo = 'P-02'
  returning ciclo_id into v_ciclo_id;

  return v_ciclo_id;
end;
$$;

comment on function public.criar_ciclo_com_herdanca(text, text, text) is
  'CA-2-05: ciclo novo com versão de parâmetros herdada do ciclo anterior; P-02/P-05/P-06/P-07 nascem requerendo confirmação.';

-- Pendências de confirmação de uma execução: os parâmetros requeridos não
-- confirmados que a versão da execução usa.
create or replace function public.pendencias_confirmacao(p_execucao uuid)
returns table (parametro_codigo text, valor text)
language sql
stable
security invoker
set search_path to 'pg_catalog', 'public'
as $$
  select pv.parametro_codigo,
         coalesce(pv.valor_numero::text, pv.valor_texto, 'PENDENTE') as valor
    from public.execucao_calculo e
    join public.parametros_valor pv on pv.versao_id = e.parametros_versao_id
   where e.execucao_id = p_execucao
     and pv.parametro_codigo in ('P-02','P-05','P-06','P-07')
     and pv.pendente_de = 'REQUER_CONFIRMACAO';
$$;

comment on function public.pendencias_confirmacao(uuid) is
  'CA-2-05: parâmetros requeridos não confirmados usados pela execução — a lista de pendências que força NAO_RECONCILIADA.';

end;