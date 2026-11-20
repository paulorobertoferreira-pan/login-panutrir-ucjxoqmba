begin;
create table if not exists public.redistribuicao_promotor_ajuste (
  ajuste_id uuid primary key default gen_random_uuid(),
  ciclo_id uuid not null references public.ciclo_meta(ciclo_id),
  versao_id uuid not null references public.parametros_versao(versao_id),
  base_hash text not null,
  ator uuid not null,
  supervisor text,
  promotor text not null,
  valor numeric(16,2) not null check (valor <> 0),
  motivo text not null check (length(motivo) between 1 and 500),
  criado_em timestamptz not null default now()
);
alter table public.redistribuicao_promotor_ajuste enable row level security;
revoke all on public.redistribuicao_promotor_ajuste from public, anon, authenticated;

-- Diário do rascunho: não edita meta_linha, nem cria/publica meta oficial.
create or replace function public.ajustar_meta_promotor_rascunho(
  p_mes text, p_promotor text default null, p_supervisor text default null,
  p_acao text default null, p_valor numeric default null, p_motivo text default null,
  p_saldo_esperado numeric default null
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
    select count(*), coalesce(sum(meta_final),0) into v_linhas,v_promotor from public.meta_linha
     where referencia_ciclo = p_mes and promotor = p_promotor and supervisor is not distinct from p_supervisor;
    if v_linhas = 0 or v_promotor <= 0 then
      raise exception 'Este promotor não tem meta positiva na base. A primeira meta deve ser atribuída ao PDV novo.';
    end if;
    select v_promotor + coalesce(sum(valor),0) into v_promotor from public.redistribuicao_promotor_ajuste
     where ciclo_id = c.ciclo_id and versao_id = c.parametros_versao_id and base_hash = v_hash
       and promotor = p_promotor and supervisor is not distinct from p_supervisor;
    if p_acao = 'colocar' then
      if v_saldo <= 0 or p_valor > v_saldo then raise exception 'Valor maior que o saldo a alocar.'; end if;
      v_ajuste := p_valor;
    else
      if v_saldo > 0 then raise exception 'Ainda há saldo a alocar: use Colocar.'; end if;
      if p_valor > v_promotor then raise exception 'Valor maior que a meta do promotor.'; end if;
      if v_alocado - p_valor > c.meta_diretoria then raise exception 'Retire valor suficiente para respeitar a Meta Diretoria.'; end if;
      v_ajuste := -p_valor;
    end if;
    insert into public.redistribuicao_promotor_ajuste(ciclo_id,versao_id,base_hash,ator,supervisor,promotor,valor,motivo)
      values(c.ciclo_id,c.parametros_versao_id,v_hash,auth.uid(),p_supervisor,p_promotor,v_ajuste,btrim(p_motivo));
    v_alocado := v_alocado + v_ajuste;
    v_saldo := c.meta_diretoria - v_alocado;
  end if;
  select coalesce(jsonb_agg(to_jsonb(g)), '[]'::jsonb) into v_grupos from (
    select supervisor,promotor,sum(valor) as ajuste from public.redistribuicao_promotor_ajuste
     where ciclo_id = c.ciclo_id and versao_id = c.parametros_versao_id and base_hash = v_hash
     group by supervisor,promotor having sum(valor) <> 0
  ) g;
  return jsonb_build_object('alocado',v_alocado,'saldo',v_saldo,'meta_diretoria',c.meta_diretoria,'grupos',v_grupos);
end;
$$;
revoke all on function public.ajustar_meta_promotor_rascunho(text,text,text,text,numeric,text,numeric) from public, anon, authenticated;
grant execute on function public.ajustar_meta_promotor_rascunho(text,text,text,text,numeric,text,numeric) to authenticated;
commit;
