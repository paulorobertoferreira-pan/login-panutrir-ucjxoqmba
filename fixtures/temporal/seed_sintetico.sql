-- T4.1 — Fixtures temporais sintéticas do catálogo canônico
-- Uso: T4.2 (resolução de chaves) e T4.3 (versionamento/reversão).
-- NÃO é aplicada automaticamente ao Supabase; roda apenas em teste, com rollback.

-- ============ Caso normal: vigência aberta ============
INSERT INTO public.catalog_produtos (produto_codigo, produto_nome, linha_codigo, unidade_medida, ativo, vigencia_inicio, vigencia_fim)
VALUES ('PROD-101', 'Produto Sintético 01', 'LIN-01', 'UN', TRUE, '2026-01-01', NULL)
ON CONFLICT DO NOTHING;

-- ============ Caso normal: vigência encerrada ============
INSERT INTO public.catalog_produtos (produto_codigo, produto_nome, linha_codigo, unidade_medida, ativo, vigencia_inicio, vigencia_fim)
VALUES ('PROD-102', 'Produto Sintético 02', 'LIN-01', 'CX', TRUE, '2026-01-01', '2026-06-30')
ON CONFLICT DO NOTHING;

-- ============ Caso esperado: homônimo NÃO é associado automaticamente ============
-- Mesmo nome, códigos diferentes: ambos entram; a escolha vira pendência (T4.2).
INSERT INTO public.catalog_produtos (produto_codigo, produto_nome, linha_codigo, unidade_medida, ativo, vigencia_inicio, vigencia_fim)
VALUES ('PROD-201', 'Produto Sintético Homônimo', 'LIN-02', 'KG', TRUE, '2026-01-01', NULL)
ON CONFLICT DO NOTHING;

INSERT INTO public.catalog_produtos (produto_codigo, produto_nome, linha_codigo, unidade_medida, ativo, vigencia_inicio, vigencia_fim)
VALUES ('PROD-202', 'Produto Sintético Homônimo', 'LIN-02', 'KG', TRUE, '2026-01-01', NULL)
ON CONFLICT DO NOTHING;

INSERT INTO public.catalog_pendencias_resolucao (tipo, entidade_tipo, entidade_codigo, detalhe, motivo)
VALUES (
  'homonimo',
  'produto',
  'PROD-201',
  'PROD-201 e PROD-202 compartilham o nome "Produto Sintético Homônimo" na mesma vigência.',
  'Nome duplicado entre códigos diferentes; resolução exige decisão humana (T4.2).'
);

-- ============ Caso esperado: lacuna de vigência vira pendência ============
-- SUP-101 cobre REG-01 até 2026-03-31; nenhum responsável cobre REG-01 em abril.
INSERT INTO public.catalog_responsaveis (responsavel_codigo, responsavel_tipo, responsavel_rotulo, vigencia_inicio, vigencia_fim)
VALUES ('SUP-101', 'supervisor', 'Supervisor Sintético 01', '2026-01-01', '2026-03-31')
ON CONFLICT DO NOTHING;

INSERT INTO public.catalog_territorios (territorio_codigo, territorio_nome, vigencia_inicio, vigencia_fim)
VALUES ('REG-01', 'Região Sintética 01', '2026-01-01', NULL)
ON CONFLICT DO NOTHING;

INSERT INTO public.catalog_vinculos (responsavel_codigo, territorio_codigo, vigencia_inicio, vigencia_fim)
VALUES ('SUP-101', 'REG-01', '2026-01-01', '2026-03-31')
ON CONFLICT DO NOTHING;

INSERT INTO public.catalog_pendencias_resolucao (tipo, entidade_tipo, entidade_codigo, detalhe, motivo)
VALUES (
  'lacuna',
  'vinculo',
  'REG-01',
  'REG-01 sem responsável entre 2026-04-01 e 2026-12-31; venda nessa janela não pode ser atribuída.',
  'Lacuna de vigência no vínculo responsável×território; decisão humana necessária (T4.2).'
);

-- ============ Caso esperado: sobreposição é RECUSADA pelo banco ============
-- O INSERT abaixo DEVE falhar com violação de catalog_vinculos_sem_sobreposicao,
-- pois REG-01 já tem SUP-101 até 2026-03-31:
-- INSERT INTO public.catalog_vinculos (responsavel_codigo, territorio_codigo, vigencia_inicio, vigencia_fim)
-- VALUES ('SUP-102', 'REG-01', '2026-02-01', '2026-05-31');
