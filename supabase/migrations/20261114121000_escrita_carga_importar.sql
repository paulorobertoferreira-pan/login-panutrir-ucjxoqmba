-- F2-T1.3 — escrita da carga pela tela de importação (CA-2-02).
--
-- As tabelas de carga nasceram com política de LEITURA apenas (a carga da Fase 1
-- era feita por script com service role). Com a tela /importar, quem tem a
-- operação `importar_bases` (operador, gestor_dados) precisa INSERIR/DELETAR em
-- venda_mensal e INSERIR/ATUALIZAR em carga_registro — pelo mesmo mecanismo de
-- autorização por papel da matriz 7×8 (private.has_operation), não por service role.
begin;

-- venda_mensal: inserir e apagar (a idempotência por mês apaga antes de gravar)
drop policy if exists venda_mensal_write on public.venda_mensal;
create policy venda_mensal_write on public.venda_mensal
  for insert to authenticated
  with check (private.has_operation('importar_bases'));

drop policy if exists venda_mensal_delete on public.venda_mensal;
create policy venda_mensal_delete on public.venda_mensal
  for delete to authenticated
  using (private.has_operation('importar_bases'));

-- carga_registro: criar o registro, atualizar o fecho e apagar em caso de falha
drop policy if exists carga_registro_write on public.carga_registro;
create policy carga_registro_write on public.carga_registro
  for insert to authenticated
  with check (private.has_operation('importar_bases'));

drop policy if exists carga_registro_update on public.carga_registro;
create policy carga_registro_update on public.carga_registro
  for update to authenticated
  using (private.has_operation('importar_bases'))
  with check (private.has_operation('importar_bases'));

drop policy if exists carga_registro_delete on public.carga_registro;
create policy carga_registro_delete on public.carga_registro
  for delete to authenticated
  using (private.has_operation('importar_bases'));

end;
