begin;
create table public.meta_transferencia (
 id uuid primary key default gen_random_uuid(), ciclo_id uuid not null references public.ciclo_meta,
 autor uuid not null, origem jsonb not null, destino jsonb not null, valor numeric not null,
 motivo text not null, criada_em timestamptz not null default now()
);
create table public.meta_transferencia_linha (
 transferencia_id uuid not null references public.meta_transferencia,
 linha_id uuid not null references public.meta_linha(meta_linha_id),
 delta numeric not null, primary key (transferencia_id,linha_id)
);
create index on public.meta_transferencia_linha(linha_id);
alter table public.meta_transferencia enable row level security;
alter table public.meta_transferencia_linha enable row level security;
revoke all on public.meta_transferencia,public.meta_transferencia_linha from public,anon,authenticated;
grant select (linha_id,delta) on public.meta_transferencia_linha to authenticated;
create policy deltas_visiveis on public.meta_transferencia_linha for select to authenticated
 using (exists(select 1 from public.meta_linha m where m.meta_linha_id=linha_id));
create view public.vw_meta_linha_vigente with (security_invoker=true) as
select m.meta_linha_id,m.referencia_ciclo,m.cliente,m.sku,m.cliente_nome,m.produto_nome,m.linha_produto,
 m.supervisor,m.promotor,m.regime,m.meta_original,m.gap_linha+coalesce(d.valor,0) gap_linha,
 m.meta_final+coalesce(d.valor,0) meta_final,m.memoria,m.criado_em
from public.meta_linha m left join (select linha_id,sum(delta) valor from public.meta_transferencia_linha group by linha_id) d on d.linha_id=m.meta_linha_id;
revoke all on public.vw_meta_linha_vigente from public,anon;
grant select on public.vw_meta_linha_vigente to authenticated;
create or replace view public.vw_meta_supervisor with (security_invoker=true) as
select referencia_ciclo,supervisor,count(*) combinacoes,count(distinct cliente) clientes,sum(meta_original) meta_original,sum(gap_linha) gap_linha,sum(meta_final) meta_final from public.vw_meta_linha_vigente group by 1,2;
create or replace view public.vw_meta_promotor with (security_invoker=true) as
select referencia_ciclo,supervisor,promotor,count(*) combinacoes,count(distinct cliente) clientes,sum(meta_original) meta_original,sum(gap_linha) gap_linha,sum(meta_final) meta_final from public.vw_meta_linha_vigente group by 1,2,3;
create or replace view public.vw_meta_regime with (security_invoker=true) as
select referencia_ciclo,regime,count(*) combinacoes,sum(meta_original) meta_original,sum(gap_linha) gap_linha,sum(meta_final) meta_final from public.vw_meta_linha_vigente group by 1,2;

create function public.transferir_meta_vigente(p_mes text,p_origem jsonb default null,p_destino jsonb default null,p_valor numeric default null,p_motivo text default null,p_revisao bigint default null)
returns jsonb language plpgsql security definer set search_path=pg_catalog,public as $$
declare
 c public.ciclo_meta; total numeric; negativas bigint; n bigint; rev bigint; tid uuid;
 unidade jsonb; idx int; parcela record; distribuido numeric; origens uuid[] := '{}'; ids uuid[] := '{}'; valores numeric[] := '{}';
begin
 if auth.uid() is null or not private.has_operation('editar_parametros') or not exists
 (select 1 from public.carteiras_de('consulta_diretoria',p_mes) x where x='EMPRESA') then
  raise exception 'Ajuste exige acesso à empresa e permissão de editar parâmetros.' using errcode='42501';
 end if;
 select * into c from public.ciclo_meta where mes_referencia=p_mes and status='publicado' for update;
 if not found or p_mes <= '2026-10' then return jsonb_build_object('habilitado',false,'motivo','O ajuste imediato começa no próximo ciclo publicado que fechar na Meta Diretoria.'); end if;
 select count(*),sum(meta_final),count(*) filter(where meta_final<0 or meta_final<>round(meta_final,2))
 into n,total,negativas from public.vw_meta_linha_vigente where referencia_ciclo=p_mes;
 if n=0 or total is distinct from c.meta_diretoria or negativas>0 then
   return jsonb_build_object('habilitado',false,'motivo','A meta precisa fechar na Meta Diretoria, em centavos e sem linhas negativas.');
 end if;
 select count(*) into rev from public.meta_transferencia where ciclo_id=c.ciclo_id;
 if p_origem is null and p_destino is null and p_valor is null then
   return jsonb_build_object('habilitado',true,'revisao',rev);
 end if;
 if p_revisao is distinct from rev then raise exception 'A meta mudou. Atualize a consulta antes de salvar.'; end if;
 if p_valor is null or not (p_valor>0 and p_valor<=c.meta_diretoria and p_valor=round(p_valor,2))
   or coalesce(length(btrim(p_motivo)),0) not between 1 and 500 then raise exception 'Informe um valor em centavos e um motivo.'; end if;
 for idx in 1..2 loop
   unidade := case when idx=1 then p_origem else p_destino end;
   if jsonb_typeof(unidade) is distinct from 'object' or coalesce(btrim(unidade->>'promotor'),'')=''
      or not (unidade ? 'supervisor') or (unidade->>'sku' is not null and unidade->>'cliente' is null) then
     raise exception 'Selecione uma origem e um destino válidos.';
   end if;
   if not exists(select 1 from public.meta_linha m where m.referencia_ciclo=p_mes
     and m.promotor=unidade->>'promotor' and m.supervisor is not distinct from unidade->>'supervisor'
     and (unidade->>'cliente' is null or m.cliente=unidade->>'cliente')
     and (unidade->>'sku' is null or m.sku=unidade->>'sku') and m.meta_final>0) then
      raise exception 'O ajuste imediato só atende metas existentes com base positiva.';
   end if;
   distribuido := 0;
   for parcela in
     with elegiveis as (
       select m.meta_linha_id id,m.meta_final saldo from public.vw_meta_linha_vigente m
       where m.referencia_ciclo=p_mes and m.promotor=unidade->>'promotor' and m.supervisor is not distinct from unidade->>'supervisor'
       and (unidade->>'cliente' is null or m.cliente=unidade->>'cliente') and (unidade->>'sku' is null or m.sku=unidade->>'sku') and m.meta_final>0
     ), pesos as (
       select id,saldo,sum(saldo) over(order by id rows unbounded preceding) acumulado,sum(saldo) over() peso from elegiveis
     ) select id, (floor(p_valor*100*acumulado/peso)-floor(p_valor*100*(acumulado-saldo)/peso))/100 valor, peso from pesos
   loop
     if idx=1 and p_valor>parcela.peso then raise exception 'Valor maior que a meta disponível na origem.'; end if;
     if idx=2 and parcela.id=any(origens) then raise exception 'Origem e destino se sobrepõem.'; end if;
     if idx=1 then origens := array_append(origens,parcela.id); end if;
     if parcela.valor<>0 then
       ids := array_append(ids,parcela.id);
       valores := array_append(valores,case when idx=1 then -parcela.valor else parcela.valor end);
     end if;
     distribuido := distribuido+parcela.valor;
   end loop;
   if distribuido<>p_valor then raise exception 'Origem ou destino sem meta positiva disponível para o rateio.'; end if;
 end loop;
 insert into public.meta_transferencia(ciclo_id,autor,origem,destino,valor,motivo) values(c.ciclo_id,auth.uid(),p_origem,p_destino,p_valor,btrim(p_motivo)) returning id into tid;
 insert into public.meta_transferencia_linha(transferencia_id,linha_id,delta) select tid,x.id,x.delta from unnest(ids,valores) x(id,delta);
 return jsonb_build_object('habilitado',true,'revisao',rev+1,'transferencia_id',tid);
end;
$$;
revoke all on function public.transferir_meta_vigente(text,jsonb,jsonb,numeric,text,bigint) from public,anon,authenticated;
grant execute on function public.transferir_meta_vigente(text,jsonb,jsonb,numeric,text,bigint) to authenticated;
commit;
