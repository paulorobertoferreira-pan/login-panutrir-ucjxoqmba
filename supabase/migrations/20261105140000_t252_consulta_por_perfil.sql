-- F2-T5.2 / SPEC-2-005 (CA-2-24) — consulta por perfil.
--
-- A consulta de saída (extrato_saida, T2.6.1) passa a aceitar o PERFIL do
-- usuário: supervisor vê a própria equipe (carteiras do papel
-- consulta_supervisor), promotor a própria carteira, Diretoria a empresa
-- (carteira 'EMPRESA'). Sem vínculo → vazio (fail-closed, T2.5.1).
--
-- A fonte é a meta publicada do ciclo (mesma construção da T2.6.1); o recorte
-- por carteira usa carteiras_de(papel, ciclo) do usuário corrente.

begin;

-- Consulta por perfil: o papel vem como parâmetro (a tela usa o papel do
-- usuário); a carteira vem de consulta_vinculo via auth.uid().
create or replace function public.consulta_por_perfil(
  p_ciclo text, p_papel text
)
returns table (
  supervisor     text,
  promotor       text,
  cliente        text,
  cliente_nome   text,
  sku            text,
  produto_nome   text,
  linha_produto  text,
  regime         text,
  meta_original  numeric,
  gap_linha      numeric,
  meta_final     numeric
)
language sql
stable
security invoker
set search_path to 'pg_catalog', 'public'
as $$
  select m.supervisor, m.promotor, m.cliente, m.cliente_nome,
         m.sku, m.produto_nome, m.linha_produto, m.regime,
         m.meta_original, m.gap_linha, m.meta_final
    from public.meta_linha m
   where m.referencia_ciclo = p_ciclo
     -- só a meta publicada (mesma construção do extrato_saida, T2.6.1)
     and exists (select 1 from public.ciclo_meta cm
                 where cm.mes_referencia = p_ciclo and cm.status = 'publicado')
     -- recorte por perfil: diretoria vê tudo ('EMPRESA'); supervisor vê as
     -- carteiras dele (a equipe = clientes marcados com o supervisor); promotor
     -- vê a carteira dele
     and (
       'EMPRESA' in (select carteiras_de(p_papel, p_ciclo))
       or (p_papel = 'consulta_supervisor'
           and m.supervisor::text in (select carteiras_de(p_papel, p_ciclo)))
       or (p_papel = 'consulta_promotor'
           and m.promotor::text in (select carteiras_de(p_papel, p_ciclo)))
     );
$$;

comment on function public.consulta_por_perfil(text, text) is
  'CA-2-24: consulta por perfil — supervisor vê a equipe, promotor a carteira, diretoria a empresa; sem vínculo, vazio (fail-closed).';

end;