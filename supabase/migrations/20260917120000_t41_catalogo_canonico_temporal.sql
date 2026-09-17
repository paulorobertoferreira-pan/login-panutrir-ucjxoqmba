-- T4.1 — Catálogo canônico temporal (SPEC-1-004 / CA-1-04)
-- Entidades canônicas com vigência por data da venda; sobreposição de vigência
-- da mesma entidade é recusada pelo banco; ambiguidade/lacuna viram pendência.
-- Somente fixtures sintéticas na Fase 1; dados reais bloqueados até o Gate G1.

CREATE EXTENSION IF NOT EXISTS btree_gist;

-- ============ Produtos canônicos ============
CREATE TABLE IF NOT EXISTS public.catalog_produtos (
  produto_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  produto_codigo TEXT NOT NULL,
  produto_nome TEXT NOT NULL,
  linha_codigo TEXT NOT NULL,
  unidade_medida TEXT NOT NULL,
  ativo BOOLEAN NOT NULL DEFAULT TRUE,
  vigencia_inicio DATE NOT NULL,
  vigencia_fim DATE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT catalog_produtos_codigo_formato CHECK (produto_codigo ~ '^PROD-[0-9]{3}$'),
  CONSTRAINT catalog_produtos_linha_formato CHECK (linha_codigo ~ '^LIN-[0-9]{2}$'),
  CONSTRAINT catalog_produtos_unidade CHECK (unidade_medida IN ('UN', 'KG', 'CX')),
  CONSTRAINT catalog_produtos_nome_obrigatorio CHECK (btrim(produto_nome) <> ''),
  CONSTRAINT catalog_produtos_vigencia_valida CHECK (vigencia_fim IS NULL OR vigencia_fim >= vigencia_inicio),
  -- Prova do "sem sobreposição silenciosa": duas vigências do mesmo código não podem se cruzar.
  CONSTRAINT catalog_produtos_sem_sobreposicao EXCLUDE USING gist (
    produto_codigo WITH =,
    daterange(vigencia_inicio, COALESCE(vigencia_fim, 'infinity'::date), '[)') WITH &&
  )
);

-- ============ Clientes canônicos ============
CREATE TABLE IF NOT EXISTS public.catalog_clientes (
  cliente_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  cliente_codigo TEXT NOT NULL,
  cliente_nome TEXT NOT NULL,
  rede_codigo TEXT,
  vigencia_inicio DATE NOT NULL,
  vigencia_fim DATE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT catalog_clientes_codigo_formato CHECK (cliente_codigo ~ '^CLI-[0-9]{3}$'),
  CONSTRAINT catalog_clientes_nome_obrigatorio CHECK (btrim(cliente_nome) <> ''),
  CONSTRAINT catalog_clientes_vigencia_valida CHECK (vigencia_fim IS NULL OR vigencia_fim >= vigencia_inicio),
  CONSTRAINT catalog_clientes_sem_sobreposicao EXCLUDE USING gist (
    cliente_codigo WITH =,
    daterange(vigencia_inicio, COALESCE(vigencia_fim, 'infinity'::date), '[)') WITH &&
  )
);

-- ============ Responsáveis canônicos (supervisor/promotor) ============
CREATE TABLE IF NOT EXISTS public.catalog_responsaveis (
  responsavel_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  responsavel_codigo TEXT NOT NULL,
  responsavel_tipo TEXT NOT NULL,
  responsavel_rotulo TEXT NOT NULL,
  vigencia_inicio DATE NOT NULL,
  vigencia_fim DATE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT catalog_responsaveis_codigo_formato CHECK (responsavel_codigo ~ '^(SUP|PROM)-[0-9]{3}$'),
  CONSTRAINT catalog_responsaveis_tipo CHECK (responsavel_tipo IN ('supervisor', 'promotor')),
  CONSTRAINT catalog_responsaveis_rotulo_sintetico CHECK (
    responsavel_rotulo ~ '^(Supervisor|Promotor) Sintético [0-9]{2}$'
  ),
  CONSTRAINT catalog_responsaveis_vigencia_valida CHECK (vigencia_fim IS NULL OR vigencia_fim >= vigencia_inicio),
  CONSTRAINT catalog_responsaveis_sem_sobreposicao EXCLUDE USING gist (
    responsavel_codigo WITH =,
    daterange(vigencia_inicio, COALESCE(vigencia_fim, 'infinity'::date), '[)') WITH &&
  )
);

-- ============ Territórios canônicos ============
CREATE TABLE IF NOT EXISTS public.catalog_territorios (
  territorio_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  territorio_codigo TEXT NOT NULL,
  territorio_nome TEXT NOT NULL,
  vigencia_inicio DATE NOT NULL,
  vigencia_fim DATE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT catalog_territorios_codigo_formato CHECK (territorio_codigo ~ '^REG-[0-9]{2}$'),
  CONSTRAINT catalog_territorios_nome_sintetico CHECK (territorio_nome ~ '^Região Sintética [0-9]{2}$'),
  CONSTRAINT catalog_territorios_vigencia_valida CHECK (vigencia_fim IS NULL OR vigencia_fim >= vigencia_inicio),
  CONSTRAINT catalog_territorios_sem_sobreposicao EXCLUDE USING gist (
    territorio_codigo WITH =,
    daterange(vigencia_inicio, COALESCE(vigencia_fim, 'infinity'::date), '[)') WITH &&
  )
);

-- ============ Vínculos responsável × território por vigência ============
-- Um território tem no máximo um responsável ativo por período: sobreposição é recusada.
CREATE TABLE IF NOT EXISTS public.catalog_vinculos (
  vinculo_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  responsavel_codigo TEXT NOT NULL,
  territorio_codigo TEXT NOT NULL,
  vigencia_inicio DATE NOT NULL,
  vigencia_fim DATE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT catalog_vinculos_responsavel_formato CHECK (responsavel_codigo ~ '^(SUP|PROM)-[0-9]{3}$'),
  CONSTRAINT catalog_vinculos_territorio_formato CHECK (territorio_codigo ~ '^REG-[0-9]{2}$'),
  CONSTRAINT catalog_vinculos_vigencia_valida CHECK (vigencia_fim IS NULL OR vigencia_fim >= vigencia_inicio),
  CONSTRAINT catalog_vinculos_sem_sobreposicao_territorio EXCLUDE USING gist (
    territorio_codigo WITH =,
    daterange(vigencia_inicio, COALESCE(vigencia_fim, 'infinity'::date), '[)') WITH &&
  )
);

CREATE INDEX IF NOT EXISTS catalog_produtos_codigo_vigencia_idx
  ON public.catalog_produtos (produto_codigo, vigencia_inicio, vigencia_fim);
CREATE INDEX IF NOT EXISTS catalog_clientes_codigo_vigencia_idx
  ON public.catalog_clientes (cliente_codigo, vigencia_inicio, vigencia_fim);
CREATE INDEX IF NOT EXISTS catalog_responsaveis_codigo_vigencia_idx
  ON public.catalog_responsaveis (responsavel_codigo, vigencia_inicio, vigencia_fim);
CREATE INDEX IF NOT EXISTS catalog_territorios_codigo_vigencia_idx
  ON public.catalog_territorios (territorio_codigo, vigencia_inicio, vigencia_fim);
CREATE INDEX IF NOT EXISTS catalog_vinculos_responsavel_vigencia_idx
  ON public.catalog_vinculos (responsavel_codigo, vigencia_inicio, vigencia_fim);
CREATE INDEX IF NOT EXISTS catalog_vinculos_territorio_vigencia_idx
  ON public.catalog_vinculos (territorio_codigo, vigencia_inicio, vigencia_fim);

-- ============ Pendências de resolução ============
-- Homônimo, lacuna de vigência ou sobreposição detectada NUNCA são resolvidos
-- por aproximação: viram pendência com motivo explícito para decisão humana.
CREATE TABLE IF NOT EXISTS public.catalog_pendencias_resolucao (
  pendencia_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tipo TEXT NOT NULL,
  entidade_tipo TEXT NOT NULL,
  entidade_codigo TEXT,
  detalhe TEXT,
  motivo TEXT NOT NULL,
  correlation_id UUID NOT NULL DEFAULT gen_random_uuid(),
  status TEXT NOT NULL DEFAULT 'pendente',
  resolvida_por UUID REFERENCES auth.users(id) ON DELETE SET NULL,
  resolvida_em TIMESTAMPTZ,
  resolucao_motivo TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT catalog_pendencias_tipo CHECK (
    tipo IN ('homonimo', 'lacuna', 'sobreposicao', 'sem_vigencia', 'outro')
  ),
  CONSTRAINT catalog_pendencias_entidade CHECK (
    entidade_tipo IN ('produto', 'cliente', 'responsavel', 'territorio', 'vinculo')
  ),
  CONSTRAINT catalog_pendencias_motivo_obrigatorio CHECK (btrim(motivo) <> ''),
  CONSTRAINT catalog_pendencias_status CHECK (status IN ('pendente', 'resolvida', 'descartada')),
  CONSTRAINT catalog_pendencias_resolvida_completa CHECK (
    status = 'pendente'
    OR (
      resolvida_em IS NOT NULL
      AND resolucao_motivo IS NOT NULL
      AND btrim(resolucao_motivo) <> ''
    )
  )
);

CREATE INDEX IF NOT EXISTS catalog_pendencias_status_idx
  ON public.catalog_pendencias_resolucao (status, created_at DESC);
CREATE INDEX IF NOT EXISTS catalog_pendencias_entidade_idx
  ON public.catalog_pendencias_resolucao (entidade_tipo, entidade_codigo);

COMMENT ON TABLE public.catalog_produtos IS
  'T4.1/SPEC-1-004: produto canônico com vigência; sobreposição recusada por constraint.';
COMMENT ON TABLE public.catalog_pendencias_resolucao IS
  'T4.1/SPEC-1-004: ambiguidade, lacuna ou sobreposição viram pendência; nunca resolução silenciosa.';

-- ============ RLS ============
ALTER TABLE public.catalog_produtos ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.catalog_clientes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.catalog_responsaveis ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.catalog_territorios ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.catalog_vinculos ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.catalog_pendencias_resolucao ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS catalog_produtos_read ON public.catalog_produtos;
CREATE POLICY catalog_produtos_read ON public.catalog_produtos
  FOR SELECT TO authenticated USING (true);
DROP POLICY IF EXISTS catalog_produtos_insert ON public.catalog_produtos;
CREATE POLICY catalog_produtos_insert ON public.catalog_produtos
  FOR INSERT TO authenticated WITH CHECK (private.has_operation('editar_catalogo'));
DROP POLICY IF EXISTS catalog_produtos_update ON public.catalog_produtos;
CREATE POLICY catalog_produtos_update ON public.catalog_produtos
  FOR UPDATE TO authenticated
  USING (private.has_operation('editar_catalogo'))
  WITH CHECK (private.has_operation('editar_catalogo'));
DROP POLICY IF EXISTS catalog_produtos_delete ON public.catalog_produtos;
CREATE POLICY catalog_produtos_delete ON public.catalog_produtos
  FOR DELETE TO authenticated USING (private.has_operation('editar_catalogo'));

DROP POLICY IF EXISTS catalog_clientes_read ON public.catalog_clientes;
CREATE POLICY catalog_clientes_read ON public.catalog_clientes
  FOR SELECT TO authenticated USING (true);
DROP POLICY IF EXISTS catalog_clientes_insert ON public.catalog_clientes;
CREATE POLICY catalog_clientes_insert ON public.catalog_clientes
  FOR INSERT TO authenticated WITH CHECK (private.has_operation('editar_catalogo'));
DROP POLICY IF EXISTS catalog_clientes_update ON public.catalog_clientes;
CREATE POLICY catalog_clientes_update ON public.catalog_clientes
  FOR UPDATE TO authenticated
  USING (private.has_operation('editar_catalogo'))
  WITH CHECK (private.has_operation('editar_catalogo'));
DROP POLICY IF EXISTS catalog_clientes_delete ON public.catalog_clientes;
CREATE POLICY catalog_clientes_delete ON public.catalog_clientes
  FOR DELETE TO authenticated USING (private.has_operation('editar_catalogo'));

DROP POLICY IF EXISTS catalog_responsaveis_read ON public.catalog_responsaveis;
CREATE POLICY catalog_responsaveis_read ON public.catalog_responsaveis
  FOR SELECT TO authenticated USING (true);
DROP POLICY IF EXISTS catalog_responsaveis_insert ON public.catalog_responsaveis;
CREATE POLICY catalog_responsaveis_insert ON public.catalog_responsaveis
  FOR INSERT TO authenticated WITH CHECK (private.has_operation('editar_catalogo'));
DROP POLICY IF EXISTS catalog_responsaveis_update ON public.catalog_responsaveis;
CREATE POLICY catalog_responsaveis_update ON public.catalog_responsaveis
  FOR UPDATE TO authenticated
  USING (private.has_operation('editar_catalogo'))
  WITH CHECK (private.has_operation('editar_catalogo'));
DROP POLICY IF EXISTS catalog_responsaveis_delete ON public.catalog_responsaveis;
CREATE POLICY catalog_responsaveis_delete ON public.catalog_responsaveis
  FOR DELETE TO authenticated USING (private.has_operation('editar_catalogo'));

DROP POLICY IF EXISTS catalog_territorios_read ON public.catalog_territorios;
CREATE POLICY catalog_territorios_read ON public.catalog_territorios
  FOR SELECT TO authenticated USING (true);
DROP POLICY IF EXISTS catalog_territorios_insert ON public.catalog_territorios;
CREATE POLICY catalog_territorios_insert ON public.catalog_territorios
  FOR INSERT TO authenticated WITH CHECK (private.has_operation('editar_catalogo'));
DROP POLICY IF EXISTS catalog_territorios_update ON public.catalog_territorios;
CREATE POLICY catalog_territorios_update ON public.catalog_territorios
  FOR UPDATE TO authenticated
  USING (private.has_operation('editar_catalogo'))
  WITH CHECK (private.has_operation('editar_catalogo'));
DROP POLICY IF EXISTS catalog_territorios_delete ON public.catalog_territorios;
CREATE POLICY catalog_territorios_delete ON public.catalog_territorios
  FOR DELETE TO authenticated USING (private.has_operation('editar_catalogo'));

DROP POLICY IF EXISTS catalog_vinculos_read ON public.catalog_vinculos;
CREATE POLICY catalog_vinculos_read ON public.catalog_vinculos
  FOR SELECT TO authenticated USING (true);
DROP POLICY IF EXISTS catalog_vinculos_insert ON public.catalog_vinculos;
CREATE POLICY catalog_vinculos_insert ON public.catalog_vinculos
  FOR INSERT TO authenticated WITH CHECK (private.has_operation('editar_catalogo'));
DROP POLICY IF EXISTS catalog_vinculos_update ON public.catalog_vinculos;
CREATE POLICY catalog_vinculos_update ON public.catalog_vinculos
  FOR UPDATE TO authenticated
  USING (private.has_operation('editar_catalogo'))
  WITH CHECK (private.has_operation('editar_catalogo'));
DROP POLICY IF EXISTS catalog_vinculos_delete ON public.catalog_vinculos;
CREATE POLICY catalog_vinculos_delete ON public.catalog_vinculos
  FOR DELETE TO authenticated USING (private.has_operation('editar_catalogo'));

-- Pendências: leitura para autenticados; criação pela engine de resolução (T4.2)
-- e pelos testes; resolução exige editar_catalogo; exclusão não é exposta.
DROP POLICY IF EXISTS catalog_pendencias_read ON public.catalog_pendencias_resolucao;
CREATE POLICY catalog_pendencias_read ON public.catalog_pendencias_resolucao
  FOR SELECT TO authenticated USING (true);
DROP POLICY IF EXISTS catalog_pendencias_insert ON public.catalog_pendencias_resolucao;
CREATE POLICY catalog_pendencias_insert ON public.catalog_pendencias_resolucao
  FOR INSERT TO authenticated WITH CHECK (true);
DROP POLICY IF EXISTS catalog_pendencias_update ON public.catalog_pendencias_resolucao;
CREATE POLICY catalog_pendencias_update ON public.catalog_pendencias_resolucao
  FOR UPDATE TO authenticated
  USING (private.has_operation('editar_catalogo'))
  WITH CHECK (private.has_operation('editar_catalogo'));

REVOKE ALL ON TABLE public.catalog_produtos FROM PUBLIC, anon, authenticated;
REVOKE ALL ON TABLE public.catalog_clientes FROM PUBLIC, anon, authenticated;
REVOKE ALL ON TABLE public.catalog_responsaveis FROM PUBLIC, anon, authenticated;
REVOKE ALL ON TABLE public.catalog_territorios FROM PUBLIC, anon, authenticated;
REVOKE ALL ON TABLE public.catalog_vinculos FROM PUBLIC, anon, authenticated;
REVOKE ALL ON TABLE public.catalog_pendencias_resolucao FROM PUBLIC, anon, authenticated;

GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.catalog_produtos TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.catalog_clientes TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.catalog_responsaveis TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.catalog_territorios TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.catalog_vinculos TO authenticated;
GRANT SELECT, INSERT, UPDATE ON TABLE public.catalog_pendencias_resolucao TO authenticated;
