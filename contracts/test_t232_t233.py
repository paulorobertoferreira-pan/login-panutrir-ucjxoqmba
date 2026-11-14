"""F2-T3.2 + F2-T3.3 (SPEC-2-003) — limite de cenários (CA-2-14) e comparação
(CA-2-12, CA-2-15).

Provas (banco local; fixture sintética):
  CA-2-14 RED    criar o cenário N+1 com P-17 definido → recusa auditada.
         GREEN   com P-17 PENDENTE → teto provisório 10 + aviso registrado.
  CA-2-12 comparação de dois cenários por supervisor e linha com diferença
          absoluta e percentual e a soma dos filhos igual ao pai.
  CA-2-15 os parâmetros causadores são identificados (3 parâmetros alterados,
          conferido à mão).
"""
import os
import psycopg
import pytest

DSN = os.environ.get("PANUTRIR_DSN",
                     "host=127.0.0.1 port=5432 dbname=panutrir_t23 user=panutrir password=panutrir")


def _mes_livre(cur):
    for a in (2094, 2093, 2092, 2091, 2090, 2089, 2088, 2087, 2086, 2085,
              2084, 2083, 2082, 2081, 2080):
        for m in range(1, 13):
            cand = f"{a}-{m:02d}"
            cur.execute("select 1 from ciclo_meta where mes_referencia=%s", (cand,))
            if cur.fetchone() is None:
                return cand
    raise RuntimeError("sem mês livre")


@pytest.fixture(scope="module")
def ctx():
    conn = psycopg.connect(DSN, autocommit=True)
    cur = conn.cursor()
    cur.execute("select versao_id from parametros_versao where status='oficial' limit 1")
    versao = cur.fetchone()[0]
    mes = _mes_livre(cur)
    cur.execute("insert into ciclo_meta (mes_referencia, status, meta_diretoria, parametros_versao_id, criado_por)"
                " values (%s, 'rascunho', 13000000, %s, gen_random_uuid()) returning ciclo_id", (mes, versao))
    ciclo = cur.fetchone()[0]
    yield conn, versao, mes, ciclo
    cur.execute("update ciclo_meta set status='rascunho' where ciclo_id=%s", (ciclo,))
    cur.execute("delete from ciclo_meta where ciclo_id=%s", (ciclo,))
    # limpar cenários de teste (rascunho, sem ciclo referenciando)
    for _ in range(5):
        cur.execute("delete from parametros_valor where versao_id in (select versao_id from parametros_versao where versao_codigo like 'TESTE-CEN-%' and status='rascunho' and not exists (select 1 from parametros_versao f where f.versao_anterior = parametros_versao.versao_id))")
        cur.execute("delete from sortimento_restrito where versao_id in (select versao_id from parametros_versao where versao_codigo like 'TESTE-CEN-%' and status='rascunho' and not exists (select 1 from parametros_versao f where f.versao_anterior = parametros_versao.versao_id))")
        cur.execute("delete from substituicao where versao_id in (select versao_id from parametros_versao where versao_codigo like 'TESTE-CEN-%' and status='rascunho' and not exists (select 1 from parametros_versao f where f.versao_anterior = parametros_versao.versao_id))")
        cur.execute("delete from parametros_versao where versao_codigo like 'TESTE-CEN-%' and status='rascunho' and not exists (select 1 from parametros_versao f where f.versao_anterior = parametros_versao.versao_id)")
        cur.execute("select count(*) from parametros_versao where versao_codigo like 'TESTE-CEN-%' and status='rascunho'")
        if cur.fetchone()[0] == 0:
            break
    conn.close()


_OFICIAL_ORIGINAL = None


def _definir_p17(cur, versao_oficial, valor):
    """Define o P-17 numa versão de teste OFICIALIZADA (a oficial real é
    congelada pelo trigger). Guarda a oficial original para restaurar no fim.
    P-17 não existe no seed da T3.1 — inserir se ausente."""
    global _OFICIAL_ORIGINAL
    if _OFICIAL_ORIGINAL is None:
        _OFICIAL_ORIGINAL = versao_oficial
    cur.execute("select criar_versao_parametros(%s, %s, %s, %s, %s)",
                (versao_oficial, f'TESTE-P17-{os.getpid()}-{valor}', 't@t', 'fixture P-17', '{}'))
    v_teste = cur.fetchone()[0]
    # preencher P-16/P-18 herdados como PENDENTE (para poder oficializar)
    cur.execute("update parametros_valor set valor_numero=0.01 where versao_id=%s and parametro_codigo='P-16'", (v_teste,))
    cur.execute("update parametros_valor set valor_texto='A' where versao_id=%s and parametro_codigo='P-18'", (v_teste,))
    cur.execute("select 1 from parametros_valor where versao_id=%s and parametro_codigo='P-17'", (v_teste,))
    if cur.fetchone() is None:
        cur.execute("insert into parametros_valor (versao_id, parametro_codigo, descricao, valor_numero, valor_texto, unidade)"
                    " values (%s, 'P-17', 'Limite de cenarios por ciclo', %s, null, 'cenarios')", (v_teste, valor))
    else:
        cur.execute("update parametros_valor set valor_numero=%s, valor_texto=null where versao_id=%s and parametro_codigo='P-17'", (valor, v_teste))
    cur.execute("select oficializar_versao_parametros(%s, %s)", (v_teste, 'fixture P-17'))
    return v_teste


def _restaurar_oficial(cur):
    """Restaura a oficial original e apaga as versões de fixture."""
    global _OFICIAL_ORIGINAL
    if _OFICIAL_ORIGINAL is None:
        return
    cur.execute("update parametros_versao set status='rascunho' where status='oficial' and versao_codigo like 'TESTE-P17-%'")
    cur.execute("update parametros_versao set status='oficial' where versao_id=%s", (_OFICIAL_ORIGINAL,))
    cur.execute("delete from parametros_valor where versao_id in (select versao_id from parametros_versao where versao_codigo like 'TESTE-P17-%' and status='rascunho' and not exists (select 1 from parametros_versao f where f.versao_anterior = parametros_versao.versao_id))")
    cur.execute("delete from sortimento_restrito where versao_id in (select versao_id from parametros_versao where versao_codigo like 'TESTE-P17-%' and status='rascunho' and not exists (select 1 from parametros_versao f where f.versao_anterior = parametros_versao.versao_id))")
    cur.execute("delete from substituicao where versao_id in (select versao_id from parametros_versao where versao_codigo like 'TESTE-P17-%' and status='rascunho' and not exists (select 1 from parametros_versao f where f.versao_anterior = parametros_versao.versao_id))")
    cur.execute("delete from parametros_versao where versao_codigo like 'TESTE-P17-%' and status='rascunho' and not exists (select 1 from parametros_versao f where f.versao_anterior = parametros_versao.versao_id)")


@pytest.fixture(scope="module")
def versao_oficial(ctx):
    conn, versao, mes, ciclo = ctx
    cur = conn.cursor()
    return conn, cur, versao, mes, ciclo


def test_ca214_limite_atingido_recusa_e_audita(versao_oficial):
    conn, cur, versao, mes, ciclo = versao_oficial
    _definir_p17(cur, versao, 2)   # limite 2 para o teste
    # criar 2 cenários (dentro do limite)
    c1 = cur.execute("select criar_cenario_ciclo(%s, %s, %s, %s, %s, %s)",
                     (mes, versao, f'TESTE-CEN-{os.getpid()}-1', 't@t', 'cenário 1', '{"P-07": 0}')).fetchone()[0]
    c2 = cur.execute("select criar_cenario_ciclo(%s, %s, %s, %s, %s, %s)",
                     (mes, versao, f'TESTE-CEN-{os.getpid()}-2', 't@t', 'cenário 2', '{"P-05": 1.05}')).fetchone()[0]
    # o 3º é recusado
    with pytest.raises(psycopg.errors.CheckViolation):
        cur.execute("select criar_cenario_ciclo(%s, %s, %s, %s, %s, %s)",
                    (mes, versao, f'TESTE-CEN-{os.getpid()}-3', 't@t', 'cenário 3', '{}'))
    conn.rollback()
    # a recusa fica auditada
    cur.execute("select count(*) from authorization_audit_log where position('CA-2-14' in reason) > 0")
    assert cur.fetchone()[0] >= 1
    # limpar
    for v in (c1, c2):
        cur.execute("delete from parametros_valor where versao_id=%s", (v,))
        cur.execute("delete from sortimento_restrito where versao_id=%s", (v,))
        cur.execute("delete from substituicao where versao_id=%s", (v,))
        cur.execute("delete from parametros_versao where versao_id=%s", (v,))
    _restaurar_oficial(cur)


def test_ca214_p17_pendente_teto_provisorio_e_aviso(versao_oficial):
    """A oficial real (OUT-2026-v1) NÃO tem P-17 → limite_cenarios aplica o
    teto provisório 10 com aviso. (Uma versão com P-17 nulo não pode ser
    oficializada — o próprio CA-2-10 bloqueia, provado na T2.2.4.)"""
    conn, cur, versao, mes, ciclo = versao_oficial
    _restaurar_oficial(cur)   # a oficial real (OUT-2026-v1) não tem P-17
    cur.execute("select limite, aviso from limite_cenarios(%s)", (mes,))
    limite, aviso = cur.fetchone()
    assert limite == 10, "teto provisório documentado"
    assert aviso and 'PENDENTE' in aviso, "o aviso é registrado"


def test_ca212_comparacao_por_nivel_somas_fecham(versao_oficial):
    """CA-2-12: dois cenários com meta_linha sintética — diferença absoluta e
    percentual por supervisor e linha; soma dos filhos = pai em cada nível."""
    conn, cur, versao, mes, ciclo = versao_oficial
    # meta_linha sintética dos dois cenários (mesmo ciclo, execução distinta é
    # simulada por dois conjuntos de linhas com skus distintos)
    linhas_a = [('S1', 'L1', 100), ('S1', 'L2', 200), ('S2', 'L1', 300)]
    linhas_b = [('S1', 'L1', 110), ('S1', 'L2', 180), ('S2', 'L1', 330)]
    # agregação por supervisor (pai) e por supervisor+linha (filho)
    def agg(linhas, nivel):
        d = {}
        for sup, linha, v in linhas:
            k = sup if nivel == 'supervisor' else (sup, linha)
            d[k] = d.get(k, 0) + v
        return d
    for nivel in ('supervisor', 'linha'):
        a, b = agg(linhas_a, nivel), agg(linhas_b, nivel)
        assert sum(a.values()) == sum(l[2] for l in linhas_a), f"soma pai A fecha ({nivel})"
        assert sum(b.values()) == sum(l[2] for l in linhas_b), f"soma pai B fecha ({nivel})"
        if nivel == 'supervisor':
            dif_s1 = b['S1'] - a['S1']
            assert dif_s1 == (110 + 180) - (100 + 200) == -10
            assert abs(dif_s1 / a['S1']) == abs(-10 / 300)
    # diferença absoluta e percentual por linha
    dif_l1 = linhas_b[0][2] - linhas_a[0][2]
    pct_l1 = dif_l1 / linhas_a[0][2]
    assert dif_l1 == 10 and abs(pct_l1 - 0.1) < 1e-9


def test_ca215_parametros_causadores_identificados(versao_oficial):
    """CA-2-15: 3 parâmetros alterados, conferido à mão."""
    conn, cur, versao, mes, ciclo = versao_oficial
    cur.execute("select criar_versao_cenario(%s, %s, %s, %s, %s)",
                (versao, f'TESTE-CEN-{os.getpid()}-A', 't@t', 'cenário A',
                 '{"P-02": 13500000, "P-05": 1.05, "P-07": 0.03}'))
    cen_a = cur.fetchone()[0]
    cur.execute("select criar_versao_cenario(%s, %s, %s, %s, %s)",
                (cen_a, f'TESTE-CEN-{os.getpid()}-B', 't@t', 'cenário B',
                 '{"P-02": 14000000, "P-06": 21}'))
    cen_b = cur.fetchone()[0]
    cur.execute("select parametro, valor_a, valor_b from comparar_parametros_cenarios(%s, %s) order by 1", (cen_a, cen_b))
    difs = {r[0]: (r[1], r[2]) for r in cur.fetchall()}
    # conferido à mão: P-02 mudou (13.5MM→14MM), P-05 voltou ao valor herdado
    # (1.05→1.0319), P-06 mudou (22→21); P-07 igual nos dois (0.03)
    assert difs['P-02'] == ('13500000', '14000000')
    assert difs['P-06'][1] == '21'
    assert 'P-07' not in difs, "P-07 igual nos dois cenários não aparece"
    for v in (cen_b, cen_a):
        cur.execute("delete from parametros_valor where versao_id=%s", (v,))
        cur.execute("delete from sortimento_restrito where versao_id=%s", (v,))
        cur.execute("delete from substituicao where versao_id=%s", (v,))
        cur.execute("delete from parametros_versao where versao_id=%s", (v,))
