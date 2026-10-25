-- T3.1 / SPEC-1-003 — Parâmetros versionados, sortimento e substituição como tabelas.
-- Nenhum número da metodologia fica escrito no motor: tudo vem daqui, amarrado a uma versão.
--
-- Regra central (CA-1-07): versão não se edita. Os valores são imutáveis; "alterar" um
-- parâmetro é criar uma versão nova a partir da anterior. A imutabilidade é garantida por
-- trigger, não por convenção: um UPDATE em parametros_valor é recusado pelo banco.

-- ---------------------------------------------------------------- versão (cabeçalho)
create table if not exists public.parametros_versao (
  versao_id        uuid primary key default gen_random_uuid(),
  versao_codigo    text not null unique,
  mes_referencia   text not null,
  status           text not null default 'rascunho',
  origem           text not null default 'oficial',
  autor            text not null,
  motivo           text,
  versao_anterior  uuid references public.parametros_versao(versao_id),
  criado_em        timestamptz not null default now(),
  congelada_em     timestamptz,
  constraint parametros_versao_mes_ck
    check (mes_referencia ~ '^[0-9]{4}-(0[1-9]|1[0-2])$'),
  constraint parametros_versao_status_ck
    check (status in ('rascunho', 'oficial', 'substituida')),
  constraint parametros_versao_origem_ck
    check (origem in ('oficial', 'sintetico')),
  -- uma versão oficial por mês: duas "oficiais" para Out/26 tornariam o cálculo ambíguo
  constraint parametros_versao_oficial_unica
    exclude using btree (mes_referencia with =) where (status = 'oficial')
);

comment on table public.parametros_versao is
  'T3.1/SPEC-1-003: versão do conjunto de parâmetros. Não se edita — criar versão nova.';
comment on constraint parametros_versao_oficial_unica on public.parametros_versao is
  'Um mês tem no máximo uma versão oficial; as demais ficam rascunho ou substituida.';

-- ------------------------------------------------------------------ valores (P-01..P-16)
create table if not exists public.parametros_valor (
  valor_id        uuid primary key default gen_random_uuid(),
  versao_id       uuid not null references public.parametros_versao(versao_id) on delete restrict,
  parametro_codigo text not null,
  descricao       text not null,
  valor_numero    numeric,
  valor_texto     text,
  valor_json      jsonb,
  unidade         text,
  pendente_de     text,
  criado_em       timestamptz not null default now(),
  constraint parametros_valor_codigo_ck
    check (parametro_codigo ~ '^P-([0-9]{2})$'),
  constraint parametros_valor_unico unique (versao_id, parametro_codigo),
  -- cada parâmetro carrega exatamente uma representação de valor, ou nenhuma (pendente de Q-x)
  constraint parametros_valor_uma_representacao
    check (num_nonnulls(valor_numero, valor_texto, valor_json) <= 1)
);

comment on table public.parametros_valor is
  'T3.1/SPEC-1-003: P-01..P-16 por versão. Imutável: alterar exige versão nova.';
comment on column public.parametros_valor.pendente_de is
  'Pergunta aberta que ainda define este parâmetro (ex.: P-16 pendente da Q-20). Valor nulo é esperado.';

-- ------------------------------------------------- sortimento restrito (M-06 / P-11)
create table if not exists public.sortimento_restrito (
  sortimento_id   uuid primary key default gen_random_uuid(),
  versao_id       uuid not null references public.parametros_versao(versao_id) on delete restrict,
  rede            text not null,
  uf              text not null,
  sku_codigo      text not null,
  criado_em       timestamptz not null default now(),
  constraint sortimento_uf_ck check (uf ~ '^[A-Z]{2}$'),
  constraint sortimento_unico unique (versao_id, rede, uf, sku_codigo)
);

comment on table public.sortimento_restrito is
  'T3.1/SPEC-1-003: sortimento vigente por rede. Linha de tabela, nunca if no código.';

-- --------------------------------------------------------- substituição (M-15 / P-10)
create table if not exists public.substituicao (
  substituicao_id uuid primary key default gen_random_uuid(),
  versao_id       uuid not null references public.parametros_versao(versao_id) on delete restrict,
  rede            text not null,
  uf              text not null,
  sku_origem      text not null,
  sku_destino     text not null,
  taxa            numeric not null,
  criado_em       timestamptz not null default now(),
  constraint substituicao_uf_ck check (uf ~ '^[A-Z]{2}$'),
  constraint substituicao_taxa_ck check (taxa > 0 and taxa <= 1),
  constraint substituicao_skus_diferentes check (sku_origem <> sku_destino),
  constraint substituicao_unico unique (versao_id, rede, uf, sku_origem, sku_destino)
);

comment on table public.substituicao is
  'T3.1/SPEC-1-003: transferência de meta entre SKUs por rede. Escopo Out/26: Assaí SP.';

-- ------------------------------------------------------------------- imutabilidade
create or replace function private.parametros_valor_imutavel()
returns trigger
language plpgsql
security definer
set search_path to 'pg_catalog', 'public'
as $$
begin
  if tg_op = 'UPDATE' then
    raise exception
      'parametros_valor e imutavel: crie uma versao nova (CA-1-07) em vez de alterar a versao %',
      old.versao_id
      using errcode = 'restrict_violation';
  end if;
  -- DELETE: só permitido enquanto a versão é rascunho (descartar versão em construção)
  if exists (select 1 from public.parametros_versao v
             where v.versao_id = old.versao_id and v.status <> 'rascunho') then
    raise exception
      'parametros_valor de versao oficial nao pode ser apagado (versao %)', old.versao_id
      using errcode = 'restrict_violation';
  end if;
  return old;
end;
$$;

drop trigger if exists trg_parametros_valor_imutavel on public.parametros_valor;
create trigger trg_parametros_valor_imutavel
  before update or delete on public.parametros_valor
  for each row execute function private.parametros_valor_imutavel();

comment on function private.parametros_valor_imutavel() is
  'CA-1-07: recusa UPDATE em valores de parâmetro. Alterar = nova versão.';

-- versão oficial não muda de valores: só status/congelada_em podem mudar
create or replace function private.parametros_versao_protege_mes()
returns trigger
language plpgsql
security definer
set search_path to 'pg_catalog', 'public'
as $$
begin
  if new.mes_referencia <> old.mes_referencia
     or new.versao_codigo <> old.versao_codigo
     or new.origem <> old.origem then
    raise exception 'identidade da versao nao pode ser alterada (versao %)', old.versao_codigo
      using errcode = 'restrict_violation';
  end if;
  return new;
end;
$$;

drop trigger if exists trg_parametros_versao_protege on public.parametros_versao;
create trigger trg_parametros_versao_protege
  before update on public.parametros_versao
  for each row execute function private.parametros_versao_protege_mes();

-- ------------------------------------------------------------ nova versão a partir de uma
-- "Alterar um valor gera nova versão (autor, data, motivo)": a única forma de mudar um número.
create or replace function public.criar_versao_parametros(
  p_versao_origem uuid,
  p_novo_codigo   text,
  p_autor         text,
  p_motivo        text,
  p_alteracoes    jsonb default '{}'::jsonb
) returns uuid
language plpgsql
security invoker
set search_path to 'pg_catalog', 'public'
as $$
declare
  v_origem   public.parametros_versao;
  v_novo_id  uuid;
  v_chave    text;
  v_valor    jsonb;
begin
  if coalesce(btrim(p_autor), '') = '' then
    raise exception 'autor da versao e obrigatorio' using errcode = 'check_violation';
  end if;
  if coalesce(btrim(p_motivo), '') = '' then
    raise exception 'motivo da nova versao e obrigatorio' using errcode = 'check_violation';
  end if;

  select * into v_origem from public.parametros_versao where versao_id = p_versao_origem;
  if not found then
    raise exception 'versao de origem inexistente: %', p_versao_origem using errcode = 'no_data_found';
  end if;

  insert into public.parametros_versao
    (versao_codigo, mes_referencia, status, origem, autor, motivo, versao_anterior)
  values
    (p_novo_codigo, v_origem.mes_referencia, 'rascunho', v_origem.origem, p_autor, p_motivo,
     v_origem.versao_id)
  returning versao_id into v_novo_id;

  -- clona todos os parâmetros
  insert into public.parametros_valor
    (versao_id, parametro_codigo, descricao, valor_numero, valor_texto, valor_json, unidade, pendente_de)
  select v_novo_id, parametro_codigo, descricao, valor_numero, valor_texto, valor_json, unidade, pendente_de
  from public.parametros_valor
  where versao_id = p_versao_origem;

  -- aplica as alterações pedidas
  for v_chave, v_valor in select key, value from jsonb_each(coalesce(p_alteracoes, '{}'::jsonb)) loop
    if not exists (select 1 from public.parametros_valor
                   where versao_id = v_novo_id and parametro_codigo = v_chave) then
      raise exception 'parametro % nao existe na versao de origem', v_chave
        using errcode = 'check_violation';
    end if;

    update public.parametros_valor
       set valor_numero = case when jsonb_typeof(v_valor) = 'number'
                               then (v_valor #>> '{}')::numeric end,
           valor_texto  = case when jsonb_typeof(v_valor) = 'string'
                               then v_valor #>> '{}' end,
           valor_json   = case when jsonb_typeof(v_valor) in ('object', 'array')
                               then v_valor end
     where versao_id = v_novo_id and parametro_codigo = v_chave;
  end loop;

  -- o sortimento e a substituição também são versionados: copiar para a nova versão
  insert into public.sortimento_restrito (versao_id, rede, uf, sku_codigo)
  select v_novo_id, rede, uf, sku_codigo from public.sortimento_restrito
  where versao_id = p_versao_origem;

  insert into public.substituicao (versao_id, rede, uf, sku_origem, sku_destino, taxa)
  select v_novo_id, rede, uf, sku_origem, sku_destino, taxa from public.substituicao
  where versao_id = p_versao_origem;

  return v_novo_id;
end;
$$;

comment on function public.criar_versao_parametros(uuid, text, text, text, jsonb) is
  'CA-1-07: cria versao nova a partir da anterior aplicando alteracoes; preserva a anterior intacta.';

-- ------------------------------------------------------------------------------- RLS
alter table public.parametros_versao    enable row level security;
alter table public.parametros_valor     enable row level security;
alter table public.sortimento_restrito  enable row level security;
alter table public.substituicao         enable row level security;

-- Leitura: quem está autenticado lê parâmetros (não são dado pessoal nem segredo).
drop policy if exists parametros_versao_read on public.parametros_versao;
create policy parametros_versao_read on public.parametros_versao
  for select to authenticated using (true);

drop policy if exists parametros_valor_read on public.parametros_valor;
create policy parametros_valor_read on public.parametros_valor
  for select to authenticated using (true);

drop policy if exists sortimento_read on public.sortimento_restrito;
create policy sortimento_read on public.sortimento_restrito
  for select to authenticated using (true);

drop policy if exists substituicao_read on public.substituicao;
create policy substituicao_read on public.substituicao
  for select to authenticated using (true);

-- Escrita: operação existente da matriz da T1.1.
-- TODO(T3.1 -> T1.2): trocar por 'editar_parametros' quando a T1.2 renomear as operações.
-- Usa 'criar_configurar_ciclo' (allow para administrador/operador) porque é a operação de
-- configuração hoje existente; inventar 'editar_parametros' aqui anteciparia a decisão da T1.2.
drop policy if exists parametros_versao_write on public.parametros_versao;
create policy parametros_versao_write on public.parametros_versao
  for all to authenticated
  using (private.has_operation('criar_configurar_ciclo'))
  with check (private.has_operation('criar_configurar_ciclo'));

drop policy if exists parametros_valor_write on public.parametros_valor;
create policy parametros_valor_write on public.parametros_valor
  for all to authenticated
  using (private.has_operation('criar_configurar_ciclo'))
  with check (private.has_operation('criar_configurar_ciclo'));

drop policy if exists sortimento_write on public.sortimento_restrito;
create policy sortimento_write on public.sortimento_restrito
  for all to authenticated
  using (private.has_operation('criar_configurar_ciclo'))
  with check (private.has_operation('criar_configurar_ciclo'));

drop policy if exists substituicao_write on public.substituicao;
create policy substituicao_write on public.substituicao
  for all to authenticated
  using (private.has_operation('criar_configurar_ciclo'))
  with check (private.has_operation('criar_configurar_ciclo'));

-- ---------------------------------------------------------------------------- índices
create index if not exists ix_parametros_valor_versao on public.parametros_valor (versao_id, parametro_codigo);
create index if not exists ix_parametros_versao_mes   on public.parametros_versao (mes_referencia, status);
create index if not exists ix_sortimento_versao_rede  on public.sortimento_restrito (versao_id, rede, uf);
create index if not exists ix_substituicao_versao_rede on public.substituicao (versao_id, rede, uf);
