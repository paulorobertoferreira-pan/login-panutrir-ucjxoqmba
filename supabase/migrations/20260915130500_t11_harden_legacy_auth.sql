-- T1.1 — Hardening complementar das funções e grants legados
-- A migration inicial criou handle_new_user como SECURITY DEFINER. Ela só deve
-- ser executada pelo trigger de auth, nunca diretamente por anon/authenticated.

ALTER FUNCTION public.handle_new_user()
  SET search_path = pg_catalog, public;

REVOKE ALL ON FUNCTION public.handle_new_user() FROM PUBLIC, anon, authenticated;

-- Perfis continuam legíveis apenas por usuários autenticados segundo a RLS;
-- nenhum cliente recebe mutação direta além do nome próprio, conforme a policy.
REVOKE ALL ON TABLE public.profiles FROM PUBLIC, anon, authenticated;
GRANT SELECT ON TABLE public.profiles TO authenticated;
GRANT UPDATE (name) ON TABLE public.profiles TO authenticated;
