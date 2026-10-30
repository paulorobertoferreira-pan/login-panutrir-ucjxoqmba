-- T3.2 / SPEC-1-003 — Calendário: dias úteis e Índice Sazonal por mês.
--
-- Dias úteis: seg–sex sem feriados (leitura provável da Q-09, confirmada pelos dados:
-- Out/26 = 22 = P-06). IS: a regra documentada (metodologia ago/26, mediana dos índices
-- anuais) dá 1,0045 para Out — NÃO reproduz o gabarito 1,0319 (P-05). Enquanto a Q-08
-- não for respondida, o IS de Out/26 vem do parâmetro oficial P-05 marcado como
-- pendente; os demais meses ficam sem IS (execução sai não reconciliada, protocolo
-- do AGENTS.md).

begin;

create table if not exists public.calendario_mes (
  mes          date primary key check (mes = date_trunc('month', mes)::date),
  dias_uteis   int not null check (dias_uteis between 0 and 31),
  is_valor     numeric(8,6),
  is_origem    text not null default 'pendente'
               check (is_origem in ('calculado','informado','pendente')),
  pendente_de  text,
  criado_em    timestamptz not null default now(),
  constraint calendario_is_pendente_ck
    check ((is_origem = 'pendente') = (pendente_de is not null and is_valor is null))
);
comment on table public.calendario_mes is
  'T3.2/SPEC-1-003: dias úteis e IS por mês. IS pendente da Q-08; Out/26 usa o valor oficial P-05.';

alter table public.calendario_mes enable row level security;
drop policy if exists calendario_read on public.calendario_mes;
create policy calendario_read on public.calendario_mes for select to authenticated using (true);
drop policy if exists calendario_write on public.calendario_mes;
create policy calendario_write on public.calendario_mes for all to authenticated
  using (private.has_operation('editar_parametros'))
  with check (private.has_operation('editar_parametros'));

-- Dias úteis Out/24–Out/26 (seg–sex, sem feriados) + IS de Out/26 pelo parâmetro oficial
insert into public.calendario_mes (mes, dias_uteis, is_valor, is_origem, pendente_de)
select d,
       count(*) filter (where extract(dow from dia) between 1 and 5),
       case when to_char(d,'YYYY-MM') = (select valor_texto from public.parametros_valor
                                          where parametro_codigo = 'P-01')
            then (select valor_numero from public.parametros_valor where parametro_codigo = 'P-05')
       end,
       case when to_char(d,'YYYY-MM') = (select valor_texto from public.parametros_valor
                                          where parametro_codigo = 'P-01')
            then 'informado' else 'pendente' end,
       case when to_char(d,'YYYY-MM') = (select valor_texto from public.parametros_valor
                                          where parametro_codigo = 'P-01')
            then 'Q-08' else 'Q-08' end
from generate_series(date '2024-10-01', date '2026-10-01', interval '1 month') g(d),
     lateral generate_series(d, d + interval '1 month - 1 day', interval '1 day') dias(dia)
group by d
on conflict (mes) do update
  set dias_uteis = excluded.dias_uteis,
      is_valor   = excluded.is_valor,
      is_origem  = excluded.is_origem,
      pendente_de = excluded.pendente_de;

commit;
