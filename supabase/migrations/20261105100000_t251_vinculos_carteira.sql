-- F2-T5.1 / SPEC-2-005 (CA-2-23) — papéis de consulta e vínculo usuário→carteira.
--
-- A consulta da Fase 1 é "authenticated lê tudo". A SPEC-2-005 exige consulta
-- POR PERFIL: supervisor vê a própria equipe, promotor a própria carteira e
-- Diretoria a empresa — e, sem vínculo, NÃO lê NADA (fail-closed, CA-2-23).
--
-- Desenho:
--   · papéis de consulta criados em app_roles: consulta_supervisor,
--     consulta_promotor, consulta_diretoria (a matriz de operações não muda —
--     esses papéis não executam operações, só consultam);
--   · consulta_vinculo: vínculo do usuário com a carteira POR PAPEL. A chave é
--     (profile_id, papel, carteira) — o MESMO código numérico pode existir em
--     papéis diferentes (descoberta da T4.2: códigos repetem entre papéis),
--     então o vínculo é SEMPRE explícito e NUNCA inferido por código;
--   · carteira: para supervisor = código do supervisor; para promotor = código
--     do promotor; para diretoria = 'EMPRESA' (vê tudo);
--   · a RLS por carteira nas tabelas de resultado é a T2.5.3 (leva C) — aqui
--     ficam a tabela de vínculos e a função de leitura do vínculo.

begin;

insert into public.app_roles (role_key, display_name, description) values
 ('consulta_supervisor', 'Consulta — Supervisor', 'Consulta a meta da própria equipe (supervisor)'),
 ('consulta_promotor',   'Consulta — Promotor',   'Consulta a meta da própria carteira (promotor)'),
 ('consulta_diretoria',  'Consulta — Diretoria',  'Consulta a meta da empresa inteira')
on conflict (role_key) do nothing;

create table if not exists public.consulta_vinculo (
  vinculo_id  uuid primary key default gen_random_uuid(),
  profile_id  uuid not null references public.profiles(id) on delete cascade,
  papel       text not null check (papel in ('consulta_supervisor','consulta_promotor','consulta_diretoria')),
  carteira    text not null,
  ciclo_inicio text not null default '0000-01',
  ciclo_fim    text,
  criado_em   timestamptz not null default now(),
  unique (profile_id, papel, carteira, ciclo_inicio),
  constraint consulta_vinculo_ciclos_ck
    check (ciclo_fim is null or ciclo_fim >= ciclo_inicio)
);
comment on table public.consulta_vinculo is
  'CA-2-23: vínculo usuário→carteira POR PAPEL. O mesmo código numérico pode existir em papéis diferentes (T4.2), então o vínculo é explícito e nunca inferido por código. Diretoria usa carteira = ''EMPRESA''.';

alter table public.consulta_vinculo enable row level security;
drop policy if exists consulta_vinculo_read on public.consulta_vinculo;
create policy consulta_vinculo_read on public.consulta_vinculo
  for select to authenticated using (true);
drop policy if exists consulta_vinculo_manage on public.consulta_vinculo;
create policy consulta_vinculo_manage on public.consulta_vinculo
  for all to authenticated
  using (private.has_operation('gerenciar_papeis'))
  with check (private.has_operation('gerenciar_papeis'));

create index if not exists consulta_vinculo_profile_idx
  on public.consulta_vinculo (profile_id, papel) where ciclo_fim is null;

-- Leitura do vínculo do usuário corrente (para as RLS da T2.5.3):
--   · diretoria → 'EMPRESA' (vê tudo);
--   · supervisor/promotor → a(s) carteira(s) vigente(s) no ciclo informado;
--   · sem vínculo → conjunto vazio (fail-closed: não lê nada).
create or replace function public.carteiras_de(p_papel text, p_ciclo text default null)
returns setof text
language sql
stable
security invoker
set search_path to 'pg_catalog', 'public'
as $$
  select v.carteira
    from public.consulta_vinculo v
   where v.profile_id = auth.uid()
     and v.papel = p_papel
     and v.ciclo_inicio <= coalesce(p_ciclo, to_char(now(), 'YYYY-MM'))
     and (v.ciclo_fim is null or v.ciclo_fim >= coalesce(p_ciclo, to_char(now(), 'YYYY-MM')));
$$;

comment on function public.carteiras_de(text, text) is
  'CA-2-23: carteiras do usuário corrente no papel informado. Sem vínculo devolve vazio (fail-closed).';

end;