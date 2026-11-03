-- T1.2 / SPEC-1-001 — Ciclo de meta, operações renomeadas e papéis reais.
--
-- Decisões declaradas (DÚVIDAS de 22/10 para a Kim seguem abertas no changelog;
-- implementado pela leitura provável, reversível por nova versão):
--  D1: mapeamento editar_catalogo→editar_estrutura, criar_configurar_ciclo→criar_ciclo,
--      importar→importar_bases, fechar_snapshot→executar_calculo; gerenciar_papeis
--      PERMANECE (administração de acesso) — matriz fica com 8 operações; homologar sai.
--  D2: papel `aprovador` criado; convive com os papéis existentes; Paulo recebe
--      aprovador além do gestor_dados atual. Léo/Ângelo: operador quando as contas
--      existirem (T1.3).
--  D3: FK direta para parametros_versao (a T3.1 já criou a tabela).

begin;

-- ------------------------------------------------------------------ operações
update public.app_operations set display_name = 'Exportar meta e diagnóstico'
 where operation_key = 'exportar';

insert into public.app_operations (operation_key, display_name, description) values
 ('criar_ciclo',       'Criar ciclo de meta',   'Criar o ciclo de meta de um mês de referência'),
 ('importar_bases',    'Importar bases',        'Importar/carregar bases de vendas, estrutura e produtos'),
 ('editar_estrutura',  'Editar estrutura',      'Editar estrutura comercial, produtos e catálogo'),
 ('editar_parametros', 'Editar parâmetros',     'Criar versões de parâmetros, sortimento e substituição'),
 ('executar_calculo',  'Executar cálculo',      'Executar o cálculo da meta do ciclo'),
 ('aprovar_publicar',  'Aprovar e publicar',    'Aprovar e publicar o ciclo (Fase 2)')
on conflict (operation_key) do nothing;

insert into public.app_roles (role_key, display_name, description) values
 ('aprovador', 'Aprovador', 'Aprova e publica o ciclo (Paulo). Usado a partir da Fase 2.')
on conflict (role_key) do nothing;

-- ------------------------------------------------- políticas apontam para os novos nomes
-- editar_catalogo      -> editar_estrutura   (16 políticas do catálogo)
-- criar_configurar_ciclo -> editar_parametros (parâmetros, sortimento, substituição)
-- Cada política é recriada com o mesmo nome e o mesmo comando, só com a operação nova.
do $$
declare
  r record;
  v_qual  text;
  v_check text;
begin
  for r in
    select schemaname, tablename, policyname, cmd, qual, with_check
    from pg_policies
    where schemaname = 'public'
      and (coalesce(qual,'')       ~ 'editar_catalogo|criar_configurar_ciclo'
        or coalesce(with_check,'') ~ 'editar_catalogo|criar_configurar_ciclo')
  loop
    v_qual  := replace(replace(r.qual,       'editar_catalogo', 'editar_estrutura'), 'criar_configurar_ciclo', 'editar_parametros');
    v_check := replace(replace(r.with_check, 'editar_catalogo', 'editar_estrutura'), 'criar_configurar_ciclo', 'editar_parametros');

    execute format('drop policy %I on %I.%I', r.policyname, r.schemaname, r.tablename);

    if r.cmd = 'SELECT' then
      execute format('create policy %I on %I.%I for select using (%s)',
                     r.policyname, r.schemaname, r.tablename, v_qual);
    elsif r.cmd = 'INSERT' then
      execute format('create policy %I on %I.%I for insert with check (%s)',
                     r.policyname, r.schemaname, r.tablename, v_check);
    elsif r.cmd = 'UPDATE' then
      execute format('create policy %I on %I.%I for update using (%s) with check (%s)',
                     r.policyname, r.schemaname, r.tablename, v_qual, v_check);
    elsif r.cmd = 'DELETE' then
      execute format('create policy %I on %I.%I for delete using (%s)',
                     r.policyname, r.schemaname, r.tablename, v_qual);
    else
      execute format('create policy %I on %I.%I for all using (%s) with check (%s)',
                     r.policyname, r.schemaname, r.tablename, v_qual, v_check);
    end if;
  end loop;
end $$;

-- --------------------------------------------------------------- matriz papel×operação
-- Reconstruída explícita: 7 papéis × 8 operações = 56 decisões, nenhuma implícita.
delete from public.role_operation_matrix
 where operation_key in ('criar_configurar_ciclo','importar','editar_catalogo','fechar_snapshot','homologar');

insert into public.role_operation_matrix (role_key, operation_key, decision, rationale) values
 ('operador','criar_ciclo','allow','SPEC-1-001: operador cria o ciclo do mês'),
 ('operador','importar_bases','allow','SPEC-1-001: operador importa bases'),
 ('operador','editar_estrutura','allow','SPEC-1-001: operador edita estrutura'),
 ('operador','editar_parametros','allow','SPEC-1-001: operador edita parâmetros'),
 ('operador','executar_calculo','allow','SPEC-1-001: operador executa o cálculo'),
 ('operador','exportar','allow','SPEC-1-001: operador exporta'),
 ('operador','aprovar_publicar','deny','Aprovação é do aprovador (Fase 2)'),
 ('operador','gerenciar_papeis','deny','Administração de acesso é do administrador'),
 ('aprovador','aprovar_publicar','allow','SPEC-1-001: Paulo aprova e publica (Fase 2)'),
 ('aprovador','exportar','allow','Aprovador confere a meta exportada'),
 ('aprovador','criar_ciclo','deny','Ciclo é criado pelo operador'),
 ('aprovador','importar_bases','deny','Sem papel de operação'),
 ('aprovador','editar_estrutura','deny','Sem papel de operação'),
 ('aprovador','editar_parametros','deny','Sem papel de operação'),
 ('aprovador','executar_calculo','deny','Execução é do operador'),
 ('aprovador','gerenciar_papeis','deny','Administração de acesso é do administrador'),
 ('gestor_dados','criar_ciclo','allow','Dono dos dados operacionais (transição; revisar na Fase 2)'),
 ('gestor_dados','importar_bases','allow','Dono dos dados operacionais'),
 ('gestor_dados','editar_estrutura','allow','Dono dos dados operacionais'),
 ('gestor_dados','editar_parametros','allow','Dono dos dados operacionais'),
 ('gestor_dados','executar_calculo','allow','Dono dos dados operacionais'),
 ('gestor_dados','exportar','allow','Dono dos dados operacionais'),
 ('gestor_dados','aprovar_publicar','deny','Aprovação é do aprovador'),
 ('gestor_dados','gerenciar_papeis','deny','Administração de acesso é do administrador'),
 ('administrador','gerenciar_papeis','allow','Administração de acesso'),
 ('administrador','criar_ciclo','deny','Sem permissão implícita'),
 ('administrador','importar_bases','deny','Sem permissão implícita'),
 ('administrador','editar_estrutura','deny','Sem permissão implícita'),
 ('administrador','editar_parametros','deny','Sem permissão implícita'),
 ('administrador','executar_calculo','deny','Sem permissão implícita'),
 ('administrador','aprovar_publicar','deny','Sem permissão implícita'),
 ('administrador','exportar','deny','Sem permissão implícita'),
 ('auditor','exportar','allow','Auditoria lê o histórico de autorizações'),
 ('auditor','criar_ciclo','deny','Sem permissão implícita'),
 ('auditor','importar_bases','deny','Sem permissão implícita'),
 ('auditor','editar_estrutura','deny','Sem permissão implícita'),
 ('auditor','editar_parametros','deny','Sem permissão implícita'),
 ('auditor','executar_calculo','deny','Sem permissão implícita'),
 ('auditor','aprovar_publicar','deny','Sem permissão implícita'),
 ('auditor','gerenciar_papeis','deny','Sem permissão implícita'),
 ('consulta','criar_ciclo','deny','Consulta na Fase 2'),
 ('consulta','importar_bases','deny','Consulta na Fase 2'),
 ('consulta','editar_estrutura','deny','Consulta na Fase 2'),
 ('consulta','editar_parametros','deny','Consulta na Fase 2'),
 ('consulta','executar_calculo','deny','Consulta na Fase 2'),
 ('consulta','aprovar_publicar','deny','Consulta na Fase 2'),
 ('consulta','exportar','deny','Consulta na Fase 2'),
 ('consulta','gerenciar_papeis','deny','Sem permissão implícita'),
 ('revisor','criar_ciclo','deny','Sem permissão implícita'),
 ('revisor','importar_bases','deny','Sem permissão implícita'),
 ('revisor','editar_estrutura','deny','Sem permissão implícita'),
 ('revisor','editar_parametros','deny','Sem permissão implícita'),
 ('revisor','executar_calculo','deny','Sem permissão implícita'),
 ('revisor','aprovar_publicar','deny','Sem permissão implícita'),
 ('revisor','exportar','deny','Sem permissão implícita'),
 ('revisor','gerenciar_papeis','deny','Sem permissão implícita')
on conflict (role_key, operation_key) do update
 set decision = excluded.decision, rationale = excluded.rationale, updated_at = now();

-- operações antigas sem sucessor saem (políticas já repontadas acima)
-- operações antigas NÃO são apagadas: authorization_audit_log é append-only e referencia
-- essas chaves (FK). Elas ficam registradas como legado, sem nenhuma linha na matriz —
-- logo, nenhum papel as exerce. Quem lê a auditoria continua conseguindo resolver o nome.
update public.app_operations
   set display_name = display_name || ' (legado)'
 where operation_key in ('criar_configurar_ciclo','importar','editar_catalogo','fechar_snapshot','homologar');

-- Paulo: aprovador além do gestor_dados (conta única existente)
insert into public.profile_role_assignments (profile_id, role_key, assigned_by)
select p.id, 'aprovador', p.id
from public.profiles p
where p.email = 'paulo.ferreira@panutrir.com.br'
  and not exists (select 1 from public.profile_role_assignments a
                  where a.profile_id = p.id and a.role_key = 'aprovador' and a.revoked_at is null);

-- ------------------------------------------------------------------- ciclo de meta
create table if not exists public.ciclo_meta (
  ciclo_id             uuid primary key default gen_random_uuid(),
  mes_referencia       text not null,
  meta_diretoria       numeric(14,2) not null,
  parametros_versao_id uuid not null references public.parametros_versao(versao_id),
  status               text not null default 'rascunho',
  criado_por           uuid,
  criado_em            timestamptz not null default now(),
  atualizado_em        timestamptz not null default now(),
  constraint ciclo_meta_mes_formato check (mes_referencia ~ '^[0-9]{4}-(0[1-9]|1[0-2])$'),
  constraint ciclo_meta_mes_unico unique (mes_referencia),
  constraint ciclo_meta_meta_nao_negativa check (meta_diretoria >= 0),
  constraint ciclo_meta_status_ck check (status in ('rascunho','calculado','aprovado','publicado'))
);
comment on table public.ciclo_meta is
  'T1.2/SPEC-1-001: um ciclo por mês. Criar de novo o mesmo mês devolve o existente. Fase 1 vai até calculado.';

alter table public.ciclo_meta enable row level security;

drop policy if exists ciclo_meta_read on public.ciclo_meta;
create policy ciclo_meta_read on public.ciclo_meta for select to authenticated using (true);
-- escrita só pela RPC (security definer); nenhuma policy de insert/update/delete.

-- RPC de criação idempotente, com auditoria da tentativa (inclusive repetição e negação)
create or replace function public.criar_ciclo_meta(
  p_mes_referencia text,
  p_meta_diretoria numeric,
  p_parametros_versao_id uuid,
  p_correlation_id uuid default gen_random_uuid()
) returns public.ciclo_meta
language plpgsql security definer set search_path to 'pg_catalog', 'public' as $func$
declare
  v_ciclo public.ciclo_meta;
  v_autorizado boolean;
begin
  v_autorizado := public.authorize_operation('criar_ciclo', 'ciclo_meta', p_mes_referencia,
                                             'criar ciclo de meta', p_correlation_id);
  if not v_autorizado then
    raise exception 'Operação negada: criar_ciclo' using errcode = '42501';
  end if;

  if p_mes_referencia !~ '^[0-9]{4}-(0[1-9]|1[0-2])$' then
    raise exception 'Mês de referência inválido: % (use o formato AAAA-MM)', p_mes_referencia
      using errcode = '22023';
  end if;
  if p_meta_diretoria is null or p_meta_diretoria < 0 then
    raise exception 'Meta da Diretoria inválida: deve ser um valor maior ou igual a zero'
      using errcode = '22023';
  end if;
  if not exists (select 1 from public.parametros_versao v where v.versao_id = p_parametros_versao_id) then
    raise exception 'Versão de parâmetros não encontrada' using errcode = '22023';
  end if;

  insert into public.ciclo_meta (mes_referencia, meta_diretoria, parametros_versao_id, status, criado_por)
  values (p_mes_referencia, p_meta_diretoria, p_parametros_versao_id, 'rascunho', auth.uid())
  on conflict (mes_referencia) do nothing
  returning * into v_ciclo;

  if v_ciclo is null then
    select * into v_ciclo from public.ciclo_meta where mes_referencia = p_mes_referencia;
  end if;
  return v_ciclo;
end $func$;

comment on function public.criar_ciclo_meta is
  'T1.2/SPEC-1-001: cria o ciclo do mês (idempotente). Negação e repetição são auditadas por authorize_operation.';

commit;
