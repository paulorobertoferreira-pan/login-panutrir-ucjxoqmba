import pytest

from redistribuicao_core import Linha, Movimento, Unidade, ratear_residuo, simular


A = Linha('A', '1', 'S1', 'P1')
B = Linha('B', '1', 'S2', 'P2')
N = Linha('N', '1', 'S2', 'P2')


def rodar(*movimentos, **alteracoes):
    args = dict(base={A: 800, B: 150}, meta_diretoria=1000,
                clientes_anterior={'A', 'B', 'ANTIGO'}, clientes_atual={'A', 'B', 'N', 'ANTIGO'},
                movimentos=list(movimentos))
    return simular(**(args | alteracoes))


def test_rateio_antes_do_movimento_mantem_total_e_base_intacta():
    base = {A: 800, B: 150}
    m = Movimento(Unidade('supervisor', 'S1'), Unidade('loja', 'N'), {A: 200}, {N: 200})
    resultado = rodar(m, base=base)
    assert resultado == {A: 643, B: 157, N: 200}
    assert sum(resultado.values()) == 1000
    assert base == {A: 800, B: 150}


def test_cliente_antigo_com_meta_recebe_por_promotor():
    m = Movimento(Unidade('loja', 'A'), Unidade('promotor', 'P2'), {A: 10}, {B: 10})
    assert rodar(m)[B] == 167


@pytest.mark.parametrize('atual,anterior', [({'A', 'B', 'N'}, {'N'}), ({'A', 'B'}, set())])
def test_primeira_meta_exige_presenca_atual_e_ausencia_anterior(atual, anterior):
    m = Movimento(Unidade('loja', 'A'), Unidade('loja', 'N'), {A: 10}, {N: 10})
    with pytest.raises(ValueError, match='somente cliente novo'):
        rodar(m, clientes_atual=atual, clientes_anterior=anterior)


@pytest.mark.parametrize('debito,credito,erro', [(10, 11, 'devem ser iguais'), (844, 844, 'saldo suficiente'), (1.5, 1.5, 'centavos')])
def test_rejeita_movimento_invalido(debito, credito, erro):
    m = Movimento(Unidade('promotor', 'P1'), Unidade('supervisor', 'S2'), {A: debito}, {B: credito})
    with pytest.raises(ValueError, match=erro):
        rodar(m)


def test_recusa_origem_e_destino_sobrepostos():
    m = Movimento(Unidade('supervisor', 'S1'), Unidade('loja', 'A'), {A: 10}, {A: 10})
    with pytest.raises(ValueError, match='sobreposta'):
        rodar(m)


def test_sem_meta_positiva_nao_pode_ratear():
    with pytest.raises(ValueError, match='sem linhas com meta positiva'):
        rodar(base={A: 0, B: 0})


def test_sobra_vai_para_maior_combinacao_e_ignora_zeros():
    assert ratear_residuo({A: 800, B: 150, N: 0}, 1000) == {A: 43, B: 7}
    assert ratear_residuo({B: 100, A: 100}, 201) == {A: 1}
    assert ratear_residuo({A: 100}, 100) == {}


def test_rateio_negativo_com_sobra_maior_que_saldo_da_primeira_linha():
    assert ratear_residuo({N: 1, B: 1, A: 1}, 1) == {A: -1, B: -1}


def test_recusa_base_negativa_e_base_mensal_ausente():
    with pytest.raises(ValueError, match='negativos'):
        rodar(base={A: -1, B: 150})
    with pytest.raises(ValueError, match='duas bases'):
        rodar(clientes_anterior=None)


def test_rateio_de_excesso_na_base():
    assert rodar(meta_diretoria=900) == {A: 757, B: 143}
