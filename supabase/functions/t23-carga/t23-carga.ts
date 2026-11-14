// T2.3 — ponte ENCERRADA (31/10/26). A carga foi concluída e verificada (888.576 combinações,
// 33 meses × 3 grandezas = 0,00 vs referência independente). Esta versão recusa TODA requisição.
// A função pode ser apagada no Dashboard (Edge Functions → t23-carga → Delete).
Deno.serve(
  () =>
    new Response(JSON.stringify({ erro: 'ponte encerrada após a T2.3' }), {
      status: 410,
      headers: { 'Content-Type': 'application/json' },
    }),
)
