-- Carga do cliente 84207 (RAIZER LOJA 3), que ficou fora da T4.2.
--
-- Por que ficou fora: o código 84207 aparece em 3 linhas da estrutura comercial
-- (C01041 RAIZER SUPERMERCADO 3, C04501 T J BARBOSA, C04432 RAIZER SUPERMERCADO 3).
-- A regra do catálogo é 1 linha vigente por cliente (EXCLUDE), então a carga
-- rejeitou as 3 e avisou como pendência de qualidade.
--
-- Decisão, com prova do gabarito do cliente:
--   * O gabarito o trata como UM cliente ("RAIZER LOJA 3"), supervisor
--     CIRO ROLIM MORAES, promotor LEANDRO MORAES PULIDO, meta R$ 897,02.
--   * Das 3 linhas, 2 são a mesma loja (C01041 e C04432, RAIZER SUPERMERCADO 3);
--     só C04501 (T J BARBOSA) é outra loja.
--   * A linha válida é a que TEM estrutura (supervisor 167 / vendedor 183, C01041);
--     as outras duas vêm sem supervisor e sem vendedor.
-- Carrega-se a linha C01041. A C04501 fica registrada em carga_rede_pendente
-- porque é outro estabelecimento usando o mesmo código — decisão de cadastro.

insert into public.catalog_clientes
  (cliente_codigo, cliente_nome, supervisor_codigo, promotor_codigo, vigencia_inicio)
values ('84207', 'RAIZER LOJA 3', '167', null, date '2026-10-01')
on conflict do nothing;

insert into public.carga_rede_pendente (cliente_codigo, motivo)
values ('84207', 'C04501 (T J BARBOSA) e C04432 compartilham o codigo 84207; carregada a linha C01041 (RAIZER LOJA 3) com estrutura. Decisao de cadastro pendente. Promotor do gabarito (LEANDRO MORAES PULIDO) nao existe no catalogo; M-25 impede criar ficticio.')
on conflict (cliente_codigo) do update set motivo = excluded.motivo;
