-- T1.4 / SPEC-1-001 — Versiona as funções de autorização reais do projeto.
--
-- Lacuna fechada: as migrations da T1.1 (16/09) nunca foram versionadas em repositório
-- (descoberta de 22/10) — `authorize_operation`, `private.has_operation` e
-- `private.append_authorization_audit` só existiam no histórico do banco Supabase.
-- O conteúdo abaixo é a definição REAL recuperada do projeto Supabase
-- (ewwjwewjpbqikknjjozb) em 01/11/2026 — nada foi reinventado.
--
-- Semântica real (e por que a prova é como é):
--   · has_operation: allow se ALGUM papel ativo do auth.uid() tem decision='allow'
--     na role_operation_matrix para a operação.
--   · authorize_operation: operação não cadastrada → 22023; TENTATIVA (allow E deny)
--     é gravada em authorization_audit_log na MESMA transação; devolve true/false.
--   · A negação audita na transação da tentativa: quando a RPC levanta 42501 depois
--     do false, o rollback desfaz o evento — por isso a prova da auditoria de negação
--     chama authorize_operation DIRETAMENTE (retorna false, sem raise) e commita.
--     É o mesmo comportamento do Supabase real.

begin;

-- ------------------------------------------------ private.has_operation (versão real)
create or replace function private.has_operation(p_operation_key text)
 returns boolean
 language sql
 stable security definer
 set search_path to 'pg_catalog', 'public'
as $function$
  SELECT EXISTS (
    SELECT 1
    FROM public.profile_role_assignments AS pra
    JOIN public.role_operation_matrix AS rom
      ON rom.role_key = pra.role_key
     AND rom.operation_key = p_operation_key
    WHERE pra.profile_id = auth.uid()
      AND pra.revoked_at IS NULL
      AND rom.decision = 'allow'
  );
$function$;

-- ------------------------------------ private.append_authorization_audit (versão real)
create or replace function private.append_authorization_audit(
  p_actor_id uuid, p_operation_key text, p_target_type text, p_target_id text,
  p_decision text, p_reason text, p_correlation_id uuid
) returns void
 language plpgsql
 security definer
 set search_path to 'pg_catalog', 'public'
as $function$
BEGIN
  INSERT INTO public.authorization_audit_log (
    actor_id, operation_key, target_type, target_id, decision, reason, correlation_id
  ) VALUES (
    p_actor_id, p_operation_key, p_target_type, p_target_id, p_decision, p_reason,
    COALESCE(p_correlation_id, gen_random_uuid())
  );
END;
$function$;

-- ------------------------------------------------- authorize_operation (versão real)
create or replace function public.authorize_operation(
  p_operation_key text,
  p_target_type   text default null,
  p_target_id     text default null,
  p_reason        text default null,
  p_correlation_id uuid default gen_random_uuid()
) returns boolean
 language plpgsql
 set search_path to 'pg_catalog', 'public'
as $function$
DECLARE
  v_allowed BOOLEAN;
  v_decision TEXT;
  v_reason TEXT;
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM public.app_operations WHERE operation_key = p_operation_key
  ) THEN
    RAISE EXCEPTION 'Operação não cadastrada: %', p_operation_key
      USING ERRCODE = '22023';
  END IF;

  v_allowed := private.has_operation(p_operation_key);
  v_decision := CASE WHEN v_allowed THEN 'allowed' ELSE 'denied' END;
  v_reason := CASE
    WHEN v_allowed THEN p_reason
    ELSE COALESCE(NULLIF(btrim(p_reason), ''), 'Nenhum papel ativo possui permissão allow para a operação.')
  END;

  PERFORM private.append_authorization_audit(
    auth.uid(), p_operation_key, p_target_type, p_target_id,
    v_decision, v_reason, p_correlation_id
  );

  RETURN v_allowed;
END;
$function$;

comment on function public.authorize_operation(text, text, text, text, uuid) is
  'T1.4/SPEC-1-001: versão REAL do Supabase, agora versionada em repositório (a T1.1 não a versionou — descoberta de 22/10). Tentativa (allow e deny) auditada na transação; a negação persiste quando a chamada é direta (sem raise do chamador).';

commit;
