-- T3.2 / SPEC-1-003 — IS histórico calculado e valor de Out/26 informado.
--
-- Resposta do cliente (30/10): "Índice Sazonal está na aba Metodologia". A aba
-- Metodologia do arquivo Meta_Outubro_2026_Modelo_Final_Consolidado.xlsx traz a
-- REGRA (seção 8: índice mês/ano pela produtividade, mediana dos anos, normalizado
-- para média 1) e NÃO traz a tabela pronta. Aplicada a regra aos dados reais de
-- 2023, 2024 e 2025 (excluindo panettones), outubro dá 1,018840 — e o gabarito
-- P-05 pede 1,031900. Ou seja: o IS de Out/26 é valor INFORMADO, não reproduzível
-- pela regra documentada. Registrado como decisão: outubro usa o parâmetro oficial
-- P-05 (origem 'informado'); os 24 meses históricos usam a regra (origem
-- 'calculado'), porque é ela que o motor precisa para dessazonalizar o passado.

begin;

-- 2023–2025 (três anos completos), sem panettones, pela regra da seção 8
with meses as (
  select generate_series(date '2024-10-01', date '2026-10-01', interval '1 month')::date as mes
), is_mes as (
  select * from (values
    (1, 0.917513::numeric), (2, 0.968952), (3, 0.976779), (4, 1.005115),
    (5, 0.972102), (6, 1.010492), (7, 0.992837), (8, 1.022244),
    (9, 1.044763), (10, 1.018840), (11, 1.084130), (12, 0.986233)
  ) as t(m, valor)
)
update public.calendario_mes cm
   set is_valor   = case when cm.mes = date '2026-10-01' then 1.031900 else im.valor end,
       is_origem  = case when cm.mes = date '2026-10-01' then 'informado' else 'calculado' end,
       pendente_de = case when cm.mes = date '2026-10-01' then 'Q-08' else null end
  from meses, is_mes im
 where cm.mes = meses.mes
   and im.m = extract(month from cm.mes);

commit;
