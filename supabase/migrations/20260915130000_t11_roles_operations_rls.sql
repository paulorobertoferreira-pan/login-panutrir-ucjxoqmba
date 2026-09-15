-- T1.1 — Perfis, matriz papel×operação e autorização RLS
-- SPEC-1-001 / CA-1-01
-- Somente fixtures sintéticas na Fase 1. A autorização usa a tabela de
-- atribuições e a matriz explícita; o texto legado de profiles.role não concede acesso.

CREATE SCHEMA IF NOT EXISTS private;

REVOKE ALL ON SCHEMA private FROM PUBLIC;
GRANT USAGE ON SCHEMA private TO authenticated;

CREATE TABLE IF NOT EXISTS public.app_roles (
  role_key TEXT PRIMARY KEY,
  display_name TEXT NOT NULL,
  description TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT app_roles_key_format CHECK (role_key ~ '^[a-z][a-z0-9_]*$')
);

CREATE TABLE IF NOT EXISTS public.app_operations (
  operation_key TEXT PRIMARY KEY,
  display_name TEXT NOT NULL,
  description TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT app_operations_key_format CHECK (operation_key ~ '^[a-z][a-z0-9_]*$')
);

CREATE TABLE IF NOT EXISTS public.role_operation_matrix (
  role_key TEXT NOT NULL REFERENCES public.app_roles(role_key) ON DELETE CASCADE,
  operation_key TEXT NOT NULL REFERENCES public.app_operations(operation_key) ON DELETE CASCADE,
  decision TEXT NOT NULL,
  rationale TEXT NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (role_key, operation_key),
  CONSTRAINT role_operation_matrix_decision CHECK (decision IN ('allow', 'deny')),
  CONSTRAINT role_operation_matrix_rationale CHECK (btrim(rationale) <> '')
);

CREATE TABLE IF NOT EXISTS public.profile_role_assignments (
  profile_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
  role_key TEXT NOT NULL REFERENCES public.app_roles(role_key) ON DELETE RESTRICT,
  assigned_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
  assigned_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  revoked_at TIMESTAMPTZ,
  PRIMARY KEY (profile_id, role_key),
  CONSTRAINT profile_role_assignments_dates CHECK (revoked_at IS NULL OR revoked_at >= assigned_at)
);

CREATE INDEX IF NOT EXISTS profile_role_assignments_active_idx
  ON public.profile_role_assignments (profile_id, role_key)
  WHERE revoked_at IS NULL;

CREATE TABLE IF NOT EXISTS public.authorization_audit_log (
  event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  actor_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
  operation_key TEXT NOT NULL REFERENCES public.app_operations(operation_key) ON DELETE RESTRICT,
  target_type TEXT,
  target_id TEXT,
  decision TEXT NOT NULL,
  reason TEXT,
  correlation_id UUID NOT NULL DEFAULT gen_random_uuid(),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT authorization_audit_decision CHECK (decision IN ('allowed', 'denied')),
  CONSTRAINT authorization_audit_denial_reason CHECK (
    decision = 'allowed' OR NULLIF(btrim(reason), '') IS NOT NULL
  )
);

CREATE INDEX IF NOT EXISTS authorization_audit_actor_created_idx
  ON public.authorization_audit_log (actor_id, created_at DESC);

CREATE INDEX IF NOT EXISTS authorization_audit_operation_created_idx
  ON public.authorization_audit_log (operation_key, created_at DESC);

COMMENT ON COLUMN public.profiles.role IS
  'Campo legado de exibição; autorização efetiva vem de profile_role_assignments e role_operation_matrix.';

INSERT INTO public.app_roles (role_key, display_name, description)
VALUES
  ('administrador', 'Administrador', 'Configura papéis e a matriz de autorização.'),
  ('operador', 'Operador', 'Cria/configura ciclos e importa dados.'),
  ('revisor', 'Revisor', 'Homologa itens em quarentena.'),
  ('gestor_dados', 'Gestor de dados', 'Edita catálogo e fecha snapshots.'),
  ('auditor', 'Auditor', 'Exporta diagnóstico e evidências auditáveis.'),
  ('consulta', 'Consulta', 'Somente lê os recursos que lhe forem expostos.')
ON CONFLICT (role_key) DO NOTHING;

INSERT INTO public.app_operations (operation_key, display_name, description)
VALUES
  ('criar_configurar_ciclo', 'Criar/configurar ciclo', 'Abrir ou configurar um ciclo em preparação.'),
  ('importar', 'Importar dados', 'Importar fixtures e bases homologadas para staging.'),
  ('homologar', 'Homologar quarentena', 'Homologar ou devolver pendências de qualidade.'),
  ('editar_catalogo', 'Editar catálogo', 'Editar entidades e vigências do catálogo canônico.'),
  ('fechar_snapshot', 'Fechar snapshot', 'Congelar o snapshot versionado do ciclo.'),
  ('exportar', 'Exportar diagnóstico', 'Exportar diagnóstico, memória de cálculo e evidências.'),
  ('gerenciar_papeis', 'Gerenciar papéis', 'Configurar atribuições e decisões da matriz.')
ON CONFLICT (operation_key) DO NOTHING;

-- Cada combinação papel×operação recebe uma decisão persistida.
-- Ausência de uma linha não concede permissão: a matriz é preenchida explicitamente.
WITH allowed(role_key, operation_key) AS (
  VALUES
    ('administrador', 'criar_configurar_ciclo'),
    ('administrador', 'importar'),
    ('administrador', 'homologar'),
    ('administrador', 'editar_catalogo'),
    ('administrador', 'fechar_snapshot'),
    ('administrador', 'exportar'),
    ('administrador', 'gerenciar_papeis'),
    ('operador', 'criar_configurar_ciclo'),
    ('operador', 'importar'),
    ('revisor', 'homologar'),
    ('gestor_dados', 'editar_catalogo'),
    ('gestor_dados', 'fechar_snapshot'),
    ('auditor', 'exportar')
)
INSERT INTO public.role_operation_matrix (role_key, operation_key, decision, rationale)
SELECT
  r.role_key,
  o.operation_key,
  CASE WHEN a.role_key IS NULL THEN 'deny' ELSE 'allow' END AS decision,
  CASE
    WHEN a.role_key IS NULL THEN 'Negado por menor privilégio; sem concessão implícita.'
    ELSE 'Concedido pela matriz mínima da SPEC-1-001.'
  END AS rationale
FROM public.app_roles AS r
CROSS JOIN public.app_operations AS o
LEFT JOIN allowed AS a
  ON a.role_key = r.role_key
 AND a.operation_key = o.operation_key
ON CONFLICT (role_key, operation_key) DO NOTHING;

-- A conta sintética existente da migration inicial é associada de forma explícita
-- ao papel de gestor de dados. Nenhuma permissão é inferida do texto legado.
INSERT INTO public.profile_role_assignments (profile_id, role_key, assigned_by)
SELECT p.id, 'gestor_dados', NULL
FROM public.profiles AS p
WHERE lower(btrim(p.role)) IN ('gestor de metas', 'gestor de dados', 'gestor_dados')
  AND NOT EXISTS (
    SELECT 1
    FROM public.profile_role_assignments AS pra
    WHERE pra.profile_id = p.id
      AND pra.revoked_at IS NULL
  )
ON CONFLICT (profile_id, role_key) DO NOTHING;

-- Perfis sintéticos sem mapeamento conhecido começam em consulta: deny-by-default.
INSERT INTO public.profile_role_assignments (profile_id, role_key, assigned_by)
SELECT p.id, 'consulta', NULL
FROM public.profiles AS p
WHERE NOT EXISTS (
  SELECT 1
  FROM public.profile_role_assignments AS pra
  WHERE pra.profile_id = p.id
    AND pra.revoked_at IS NULL
)
ON CONFLICT (profile_id, role_key) DO NOTHING;

CREATE OR REPLACE FUNCTION private.has_role(p_role_key TEXT)
RETURNS BOOLEAN
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = pg_catalog, public
AS $$
  SELECT EXISTS (
    SELECT 1
    FROM public.profile_role_assignments AS pra
    WHERE pra.profile_id = auth.uid()
      AND pra.role_key = p_role_key
      AND pra.revoked_at IS NULL
  );
$$;

CREATE OR REPLACE FUNCTION private.has_operation(p_operation_key TEXT)
RETURNS BOOLEAN
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = pg_catalog, public
AS $$
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
$$;

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
SECURITY DEFINER
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
    auth.uid(),
    p_operation_key,
    p_target_type,
    p_target_id,
    v_decision,
    v_reason,
    COALESCE(p_correlation_id, gen_random_uuid())
  );

  RETURN v_allowed;
END;
$$;

CREATE OR REPLACE FUNCTION private.prevent_authorization_audit_mutation()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public
AS $$
BEGIN
  RAISE EXCEPTION 'authorization_audit_log é append-only'
    USING ERRCODE = '42501';
END;
$$;

DROP TRIGGER IF EXISTS authorization_audit_append_only ON public.authorization_audit_log;
CREATE TRIGGER authorization_audit_append_only
  BEFORE UPDATE OR DELETE ON public.authorization_audit_log
  FOR EACH ROW EXECUTE FUNCTION private.prevent_authorization_audit_mutation();

-- Substitui a leitura ampla e impede elevação por edição do próprio papel.
DROP POLICY IF EXISTS profiles_select_authenticated ON public.profiles;
DROP POLICY IF EXISTS profiles_update_own ON public.profiles;
DROP POLICY IF EXISTS profiles_insert_own ON public.profiles;

CREATE POLICY profiles_select_self_or_admin
  ON public.profiles
  FOR SELECT TO authenticated
  USING (id = auth.uid() OR private.has_operation('gerenciar_papeis'));

CREATE POLICY profiles_update_name
  ON public.profiles
  FOR UPDATE TO authenticated
  USING (id = auth.uid() OR private.has_operation('gerenciar_papeis'))
  WITH CHECK (id = auth.uid() OR private.has_operation('gerenciar_papeis'));

ALTER TABLE public.app_roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.app_operations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.role_operation_matrix ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.profile_role_assignments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.authorization_audit_log ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS app_roles_authenticated_read ON public.app_roles;
CREATE POLICY app_roles_authenticated_read
  ON public.app_roles
  FOR SELECT TO authenticated
  USING (true);

DROP POLICY IF EXISTS app_operations_authenticated_read ON public.app_operations;
CREATE POLICY app_operations_authenticated_read
  ON public.app_operations
  FOR SELECT TO authenticated
  USING (true);

DROP POLICY IF EXISTS role_operation_matrix_authenticated_read ON public.role_operation_matrix;
CREATE POLICY role_operation_matrix_authenticated_read
  ON public.role_operation_matrix
  FOR SELECT TO authenticated
  USING (true);

DROP POLICY IF EXISTS role_operation_matrix_admin_insert ON public.role_operation_matrix;
CREATE POLICY role_operation_matrix_admin_insert
  ON public.role_operation_matrix
  FOR INSERT TO authenticated
  WITH CHECK (private.has_operation('gerenciar_papeis'));

DROP POLICY IF EXISTS role_operation_matrix_admin_update ON public.role_operation_matrix;
CREATE POLICY role_operation_matrix_admin_update
  ON public.role_operation_matrix
  FOR UPDATE TO authenticated
  USING (private.has_operation('gerenciar_papeis'))
  WITH CHECK (private.has_operation('gerenciar_papeis'));

DROP POLICY IF EXISTS role_operation_matrix_admin_delete ON public.role_operation_matrix;
CREATE POLICY role_operation_matrix_admin_delete
  ON public.role_operation_matrix
  FOR DELETE TO authenticated
  USING (private.has_operation('gerenciar_papeis'));

DROP POLICY IF EXISTS profile_role_assignments_self_or_admin_read ON public.profile_role_assignments;
CREATE POLICY profile_role_assignments_self_or_admin_read
  ON public.profile_role_assignments
  FOR SELECT TO authenticated
  USING (profile_id = auth.uid() OR private.has_operation('gerenciar_papeis'));

DROP POLICY IF EXISTS profile_role_assignments_admin_insert ON public.profile_role_assignments;
CREATE POLICY profile_role_assignments_admin_insert
  ON public.profile_role_assignments
  FOR INSERT TO authenticated
  WITH CHECK (
    private.has_operation('gerenciar_papeis')
    AND assigned_by = auth.uid()
  );

DROP POLICY IF EXISTS profile_role_assignments_admin_update ON public.profile_role_assignments;
CREATE POLICY profile_role_assignments_admin_update
  ON public.profile_role_assignments
  FOR UPDATE TO authenticated
  USING (private.has_operation('gerenciar_papeis'))
  WITH CHECK (
    private.has_operation('gerenciar_papeis')
    AND assigned_by = auth.uid()
  );

DROP POLICY IF EXISTS profile_role_assignments_admin_delete ON public.profile_role_assignments;
CREATE POLICY profile_role_assignments_admin_delete
  ON public.profile_role_assignments
  FOR DELETE TO authenticated
  USING (private.has_operation('gerenciar_papeis'));

DROP POLICY IF EXISTS authorization_audit_admin_or_auditor_read ON public.authorization_audit_log;
CREATE POLICY authorization_audit_admin_or_auditor_read
  ON public.authorization_audit_log
  FOR SELECT TO authenticated
  USING (
    private.has_operation('gerenciar_papeis')
    OR private.has_operation('exportar')
  );

-- Sem política de INSERT/UPDATE/DELETE para clientes: o log só é escrito pela
-- função SECURITY DEFINER e alterações são bloqueadas pelo trigger append-only.

REVOKE ALL ON TABLE public.app_roles FROM PUBLIC, anon, authenticated;
REVOKE ALL ON TABLE public.app_operations FROM PUBLIC, anon, authenticated;
REVOKE ALL ON TABLE public.role_operation_matrix FROM PUBLIC, anon, authenticated;
REVOKE ALL ON TABLE public.profile_role_assignments FROM PUBLIC, anon, authenticated;
REVOKE ALL ON TABLE public.authorization_audit_log FROM PUBLIC, anon, authenticated;

GRANT SELECT ON TABLE public.app_roles, public.app_operations TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.role_operation_matrix TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.profile_role_assignments TO authenticated;
GRANT SELECT ON TABLE public.authorization_audit_log TO authenticated;

REVOKE INSERT, UPDATE, DELETE ON TABLE public.profiles FROM PUBLIC, anon, authenticated;
GRANT SELECT ON TABLE public.profiles TO authenticated;
GRANT UPDATE (name) ON TABLE public.profiles TO authenticated;

REVOKE ALL ON FUNCTION private.has_role(TEXT) FROM PUBLIC, anon, authenticated;
REVOKE ALL ON FUNCTION private.has_operation(TEXT) FROM PUBLIC, anon, authenticated;
REVOKE ALL ON FUNCTION public.authorize_operation(TEXT, TEXT, TEXT, TEXT, UUID) FROM PUBLIC, anon, authenticated;
REVOKE ALL ON FUNCTION private.prevent_authorization_audit_mutation() FROM PUBLIC, anon, authenticated;

GRANT EXECUTE ON FUNCTION private.has_role(TEXT) TO authenticated;
GRANT EXECUTE ON FUNCTION private.has_operation(TEXT) TO authenticated;
GRANT EXECUTE ON FUNCTION public.authorize_operation(TEXT, TEXT, TEXT, TEXT, UUID) TO authenticated;

ALTER FUNCTION public.handle_new_user() SET search_path = public;
