-- T3.1 / SPEC-1-003 — Carga da versão Out/26 OFICIAL (P-01..P-16) + sortimento e substituição.
-- Fonte: 06_notas/2026-10-20-metodologia-oficial-out-2026.md (tabela "Parâmetros Out/26").
-- Esta migration retira a restrição "somente SINTETICO" da T2.1b: agora os valores oficiais entram.
--
-- Idempotente: se a versão oficial de 2026-10 já existir, não faz nada.

do $$
declare
  v_versao uuid;
begin
  select versao_id into v_versao
  from public.parametros_versao
  where mes_referencia = '2026-10' and status = 'oficial';

  if v_versao is not null then
    raise notice 'Versao oficial 2026-10 ja existe (%), nada a fazer.', v_versao;
    return;
  end if;

  insert into public.parametros_versao
    (versao_codigo, mes_referencia, status, origem, autor, motivo, congelada_em)
  values
    ('OUT-2026-v1', '2026-10', 'oficial', 'oficial', 'Paulo Ferreira',
     'Carga inicial da metodologia oficial Out/26 (EMENDA 02/2026).', now())
  returning versao_id into v_versao;

  insert into public.parametros_valor
    (versao_id, parametro_codigo, descricao, valor_numero, valor_texto, valor_json, unidade, pendente_de)
  values
    (v_versao, 'P-01', 'Mes de referencia',               null, '2026-10', null, 'YYYY-MM', null),
    (v_versao, 'P-02', 'Meta Diretoria',                  13000000.00, null, null, 'BRL', null),
    (v_versao, 'P-03', 'Janela de elegibilidade',         null, null,
       '{"meses":3,"periodo":"Jul-Set/26","metrica":"venda bruta","condicao":"> 0"}'::jsonb, 'meses', null),
    (v_versao, 'P-04', 'Janela e pesos do motor',         null, null,
       '{"janela_meses":24,"pesos":[{"bloco":"M-1:M-6","peso":0.35},{"bloco":"M-7:M-12","peso":0.30},{"bloco":"M-13:M-24","peso":0.35}]}'::jsonb,
       'peso', null),
    (v_versao, 'P-05', 'Indice Sazonal do mes',           1.0319, null, null, 'indice', 'Q-08'),
    (v_versao, 'P-06', 'Dias uteis do mes',               22, null, null, 'dias', 'Q-09'),
    (v_versao, 'P-07', 'Crescimento esperado G',          0.02591659, null, null, 'fracao', 'Q-10'),
    (v_versao, 'P-08', 'Introducao',                      null, null,
       '{"maturidade_meses":12,"primeiro_mes":1.25,"meses_2_a_12":1.10}'::jsonb, 'fator', null),
    (v_versao, 'P-09', 'Piso tecnico',                    null,
       'media dos meses positivos da janela de 3 meses x (1+G)', null, 'formula', null),
    (v_versao, 'P-10', 'Substituicao',                    null, null,
       '{"sku_origem":"81661","sku_destino":"5","rede":"GRUPO ASSAI","uf":"SP","taxa":0.59}'::jsonb,
       'regra', null),
    (v_versao, 'P-11', 'Sortimento Assai SP',             null, null,
       '{"rede":"GRUPO ASSAI","uf":"SP","skus":["5","6","1224","69251","82051"]}'::jsonb,
       'lista', null),
    (v_versao, 'P-12', 'Share final Indireto',            0.055, null, null, 'fracao', null),
    (v_versao, 'P-13', 'Mix de linha',                    null, null,
       '{"janela_meses":6,"convergencia":0.50,"aplicacao":"somente GAP Direto"}'::jsonb, 'regra', null),
    (v_versao, 'P-14', 'Limiar de baixa relevancia',      300.00, null, null, 'BRL', null),
    (v_versao, 'P-15', 'Exclusao',                        null,
       'PANETTONE (descricao ou categoria contem)', null, 'regra', null),
    -- P-16 fica sem valor de proposito: a Q-20 (onde arredondar o GAP) ainda esta aberta.
    -- Carregar um numero aqui seria inventar regra; a T6.1 preenche numa versao nova.
    (v_versao, 'P-16', 'Tolerancia de reconciliacao',     null, null, null, 'BRL', 'Q-20');

  -- Sortimento Assai SP (P-11 / M-06)
  insert into public.sortimento_restrito (versao_id, rede, uf, sku_codigo)
  select v_versao, 'GRUPO ASSAI', 'SP', s
  from unnest(array['5','6','1224','69251','82051']) as s;

  -- Substituicao PlufiNut -> Pao de Leite (P-10 / M-15)
  insert into public.substituicao (versao_id, rede, uf, sku_origem, sku_destino, taxa)
  values (v_versao, 'GRUPO ASSAI', 'SP', '81661', '5', 0.59);

  raise notice 'Versao oficial OUT-2026-v1 carregada: %', v_versao;
end;
$$;
