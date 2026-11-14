-- D3 (Kim, 11/11) — cod_cliente = 0 é CLIENTE REAL.
--
-- A constraint da T2.2 exigia cod_cliente > 0 e rejeitava as 21 linhas de
-- Out/26 com codcli = 0 (R$ 80.117,36 de bruta). A auditoria do gabarito traz
-- o código 0 como cliente real com R$ 50.002,93 de venda, e a Kim confirmou em
-- 11/11 que o 0 e o vazio ENTRAM no universo (V-02 deixa de rejeitar).
--
-- O que continua inválido: código NEGATIVO (não existe) e SKU 0 (não existe
-- SKU 0 no catálogo). O vazio/nulo não chega aqui — é barrado na leitura.
begin;

alter table public.venda_mensal drop constraint if exists venda_mensal_codigos_ck;
alter table public.venda_mensal
  add constraint venda_mensal_codigos_ck check (cod_cliente >= 0 and cod_sku > 0);

comment on constraint venda_mensal_codigos_ck on public.venda_mensal is
  'D3: cod_cliente 0 é cliente real (entra); negativo e SKU 0 continuam inválidos.';

end;
