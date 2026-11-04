-- F2-T2.1 / SPEC-2-002 (CA-2-06) — rascunho de parâmetros é editável.
--
-- A T3.1 deixou o trigger de imutabilidade recusando TODO update em
-- parametros_valor, inclusive em versões rascunho — o que quebra a própria
-- RPC criar_versao_parametros quando p_alteracoes != {} (o clone é criado e
-- o update das alterações falha com restrict_violation). O teste da T3.1 não
-- cobriu esse caminho (só provou criar versão SEM alterações e UPDATE direto
-- na oficial recusado).
--
-- Regra corrigida (mesma do DELETE, já existente): UPDATE é permitido apenas
-- enquanto a versão é 'rascunho'; versão 'oficial' e 'substituida' continuam
-- congeladas (CA-1-07 intacto).
create or replace function private.parametros_valor_imutavel()
returns trigger
language plpgsql
security definer
set search_path to 'pg_catalog', 'public'
as $$
begin
  if tg_op = 'UPDATE' then
    if exists (select 1 from public.parametros_versao v
               where v.versao_id = old.versao_id and v.status <> 'rascunho') then
      raise exception
        'parametros_valor e imutavel: crie uma versao nova (CA-1-07) em vez de alterar a versao %',
        old.versao_id
        using errcode = 'restrict_violation';
    end if;
    return new;
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

comment on function private.parametros_valor_imutavel() is
  'CA-1-07/F2-T2.1: UPDATE só em rascunho; oficial e substituída congeladas. Alterar = nova versão.';