-- T4.2 — Evolução do catálogo T4.1 para dados reais (EMENDA 02/2026)
--
-- Por quê: as tabelas do catálogo nasceram na era dos dados SINTÉTICOS (SPEC-1-004
-- original, antes da EMENDA 02 liberar dados reais) e suas constraints rejeitam
-- todos os códigos reais da Panutrir:
--   produto_codigo  ~ '^PROD-[0-9]{3}$'   reais: 2, 5, 99161 (até 6 dígitos)
--   linha_codigo    ~ '^LIN-[0-9]{2}$'    reais: 'Branca'/'Especiais'/'Panetones'
--   cliente_codigo  ~ '^CLI-[0-9]{3}$'    reais: 58121, 284, ... (até 6 dígitos)
--   responsavel_codigo ~ '^(SUP|PROM)-[0-9]{3}$'   reais: 325, 22552, ...
--   responsavel_rotulo ~ '^(Supervisor|Promotor) Sintético [0-9]{2}$'  reais: nomes próprios
--   unidade_medida NOT NULL in (UN,KG,CX)      a base de produtos não traz unidade
-- Colunas que a T4.2 exige e não existiam: produtos.ean, produtos.is_panettone (M-03),
-- clientes.canal, clientes.rede, clientes.uf, clientes.supervisor_codigo,
-- clientes.promotor_codigo (M-04/M-25: estrutura atual; promotor pode ser vazio).
--
-- A tabela está vazia (0 linhas), então não há migração de dados — só de formato.
-- RLS, índices e o EXCLUDE de sobreposição por vigência continuam válidos e não mudam.
-- Territórios e vínculos (responsável↔território) não são usados pela estrutura atual
-- (cliente→supervisor direto) e ficam intocados para uso futuro (Fase 4).

-- ============================================================ produtos
alter table public.catalog_produtos drop constraint catalog_produtos_codigo_formato;
alter table public.catalog_produtos drop constraint catalog_produtos_linha_formato;
alter table public.catalog_produtos drop constraint catalog_produtos_unidade;

alter table public.catalog_produtos add constraint catalog_produtos_codigo_formato
  check (produto_codigo ~ '^[0-9]{1,9}$');
alter table public.catalog_produtos add constraint catalog_produtos_linha_formato
  check (linha_codigo in ('Branca', 'Especiais', 'Panetones'));
alter table public.catalog_produtos alter column unidade_medida drop not null;

alter table public.catalog_produtos add column if not exists ean text;
alter table public.catalog_produtos add column if not exists is_panettone boolean not null default false;
alter table public.catalog_produtos add constraint catalog_produtos_ean_formato
  check (ean is null or ean ~ '^[0-9]{8,14}$');
-- M-03: Panettone identificado pela LINHA 'Panetones' ou pela descrição;
-- a flag é derivada na carga e conferida pelo G-11.
create index if not exists catalog_produtos_ean_idx on public.catalog_produtos (ean);

-- ============================================================ clientes
alter table public.catalog_clientes drop constraint catalog_clientes_codigo_formato;

alter table public.catalog_clientes add constraint catalog_clientes_codigo_formato
  check (cliente_codigo ~ '^[0-9]{1,9}$');

alter table public.catalog_clientes add column if not exists canal text;
alter table public.catalog_clientes add column if not exists rede text;
alter table public.catalog_clientes add column if not exists uf text;
alter table public.catalog_clientes add column if not exists supervisor_codigo text;
alter table public.catalog_clientes add column if not exists promotor_codigo text;
-- M-04: estrutura atual vale para todo o histórico (a linha vigente do cliente).
-- M-25: promotor_codigo pode ser null — nunca criar promotor fictício.
alter table public.catalog_clientes add constraint catalog_clientes_canal_formato
  check (canal is null or canal in ('Direto', 'Indireto'));
alter table public.catalog_clientes add constraint catalog_clientes_supervisor_formato
  check (supervisor_codigo is null or supervisor_codigo ~ '^[0-9]{1,9}$');
alter table public.catalog_clientes add constraint catalog_clientes_promotor_formato
  check (promotor_codigo is null or promotor_codigo ~ '^[0-9]{1,9}$');
create index if not exists catalog_clientes_supervisor_idx on public.catalog_clientes (supervisor_codigo);

-- ============================================================ responsáveis
alter table public.catalog_responsaveis drop constraint catalog_responsaveis_codigo_formato;
alter table public.catalog_responsaveis drop constraint catalog_responsaveis_rotulo_sintetico;

alter table public.catalog_responsaveis add constraint catalog_responsaveis_codigo_formato
  check (responsavel_codigo ~ '^[0-9]{1,9}$');
alter table public.catalog_responsaveis add constraint catalog_responsaveis_rotulo_obrigatorio
  check (btrim(responsavel_rotulo) <> '');
