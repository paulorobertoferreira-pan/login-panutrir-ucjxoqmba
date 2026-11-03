-- Correção da estrutura: o código 179 é ANDRE LUIZ ALVES PEREIRA, não DOUGLAS.
--
-- Prova na fonte (estrutura_comercial_atual.xlsx, 3.319 linhas):
--   cod_supervisor 179 aparece em 202 linhas, 201 rotuladas ANDRE LUIZ ALVES PEREIRA
--   e 1 rotulada DOUGLAS SOTTO REZENDE (erro de digitação da origem).
--   O cod_supervisor_s7 (SAP) é 56991 nas duas, então o código 179 é o mesmo
--   responsável — e o rótulo correto é o de 201 dos 202 registros.
--
-- Impacto: a conferência por supervisor contra o gabarito do cliente fechava 15/18
-- antes; com o rótulo errado, DOUGLAS acumulava R$ 1,88M (contra R$ 945 mil do
-- gabarito) e ANDRE aparecia com R$ 0 (contra R$ 930 mil). É rótulo, não valor:
-- nenhuma meta muda, mas a visão por supervisor fica errada e some um gerente.

update public.catalog_responsaveis
   set responsavel_rotulo = 'ANDRE LUIZ ALVES PEREIRA'
 where responsavel_tipo = 'supervisor'
   and responsavel_codigo = '179'
   and responsavel_rotulo <> 'ANDRE LUIZ ALVES PEREIRA';
