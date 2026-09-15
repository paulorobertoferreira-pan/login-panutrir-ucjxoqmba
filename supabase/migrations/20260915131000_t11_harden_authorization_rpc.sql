-- T1.1 — RPC de autorização sem SECURITY DEFINER exposto
-- A função pública é invoker; somente o append do log usa privilégio elevado
-- e fica no schema privado, fora da superfície RPC pública.

CREATE OR REPLACE FUNCTION private.append_authorization_audit(
  p_actor_id UUID,
  p_operation_key TEXT,
  p_target_type TEXT,
  p_target_id TEXT,
  p_decision TEXT,
  p_reason TEXT,
  p_correlation_id UUID
)
RETURNS VOID
LANGUAGE plpgsql
VOLATILE
SECURITY DEFINER
SET search_path = pg_catalog, public
AS $$
BEGIN
  INSERT INTO public.authorization_audit_log (
    actor_id,
    operation_key,
    target_type,
    target_id,
    decision,
    reason,
    correlation_id
  )
  VALUES (
    p_actor_id,
    p_operation_key,
    p_target_type,
    p_target_id,
    p_decision,
    p_reason,
    COALESCE(p_correlation_id, gen_random_uuid())
  );
END;
$$;

REVOKE ALL ON FUNCTION private.append_authorization_audit(UUID, TEXT, TEXT, TEXT, TEXT, TEXT, UUID)
  FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION private.append_authorization_audit(UUID, TEXT, TEXT, TEXT, TEXT, TEXT, UUID)
  TO authenticated;

CREATE OR REPLACE FUNCTION public.authorize_operation(
  p_operation_key TEXT,
  p_target_type TEXT DEFAULT NULL,
  p_target_id TEXT DEFAULT NULL,
  p_reason TEXT DEFAULT NULL,
  p_correlation_id UUID DEFAULT gen_random_uuid()
)
RETURNS BOOLEAN
LANGUAGE plpgsql
VOLATILE
SECURITY INVOKER
SET search_path = pg_catalog, public
AS $$
DECLARE
  v_allowed BOOLEAN;
  v_decision TEXT;
  v_reason TEXT;
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM public.app_operations
    WHERE operation_key = p_operation_key
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
    auth.uid(),
    p_operation_key,
    p_target_type,
    p_target_id,
    v_decision,
    v_reason,
    p_correlation_id
  );

  RETURN v_allowed;
END;
$$;

REVOKE ALL ON FUNCTION public.authorize_operation(TEXT, TEXT, TEXT, TEXT, UUID)
  FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.authorize_operation(TEXT, TEXT, TEXT, TEXT, UUID)
  TO authenticated;
