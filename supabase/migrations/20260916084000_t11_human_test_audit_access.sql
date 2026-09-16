-- T1.1 — Leitura restrita dos próprios testes humanos de autorização
-- Permite que o usuário veja apenas os registros que ele mesmo gerou
-- pela tela de teste, sem abrir a auditoria completa para perfis comuns.

DROP POLICY IF EXISTS authorization_audit_actor_test_read ON public.authorization_audit_log;
CREATE POLICY authorization_audit_actor_test_read
  ON public.authorization_audit_log
  FOR SELECT TO authenticated
  USING (
    (actor_id = auth.uid() AND target_type = 'human_test')
    OR private.has_operation('gerenciar_papeis')
    OR private.has_operation('exportar')
  );
