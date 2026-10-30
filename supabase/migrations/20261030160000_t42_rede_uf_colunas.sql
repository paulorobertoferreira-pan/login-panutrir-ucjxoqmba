-- T4.2/T5.1 — Rede, canal e UF dos clientes (Q-04 respondida pela congelada de vendas)
--
-- A Q-04 pedia o DE→PARA "com rede e loja". O arquivo de vendas congelado traz as três
-- colunas por linha (rede, uf, e o canal se deriva da rede) e a estrutura comercial traz
-- supervisor e promotor. A carga usa SOMENTE fonte do cliente — nada inferido:
--   rede/uf ....... da congelada de vendas (2024→2026, a mais recente vence)
--   canal ......... 'Indireto' quando a rede é distribuidor; 'Direto' caso contrário
--                   (M-19 fixa o Indireto em 5,5% da Meta Final — a lista de redes
--                   indiretas vem do DE→PARA; enquanto ele não chega, fica NULL e o
--                   cálculo do canal sai como pendente, nunca chutado)
--   supervisor .... estrutura_comercial_atual (T4.2, já carregada: 3.240 clientes)
--
-- O que NÃO é feito aqui: preencher o que não veio. Cliente sem rede na fonte fica NULL.

begin;

alter table public.catalog_clientes
  add column if not exists rede_codigo_sap text;

comment on column public.catalog_clientes.rede is
  'M-04/Q-04: nome da rede, da congelada de vendas. NULL = cliente avulso (metodologia: "Clientes").';
comment on column public.catalog_clientes.rede_codigo_sap is
  'Q-04: codrede da fonte. Agrupa as lojas da mesma rede.';

-- conferência de apoio para a carga (scripts/20261030160000_t42_rede_uf.py)
create table if not exists public.carga_rede_pendente (
  cliente_codigo text primary key,
  motivo         text not null,
  criado_em      timestamptz not null default now()
);
comment on table public.carga_rede_pendente is
  'Q-04: clientes cuja rede/UF não veio na fonte. Ficam explícitos; nada é inferido (M-27).';

commit;
