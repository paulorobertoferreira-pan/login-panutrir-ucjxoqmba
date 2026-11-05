-- F2-T6.1 / SPEC-2-006 (CA-2-28, CA-2-31) — consulta de saída com layout lido de parâmetro.
--
-- A SPEC manda que o layout do extrato de saída seja lido do parâmetro P-18
-- (versionado), NUNCA fixo no código: trocar o layout não pode exigir deploy
-- (CA-2-28). Enquanto a Q-22 não for respondida, P-18 fica PENDENTE e o
-- extrato não é enviado ao Metabase (sai em arquivo para conferência local).
--
-- Desenho:
--   · P-18 entra na versão oficial de parâmetros como PENDENTE (valor_texto
--     'PENDENTE', pendente_de 'Q-22') — a versão nova é criada pela RPC
--     existente (T2.2.1), preservando a OUT-2026-v1;
--   · layout_saida(p_ciclo): devolve o layout do P-18 da versão oficial
--     vigente — 'PENDENTE' se não respondido, ou o código do layout (A, B...);
--   · extrato_saida(p_ciclo): devolve a meta PUBLICADA do ciclo no layout
--     pedido. Por construção só lê de meta publicada (rascunho/cenário/não
--     reconciliada ficam de fora — CA-2-30, prova na T2.6.3). O campo de perfil
--     (supervisor/promotor) vai em todas as linhas para a permissão no Metabase.
--   · Nenhum layout é fixo no código: quem interpreta o código do layout é a
--     camada de geração do arquivo (T2.6.2/2.6.3), lendo P-18 a cada execução.

begin;

-- P-18 na versão oficial vigente, como PENDENTE da Q-22 (idempotente).
-- A coluna pendente_de registra a origem da pendência (a Q-22).
insert into public.parametros_valor
  (versao_id, parametro_codigo, descricao, valor_texto, unidade, pendente_de)
select v.versao_id, 'P-18', 'Layout da consulta de saida (Q-22)', 'PENDENTE', 'layout', 'Q-22'
  from public.parametros_versao v
 where v.status = 'oficial'
   and not exists (select 1 from public.parametros_valor pv
                    where pv.versao_id = v.versao_id and pv.parametro_codigo = 'P-18');

comment on table public.parametros_valor is
  'T3.1: parâmetros versionados. P-18 = layout da consulta de saída (Q-22); PENDENTE enquanto sem resposta.';

-- Layout vigente: lê o P-18 da versão oficial do ciclo (a mais recente oficial
-- válida para o ciclo; se não houver, a oficial mais recente).
create or replace function public.layout_saida(p_ciclo text)
returns text
language plpgsql
stable
security invoker
set search_path to 'pg_catalog', 'public'
as $$
declare
  v_layout text;
begin
  select pv.valor_texto into v_layout
    from public.parametros_valor pv
    join public.parametros_versao v using (versao_id)
   where pv.parametro_codigo = 'P-18'
     and v.status = 'oficial'
     and v.mes_referencia <= p_ciclo
   order by v.mes_referencia desc, v.criado_em desc
   limit 1;
  return coalesce(v_layout, 'PENDENTE');
end;
$$;

comment on function public.layout_saida(text) is
  'CA-2-28: layout de saída lido do P-18 da versão oficial vigente. Sem resposta da Q-22 devolve PENDENTE.';

-- Consulta de saída: a meta PUBLICADA do ciclo, com campo de perfil.
-- Fonte: meta_linha do ciclo (a publicada é a execução aprovada — a marcação
-- de publicada é da T2.4.2; enquanto não existe, a função devolve vazio).
create or replace function public.extrato_saida(p_ciclo text)
returns table (
  referencia_ciclo text,
  supervisor       text,
  promotor         text,
  cliente          text,
  cliente_nome     text,
  sku              text,
  produto_nome     text,
  linha_produto    text,
  regime           text,
  meta_original    numeric,
  gap_linha        numeric,
  meta_final       numeric
)
language sql
stable
security invoker
set search_path to 'pg_catalog', 'public'
as $$
  select p_ciclo, m.supervisor, m.promotor, m.cliente, m.cliente_nome,
         m.sku, m.produto_nome, m.linha_produto, m.regime,
         m.meta_original, m.gap_linha, m.meta_final
    from public.meta_linha m
   where m.referencia_ciclo = p_ciclo
     -- CA-2-30 (T2.6.3): só a meta publicada entra no extrato. Enquanto o
     -- ciclo não está publicado (T2.4.2), a consulta devolve vazio por construção.
     and exists (select 1 from public.ciclo_meta cm
                 where cm.mes_referencia = p_ciclo and cm.status = 'publicado');
$$;

comment on function public.extrato_saida(text) is
  'CA-2-28/CA-2-30: consulta de saída da meta publicada, com campo de perfil. Vazio se o ciclo não está publicado.';

end;