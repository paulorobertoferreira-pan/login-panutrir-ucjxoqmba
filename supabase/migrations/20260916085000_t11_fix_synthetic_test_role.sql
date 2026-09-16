-- T1.1 — Corrige o papel da conta sintética usada no teste humano
-- A conta é fixture do ambiente de desenvolvimento, não um usuário real.
-- A associação é feita pelo e-mail da fixture para evitar depender de UUID gerado.

UPDATE public.profiles AS p
SET
  role = 'Gestor de dados',
  updated_at = NOW()
FROM auth.users AS u
WHERE u.id = p.id
  AND lower(u.email) = 'paulo.ferreira@panutrir.com.br';

UPDATE public.profile_role_assignments AS pra
SET revoked_at = COALESCE(pra.revoked_at, NOW())
FROM public.profiles AS p
WHERE pra.profile_id = p.id
  AND lower(p.email) = 'paulo.ferreira@panutrir.com.br'
  AND pra.role_key <> 'gestor_dados'
  AND pra.revoked_at IS NULL;

INSERT INTO public.profile_role_assignments (profile_id, role_key, assigned_by)
SELECT p.id, 'gestor_dados', NULL
FROM public.profiles AS p
WHERE lower(p.email) = 'paulo.ferreira@panutrir.com.br'
ON CONFLICT (profile_id, role_key)
DO UPDATE SET revoked_at = NULL;
