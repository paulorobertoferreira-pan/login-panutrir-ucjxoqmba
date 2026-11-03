-- Promotores: chave por PAPEL e carga dos 128 vendedores da estrutura comercial.
--
-- Autorizado por Alex (31/10): (1) codigos podem repetir entre papeis -> chave (papel, codigo);
-- (2) vendedor vazio = cliente SEM promotor; (3) carregar os 128 vendedores como promotores,
-- codigo e nome exatamente como na fonte.
--
-- Por que a constraint muda: a versao anterior era EXCLUDE so em responsavel_codigo e
-- IMPEDIA o codigo 167 ser supervisor E promotor. O 167 e supervisor (CIRO ROLIM MORAES)
-- e estava gravado como "promotor" de 293 clientes -- 514 dos 624 preenchidos apontavam
-- para o codigo do proprio supervisor.
--
-- Prova contra o gabarito do cliente: 123/123 pares supervisor x promotor batem no centavo
-- e "sem promotor" fecha exatamente R$ 563.066,71 (aba Meta Supervisor).
--
-- A atribuicao cliente -> promotor NAO esta aqui: sao 3.317 linhas de dado derivado.
-- Ela e reproduzida por `contracts/carga_promotores.py`, que le a estrutura comercial
-- e gera o UPDATE -- versionar o gerador, nao o despejo.
--
-- CONTEUDO GERADO DA FONTE (estrutura_comercial_atual.xlsx) -- nunca redigitado.

begin;

alter table public.catalog_responsaveis
  drop constraint if exists catalog_responsaveis_sem_sobreposicao;
alter table public.catalog_responsaveis
  add constraint catalog_responsaveis_sem_sobreposicao
  exclude using gist (
    responsavel_tipo with =,
    responsavel_codigo with =,
    daterange(vigencia_inicio, coalesce(vigencia_fim,'infinity'::date), '[)') with &&
  );

create temp table _prom (codigo text primary key, nome text not null) on commit drop;
insert into _prom values
  ('174','LUAN DA SILVA CARNEIRO'),
  ('180','PAULO CESAR ALVES'),
  ('182','GIOVANI SARDINHA PEREIRA'),
  ('183','LEANDRO MORAES PULIDO'),
  ('185','ESTEVAO VIEIRA SALVADIO'),
  ('186','ALEXANDRE MARQUES SANTOS'),
  ('187','VAGNER VINICIUS MENDES'),
  ('188','LUCAS RIBEIRO DA SILVA ANDRADE'),
  ('189','JOSIANE GAZONI MOREIRA DA SILVA'),
  ('190','EDNA MARIA SCHEMBERGER OLIVEIRA'),
  ('191','JONATHAN HENRIQUE FUZATI'),
  ('192','JULIO CESAR JORGE'),
  ('193','MARCELO LOPES VIEIRA DA SILVA'),
  ('194','CLEBIA MARIA DE REZENDE CANOSSA'),
  ('195','MONICA MARIA DA SILVA'),
  ('196','DIORANDE DE ARAUJO SILVA'),
  ('197','ADRIANO DOS SANTOS'),
  ('198','JOHNNY DOS SANTOS'),
  ('199','FRANCISCO AUGUSTO ROSE'),
  ('200','JAQUELINE VIEIRA DA SILVA'),
  ('201','KENYARA ANDRADE DA LUZ'),
  ('202','MARCIO MIRANDA LIMA'),
  ('203','WELLINGTON ALVES DOS SANTOS'),
  ('204','JESIANE CASSIA DE OLIVEIRA'),
  ('205','LEANDRO ALVES DE CAMARGO'),
  ('206','MARCOS ROBERTO FERREIRA DO CARMO'),
  ('207','ROSELI FONTOURA RODRIGUES'),
  ('208','JEAN MICHEL DA SILVA'),
  ('209','ROZICLEIA ALVES DE LIMA'),
  ('210','ADRIANO SIDNEI MELLO'),
  ('211','CAMILA DE CASSIA OLIVEIRA DE SOUZA'),
  ('212','UEDERLI VILACA FERNANDES'),
  ('213','SILVANA GARBELINI VALERETO'),
  ('214','AMANDA BARBOSA SANTANA'),
  ('216','MAGNUM OLIVEIRA SILVA'),
  ('217','MARIA ELIANE GARCON'),
  ('218','VANESSA CRISTIANE ZAPOTOSNI'),
  ('220','MICHELE DE SOUZA RODRIGUES'),
  ('221','JESSICA MENEZES MARTINS'),
  ('222','DEJANIR APARECIDA MOREIRA'),
  ('223','PAULO VITOR ALMEIDA LOPES'),
  ('224','MARCIO SOARES DE MELO'),
  ('225','JHONATAN FERREIRA DA CRUZ'),
  ('226','LUIZ GUSTAVO JARDIM SANTOS'),
  ('227','JENNIFER LOPES LEITE'),
  ('228','FRANSCIELE GUEDES RIBEIRO'),
  ('230','JAKELINE PEREIRA DO NASCIMENTO SOUZA'),
  ('231','KETLYN COELHO DANTAS'),
  ('232','DAIANE FERNANDES DE JEZUS'),
  ('233','THIAGO SANTOS DE LUNA'),
  ('235','VALERIA CRISTINA GONCALVES FONTES'),
  ('237','DAIANE STEFF'),
  ('239','JOSICLEIDE DA SILVA SANTOS'),
  ('240','KISI DE PAULA GONZAGA'),
  ('241','MAICON RIBEIRO INACIO'),
  ('242','ILBERTON AZEREDO OLIVEIRA'),
  ('243','FERNANDO JOSE LOPES MARTINS'),
  ('244','LUIS CLAUDIO BISPO DOS SANTOS'),
  ('245','CARLA RENATA LIMA VEIGA'),
  ('247','DOUGLAS MOREIRA SOUZA'),
  ('248','SOLANGE APARECIDA FERREIRA DA CONCEICAO'),
  ('249','DANIELA RAMOS DA SILVA'),
  ('250','ELIANA GABERLINI'),
  ('251','DERALDO DE SOUZA'),
  ('252','RUDNEY GONCALVES PIRES'),
  ('253','ROSANGELA FERREIRA'),
  ('255','MARCELO TRAJANO DE SOUZA'),
  ('256','MILENA XAVIER COELHO'),
  ('257','INGREDY ARTEMAN DE OLIVEIRA'),
  ('258','MAX ANTONIO PEREIRA'),
  ('260','SIMONE ROSA DA SILVA DE ABREU'),
  ('261','VALERIA ALVES DA SILVA CORREIA'),
  ('262','LUIZ HENRIQUE MOREIRA DOS SANTOS'),
  ('263','GIOVANI AVANCI'),
  ('264','ARLENE DE FATIMA MOREIRA'),
  ('265','LUCAS FERNANDES DA SILVA'),
  ('266','ROBSON ANTONIO MIQUELINO'),
  ('267','JEAN CARLOS MARTINS'),
  ('269','ANAGILI SEGANTIM FATORELLI DA SILVA'),
  ('271','ADRIANA ZALUSKI'),
  ('272','ALYSON DE FREITAS'),
  ('273','EMERSON GABRIEL CAMPOS DE SOUSA'),
  ('274','ANTONIO OLIVANDO DO NASCIMENTO'),
  ('275','ANA PAULA PINHEIRO MATOS'),
  ('276','ELAINE BUENO PINTO FRANCISCO'),
  ('278','RICARDO ROQUE DA HORA JUNIOR'),
  ('279','MARIANA ALVES VIEIRA DOS SANTOS'),
  ('282','SANDRA REGINA PINTO'),
  ('283','TAMIRES LUCAS'),
  ('284','PATRICIA FERREIRA CUNHA'),
  ('287','JOAO SANTANA DOS SANTOS'),
  ('288','DEBORA VALERIA GARDIANO DE OLIVEIRA'),
  ('290','ROGERIO CASTELLANO'),
  ('292','GLEIDE LUDIMILA DOS SANTOS'),
  ('293','FLAVIA CAMILA DE OLIVEIRA IGNACIO'),
  ('294','BEATRIZ MARIA DOS SANTOS'),
  ('296','ANDERSON DOS SANTOS MARTINS'),
  ('298','BRUNO FERNANDES'),
  ('299','LUCAS PEREIRA ROCHA'),
  ('300','VERA CRISTINA DA SILVA'),
  ('302','JOICE FERNANDA DA SILVA TRINDADE'),
  ('303','HENRIQUE SALES DOS SANTOS'),
  ('304','CLEYTON GONCALVES FEITOZA'),
  ('307','JAQUELINE COSTA DA SILVA'),
  ('308','IVAN BARBOSA DE ALMEIDA'),
  ('309','HIGOR QUADROS DA SILVA'),
  ('310','ROSILAINE DE MARCHI'),
  ('314','JUCELIA SOMBRA DOS SANTOS'),
  ('315','CARINA BARBOSA RODRIGUES'),
  ('316','LAVINEA SOARES MACHADO'),
  ('317','FRANCISCO CESAR FERREIRA DA COSTA'),
  ('318','MARCOS VINICIUS ALMEIDA LOPES'),
  ('319','CELSO DA SILVA NASCIMENTO'),
  ('321','THAIANE SILVA MONTEIRO'),
  ('322','WHEILLA DE SOUZA SOARES'),
  ('368','EDENILSON DE JESUS ARAGAO'),
  ('369','DAYSE CRISTIANE CARVALHO SANTOS PINHEIRO'),
  ('370','LUIZ FERNANDO CUSTODIO MARTINS'),
  ('372','KELVIS DO AMARAL PACIFICO'),
  ('374','JOSIMAR ALEXANDRE MORAES DOS SANTOS FREIAS'),
  ('375','ALVARO FELIPE NUNES'),
  ('376','CARLOS JOSE ORIOLI'),
  ('388','ANDRE GUSTAVO CABRAL DE MATOS'),
  ('393','DANILO DA SILVA RODRIGUES'),
  ('407','IGOR TOFANELLI'),
  ('409','LUCAS NEVES'),
  ('411','BRUNA VILELA'),
  ('413','RAFAEL ALMEIDA BRASIL');

update public.catalog_responsaveis r
   set responsavel_rotulo = p.nome
  from _prom p
 where r.responsavel_tipo = 'promotor'
   and r.responsavel_codigo = p.codigo
   and r.responsavel_rotulo <> p.nome;

insert into public.catalog_responsaveis
  (responsavel_codigo, responsavel_tipo, responsavel_rotulo, vigencia_inicio)
select p.codigo, 'promotor', p.nome, date '2026-10-01'
  from _prom p
 where not exists (
   select 1 from public.catalog_responsaveis r
    where r.responsavel_tipo = 'promotor' and r.responsavel_codigo = p.codigo
 );

commit;
