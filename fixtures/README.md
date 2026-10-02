# Fixtures sintéticas da Fase 1

Todos os arquivos desta pasta são fictícios e servem apenas para validar os contratos da T2.1.

- `valid/`: entradas que devem ser aceitas pelo contrato.
- `invalid/`: entradas que devem ser rejeitadas com motivo explícito.
- `vendas_reenvio_identico.csv`: cópia byte a byte da fixture de vendas para o teste de idempotência da T2.2.
- `estrutura_comercial_ponto_virgula.csv`: variante válida do delimitador aceito.
- `parametros_calculo.csv`: fixture válida do catálogo de parâmetros do cálculo (T2.1b), com os 8 parâmetros da metodologia oficial em valores sintéticos.
- Fixtures de vendas e produtos foram atualizadas pela T2.1b: vendas ganhou `devolucoes`, `tributos`, `valor_liquido` e `canal_venda`; produtos ganhou `linha_tipo`.

Nenhum arquivo contém dados reais, credenciais ou PII real. Não usar esta pasta como evidência de compatibilidade com o schema produtivo: essa revalidação depende do Gate G1.
