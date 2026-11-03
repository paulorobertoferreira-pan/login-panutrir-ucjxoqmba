-- T3.3 / SPEC-1-003 — Execução versionada e prova de reprodutibilidade.
--
-- Cada cálculo é uma execução dentro do ciclo: guarda versão de parâmetros, versão do
-- motor, cargas usadas e o hash do resultado. Uma execução não é sobrescrita: concluída,
-- congela por trigger. Rodar de novo com os mesmos insumos cria OUTRA execução com o
-- MESMO hash — é essa igualdade que prova a reprodutibilidade (CA-1-09).

begin;

create table if not exists public.execucao_calculo (
  execucao_id          uuid primary key default gen_random_uuid(),
  ciclo_id             uuid not null references public.ciclo_meta(ciclo_id),
  parametros_versao_id uuid not null references public.parametros_versao(versao_id),
  motor_versao         text not null,
  cargas               jsonb not null default '[]'::jsonb,
  iniciado_em          timestamptz not null default now(),
  finalizado_em        timestamptz,
  autor                text not null,
  status               text not null default 'em_andamento',
  contagens            jsonb,
  hash_resultado       text,
  constraint execucao_status_ck
    check (status in ('em_andamento','concluida','falhou')),
  constraint execucao_concluida_tem_hash
    check (status <> 'concluida' or (hash_resultado is not null and finalizado_em is not null))
);
comment on table public.execucao_calculo is
  'T3.3/SPEC-1-003: execução do cálculo. Concluída, congela; repetir cria outra execução com o mesmo hash.';

alter table public.execucao_calculo enable row level security;
drop policy if exists execucao_read on public.execucao_calculo;
create policy execucao_read on public.execucao_calculo for select to authenticated using (true);
drop policy if exists execucao_write on public.execucao_calculo;
create policy execucao_write on public.execucao_calculo for all to authenticated
  using (private.has_operation('executar_calculo'))
  with check (private.has_operation('executar_calculo'));

-- Imutabilidade: concluída, nenhuma coluna muda; em andamento, só status/fim/contagens/hash.
create or replace function public.trg_execucao_imutavel() returns trigger
language plpgsql as $func$
begin
  if old.status = 'concluida' then
    raise exception 'Execução concluída não pode ser alterada; crie uma nova execução'
      using errcode = '55006';
  end if;
  if new.execucao_id <> old.execucao_id
     or new.ciclo_id <> old.ciclo_id
     or new.parametros_versao_id <> old.parametros_versao_id
     or new.motor_versao <> old.motor_versao
     or new.cargas <> old.cargas
     or new.iniciado_em <> old.iniciado_em
     or new.autor <> old.autor then
    raise exception 'Insumos da execução são imutáveis; crie uma nova execução'
      using errcode = '55006';
  end if;
  return new;
end $func$;

drop trigger if exists trg_execucao_imutavel on public.execucao_calculo;
create trigger trg_execucao_imutavel before update on public.execucao_calculo
  for each row execute function public.trg_execucao_imutavel();

-- Hash determinístico dos insumos: mesmos insumos → mesmo hash (a versão do resultado
-- linha a linha é amarrada pelo motor na T5.6, que grava o hash do conjunto de linhas).
create or replace function public.hash_insumos_execucao(p_execucao_id uuid)
returns text language sql stable as $func$
  select md5(
    coalesce(e.motor_versao,'') || '|' ||
    e.parametros_versao_id::text || '|' ||
    (select string_agg(v.parametro_codigo || '=' || coalesce(v.valor_numero::text, v.valor_texto,
        coalesce(v.valor_json::text,'')), ';' order by v.parametro_codigo)
     from public.parametros_valor v where v.versao_id = e.parametros_versao_id) || '|' ||
    coalesce((select string_agg(c::text, ';' order by c) from jsonb_array_elements_text(e.cargas) c), '')
  )
  from public.execucao_calculo e where e.execucao_id = p_execucao_id
$func$;

comment on function public.hash_insumos_execucao is
  'T3.3/SPEC-1-003: hash determinístico dos insumos da execução. Igual em execuções repetidas.';

commit;
