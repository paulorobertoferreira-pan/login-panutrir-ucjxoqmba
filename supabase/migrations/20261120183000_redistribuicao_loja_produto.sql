begin;
alter table public.redistribuicao_promotor_ajuste add column if not exists cliente text, add column if not exists sku text, add column if not exists rateio jsonb;
create or replace function public.ajustar_meta_rascunho(
  p_mes text, p_promotor text default null, p_supervisor text default null,
  p_acao text default null, p_valor numeric default null, p_motivo text default null,
  p_saldo_esperado numeric default null, p_cliente text default null, p_sku text default null
) returns jsonb language plpgsql security definer
set search_path = pg_catalog, public as $$
declare
  c public.ciclo_meta;
  v_hash text;
  v_base numeric;
  v_alocado numeric;
  v_saldo numeric;
  v_promotor numeric;
  v_ajuste numeric;
  v_linhas bigint;
  v_grupos jsonb;
  v_rateio jsonb;
  v_detalhes jsonb;
  v_positivas numeric;
  v_peso_original boolean := false;
begin
  if auth.uid() is null or not private.has_operation('editar_parametros')
     or not exists (select 1 from public.carteiras_de('consulta_diretoria', p_mes) x where x = 'EMPRESA') then
    raise exception 'Ajuste exige acesso de diretoria e permissão de editar parâmetros.' using errcode = '42501';
  end if;
  select * into c from public.ciclo_meta where mes_referencia = p_mes and status = 'publicado' for update;
  if not found then raise exception 'Ciclo publicado não encontrado.'; end if;
  select count(*), coalesce(sum(meta_final),0), md5(string_agg(jsonb_build_array(meta_linha_id, cliente, sku, supervisor, promotor, meta_final)::text, E'\n' order by meta_linha_id))
    into v_linhas, v_base, v_hash from public.meta_linha where referencia_ciclo = p_mes;
  if v_linhas = 0 then raise exception 'A meta base não está disponível.'; end if;

  if exists (select 1 from public.redistribuicao_promotor_ajuste where ciclo_id=c.ciclo_id
     and versao_id=c.parametros_versao_id and base_hash=v_hash and rateio is null) then
    raise exception 'Há ajustes anteriores sem detalhamento que precisam ser reconciliados.';
  end if;
  select v_base + coalesce(sum(valor),0) into v_alocado from public.redistribuicao_promotor_ajuste
   where ciclo_id = c.ciclo_id and versao_id = c.parametros_versao_id and base_hash = v_hash;
  v_saldo := c.meta_diretoria - v_alocado;
  if p_acao is not null then
    if p_promotor is null or btrim(p_promotor) = '' or p_acao not in ('colocar','retirar')
       or p_valor is null or not (p_valor > 0 and p_valor <= c.meta_diretoria and p_valor = round(p_valor,2))
       or coalesce(length(btrim(p_motivo)),0) not between 1 and 500 then
      raise exception 'Informe um valor positivo em centavos e um motivo.';
    end if;
    if p_saldo_esperado is distinct from v_saldo then
      raise exception 'O saldo mudou. Atualize a consulta e tente novamente.';
    end if;
    if p_sku is not null and p_cliente is null then raise exception 'Selecione a loja do produto.'; end if;
    with deltas as (
      select item.key, sum(item.value::numeric) delta
      from public.redistribuicao_promotor_ajuste a cross join lateral jsonb_each_text(a.rateio) item
      where a.ciclo_id=c.ciclo_id and a.versao_id=c.parametros_versao_id and a.base_hash=v_hash group by item.key
    ), alvo as (
      select m.meta_linha_id id, m.meta_final original, m.meta_final + coalesce(d.delta,0) saldo
      from public.meta_linha m left join deltas d on d.key=m.meta_linha_id::text
      where m.referencia_ciclo=p_mes and m.promotor=p_promotor and m.supervisor is not distinct from p_supervisor
        and (p_cliente is null or m.cliente=p_cliente) and (p_sku is null or m.sku=p_sku)
    ) select coalesce(sum(original),0),coalesce(sum(saldo),0),coalesce(sum(greatest(saldo,0)),0)
      into v_base,v_promotor,v_positivas from alvo;
    if v_base <= 0 then
      raise exception 'Este destino não tem meta positiva na base. A primeira meta exige o fluxo de PDV novo.';
    end if;
    if p_acao = 'colocar' then
      if v_saldo <= 0 or p_valor > v_saldo then raise exception 'Valor maior que o saldo a alocar.'; end if;
      v_ajuste := p_valor;
      v_peso_original := v_positivas = 0;
    else
      if v_saldo > 0 then raise exception 'Ainda há saldo a alocar: use Colocar.'; end if;
      if p_valor > v_promotor then raise exception 'Valor maior que a meta do destino.'; end if;
      if v_alocado - p_valor > c.meta_diretoria then raise exception 'Retire valor suficiente para respeitar a Meta Diretoria.'; end if;
      v_ajuste := -p_valor;
    end if;
    -- Rateio cumulativo em centavos preserva o valor exato e nunca debita mais que a linha positiva.
    with deltas as (
      select item.key, sum(item.value::numeric) delta
      from public.redistribuicao_promotor_ajuste a cross join lateral jsonb_each_text(a.rateio) item
      where a.ciclo_id=c.ciclo_id and a.versao_id=c.parametros_versao_id and a.base_hash=v_hash group by item.key
    ), elegiveis as (
      select m.meta_linha_id id, case when v_peso_original then m.meta_final else m.meta_final + coalesce(d.delta,0) end saldo
      from public.meta_linha m left join deltas d on d.key=m.meta_linha_id::text
      where m.referencia_ciclo=p_mes and m.promotor=p_promotor and m.supervisor is not distinct from p_supervisor
        and (p_cliente is null or m.cliente=p_cliente) and (p_sku is null or m.sku=p_sku)
        and (case when v_peso_original then m.meta_final else m.meta_final + coalesce(d.delta,0) end) > 0
    ), acum as (
      select id,saldo,sum(saldo) over(order by id rows unbounded preceding) total from elegiveis
    ), parcelas as (
      select id, sign(v_ajuste) * (floor(abs(v_ajuste)*100*total/(select max(total) from acum))
        - floor(abs(v_ajuste)*100*(total-saldo)/(select max(total) from acum)))/100 parcela from acum
    ) select jsonb_object_agg(id,parcela) into v_rateio from parcelas where parcela<>0;
    if (select sum(value::numeric) from jsonb_each_text(v_rateio)) is distinct from v_ajuste then
      raise exception 'O rateio não fechou no valor do ajuste.';
    end if;
    insert into public.redistribuicao_promotor_ajuste(ciclo_id,versao_id,base_hash,ator,supervisor,promotor,valor,motivo,cliente,sku,rateio)
      values(c.ciclo_id,c.parametros_versao_id,v_hash,auth.uid(),p_supervisor,p_promotor,v_ajuste,btrim(p_motivo),p_cliente,p_sku,v_rateio);
    v_alocado := v_alocado + v_ajuste;
    v_saldo := c.meta_diretoria - v_alocado;
  end if;
  with deltas as (
    select item.key, sum(item.value::numeric) ajuste
    from public.redistribuicao_promotor_ajuste a cross join lateral jsonb_each_text(a.rateio) item
    where a.ciclo_id=c.ciclo_id and a.versao_id=c.parametros_versao_id and a.base_hash=v_hash group by item.key
  ), impactadas as (
    select m.supervisor,m.promotor,m.cliente,m.sku,d.ajuste from public.meta_linha m
    join deltas d on d.key=m.meta_linha_id::text where m.referencia_ciclo=p_mes
  ), grupos as (select supervisor,promotor,sum(ajuste) ajuste from impactadas group by 1,2),
    lojas as (select supervisor,promotor,cliente,sum(ajuste) ajuste from impactadas group by 1,2,3)
  select coalesce((select jsonb_agg(to_jsonb(g)) from grupos g),'[]'),
         jsonb_build_object('lojas',coalesce((select jsonb_agg(to_jsonb(l)) from lojas l),'[]'),
                            'produtos',coalesce((select jsonb_agg(to_jsonb(i)) from impactadas i),'[]'))
    into v_grupos,v_detalhes;
  if p_acao is null and p_cliente is not null then
    select coalesce(sum(m.meta_final),0) into v_base from public.meta_linha m
      where m.referencia_ciclo=p_mes and m.promotor=p_promotor and m.supervisor is not distinct from p_supervisor
        and m.cliente=p_cliente and (p_sku is null or m.sku=p_sku);
  else v_base := null;
  end if;
  return jsonb_build_object('alocado',v_alocado,'saldo',v_saldo,'meta_diretoria',c.meta_diretoria,
    'grupos',v_grupos,'meta_alvo',v_base) || v_detalhes;
end;
$$;
revoke all on function public.ajustar_meta_rascunho(text,text,text,text,numeric,text,numeric,text,text) from public, anon, authenticated;
grant execute on function public.ajustar_meta_rascunho(text,text,text,text,numeric,text,numeric,text,text) to authenticated;

-- O painel anterior continua usando o mesmo diário e as mesmas travas.
create or replace function public.ajustar_meta_promotor_rascunho(
  p_mes text, p_promotor text default null, p_supervisor text default null,
  p_acao text default null, p_valor numeric default null, p_motivo text default null,
  p_saldo_esperado numeric default null
) returns jsonb language sql security invoker set search_path=pg_catalog, public as $$
  select public.ajustar_meta_rascunho(p_mes,p_promotor,p_supervisor,p_acao,p_valor,p_motivo,p_saldo_esperado);
$$;
commit;
